import time
from src.database.supabase_client import get_client
from src.models.category import Category, Subcategory, ProductType
from src.models.attribute import AttributeDefinition
from src.models.product import Product, PhoneDetails
from src.models.transaction import Transaction


class Repository:
    def __init__(self):
        self.client = get_client()
        # In-memory hierarchy caches (loaded once, invalidated on brand add/remove)
        self._categories: list[Category] | None = None
        self._subcategories: list[Subcategory] | None = None
        self._product_types: list[ProductType] | None = None
        # Product name map cache with TTL
        self._product_name_map: dict[str, str] | None = None
        self._product_name_map_time: float = 0

    # ── Cache Management ─────────────────────────────────────

    def invalidate_caches(self):
        self._categories = None
        self._subcategories = None
        self._product_types = None
        self._product_name_map = None

    def _ensure_hierarchy(self):
        if self._categories is None:
            resp = self.client.table("categories").select("*").order("display_order").execute()
            self._categories = [Category(**row) for row in resp.data]
        if self._subcategories is None:
            resp = self.client.table("subcategories").select("*").order("display_order").execute()
            self._subcategories = [Subcategory(**row) for row in resp.data]
        if self._product_types is None:
            resp = self.client.table("product_types").select("*").order("display_order").execute()
            self._product_types = [ProductType(**row) for row in resp.data]

    # ── Categories ──────────────────────────────────────────

    def get_categories(self) -> list[Category]:
        self._ensure_hierarchy()
        return self._categories

    def get_category_by_name(self, name: str) -> Category | None:
        self._ensure_hierarchy()
        return next((c for c in self._categories if c.name == name), None)

    # ── Subcategories ───────────────────────────────────────

    def get_subcategories(self, category_id: str) -> list[Subcategory]:
        self._ensure_hierarchy()
        return [s for s in self._subcategories if s.category_id == category_id]

    def get_all_subcategories(self) -> list[Subcategory]:
        self._ensure_hierarchy()
        return self._subcategories

    def get_subcategory_by_name(self, category_id: str, name: str) -> Subcategory | None:
        self._ensure_hierarchy()
        return next(
            (s for s in self._subcategories if s.category_id == category_id and s.name == name),
            None,
        )


    def create_subcategory(self, subcategory: Subcategory) -> Subcategory:
        data = {"category_id": subcategory.category_id, "name": subcategory.name, "display_order": subcategory.display_order}
        resp = self.client.table("subcategories").insert(data).execute()
        created = Subcategory(**resp.data[0])
        if self._subcategories is not None:
            self._subcategories.append(created)
        return created

    # ── Product Types ───────────────────────────────────────

    def get_product_types(self, subcategory_id: str) -> list[ProductType]:
        self._ensure_hierarchy()
        return [pt for pt in self._product_types if pt.subcategory_id == subcategory_id]

    def get_all_product_types(self) -> list[ProductType]:
        self._ensure_hierarchy()
        return self._product_types

    def get_product_type_by_name(self, subcategory_id: str, name: str) -> ProductType | None:
        self._ensure_hierarchy()
        return next(
            (pt for pt in self._product_types if pt.subcategory_id == subcategory_id and pt.name == name),
            None,
        )


    def create_product_type(self, product_type: ProductType) -> ProductType:
        data = {"subcategory_id": product_type.subcategory_id, "name": product_type.name, "display_order": product_type.display_order}
        resp = self.client.table("product_types").insert(data).execute()
        created = ProductType(**resp.data[0])
        if self._product_types is not None:
            self._product_types.append(created)
        return created

    # ── Attribute Definitions ───────────────────────────────

    def get_attribute_definitions(self, product_type_id: str) -> list[AttributeDefinition]:
        resp = (
            self.client.table("attribute_definitions")
            .select("*")
            .eq("product_type_id", product_type_id)
            .order("display_order")
            .execute()
        )
        return [AttributeDefinition(**row) for row in resp.data]


    def create_attribute_definition(self, attr: AttributeDefinition) -> AttributeDefinition:
        data = {
            "product_type_id": attr.product_type_id,
            "name": attr.name,
            "label": attr.label,
            "field_type": attr.field_type,
            "options": attr.options,
            "is_required": attr.is_required,
            "display_order": attr.display_order
        }
        resp = self.client.table("attribute_definitions").insert(data).execute()
        return AttributeDefinition(**resp.data[0])

    # ── Products ────────────────────────────────────────────

    def get_products(self, product_type_id: str | None = None, status: str | None = None) -> list[Product]:
        query = self.client.table("products").select("*")
        if product_type_id:
            query = query.eq("product_type_id", product_type_id)
        if status:
            query = query.eq("status", status)
        resp = query.order("created_at", desc=True).execute()
        return [Product(**row) for row in resp.data]

    def get_products_by_subcategory(self, subcategory_id: str) -> list[Product]:
        self._ensure_hierarchy()
        pt_ids = [pt.id for pt in self._product_types if pt.subcategory_id == subcategory_id]
        if not pt_ids:
            return []
        resp = (
            self.client.table("products")
            .select("*")
            .in_("product_type_id", pt_ids)
            .order("created_at", desc=True)
            .execute()
        )
        return [Product(**row) for row in resp.data]

    def get_products_by_category(self, category_id: str) -> list[Product]:
        self._ensure_hierarchy()
        sub_ids = {s.id for s in self._subcategories if s.category_id == category_id}
        pt_ids = [pt.id for pt in self._product_types if pt.subcategory_id in sub_ids]
        if not pt_ids:
            return []
        resp = (
            self.client.table("products")
            .select("*")
            .in_("product_type_id", pt_ids)
            .order("created_at", desc=True)
            .execute()
        )
        return [Product(**row) for row in resp.data]

    def get_product_by_id(self, product_id: str) -> Product | None:
        resp = self.client.table("products").select("*").eq("id", product_id).execute()
        return Product(**resp.data[0]) if resp.data else None

    def get_product_name_map(self) -> dict[str, str]:
        """Batch fetch all product id->name mappings. Cached for 30s."""
        now = time.time()
        if self._product_name_map is not None and (now - self._product_name_map_time) < 30:
            return self._product_name_map
        resp = self.client.table("products").select("id, name").execute()
        self._product_name_map = {row["id"]: row["name"] for row in resp.data}
        self._product_name_map_time = now
        return self._product_name_map

    def create_product(self, product: Product) -> Product:
        data = {
            "product_type_id": product.product_type_id,
            "name": product.name,
            "brand": product.brand,
            "model": product.model,
            "purchase_price": product.purchase_price,
            "sale_price": product.sale_price,
            "quantity": product.quantity,
            "status": product.status,
            "attributes": product.attributes,
            "notes": product.notes,
        }
        resp = self.client.table("products").insert(data).execute()
        self._product_name_map = None
        return Product(**resp.data[0])

    def update_product(self, product: Product) -> Product:
        data = {
            "name": product.name,
            "brand": product.brand,
            "model": product.model,
            "purchase_price": product.purchase_price,
            "sale_price": product.sale_price,
            "quantity": product.quantity,
            "status": product.status,
            "attributes": product.attributes,
            "notes": product.notes,
        }
        resp = self.client.table("products").update(data).eq("id", product.id).execute()
        self._product_name_map = None
        return Product(**resp.data[0])

    def delete_product(self, product_id: str) -> None:
        self.client.table("products").delete().eq("id", product_id).execute()
        self._product_name_map = None

    def get_all_products(self) -> list[Product]:
        resp = self.client.table("products").select("*").order("created_at", desc=True).execute()
        return [Product(**row) for row in resp.data]

    # ── Phone Details ───────────────────────────────────────

    def get_phone_details(self, product_id: str) -> PhoneDetails | None:
        resp = (
            self.client.table("phone_details")
            .select("*")
            .eq("product_id", product_id)
            .execute()
        )
        return PhoneDetails(**resp.data[0]) if resp.data else None

    def create_phone_details(self, details: PhoneDetails) -> PhoneDetails:
        data = {
            "product_id": details.product_id,
            "imei1": details.imei1,
            "imei2": details.imei2,
            "phone_type": details.phone_type,
            "has_box": details.has_box,
            "has_charger": details.has_charger,
            "keypad_type": details.keypad_type,
            "is_claimed": details.is_claimed,
            "claim_reason": details.claim_reason,
            "condition": details.condition,
            "storage_gb": details.storage_gb,
            "ram_gb": details.ram_gb,
            "color": details.color,
            "region_variant": details.region_variant,
        }
        resp = self.client.table("phone_details").insert(data).execute()
        return PhoneDetails(**resp.data[0])

    def update_phone_details(self, details: PhoneDetails) -> PhoneDetails:
        data = {
            "imei1": details.imei1,
            "imei2": details.imei2,
            "phone_type": details.phone_type,
            "has_box": details.has_box,
            "has_charger": details.has_charger,
            "keypad_type": details.keypad_type,
            "is_claimed": details.is_claimed,
            "claim_reason": details.claim_reason,
            "condition": details.condition,
            "storage_gb": details.storage_gb,
            "ram_gb": details.ram_gb,
            "color": details.color,
            "region_variant": details.region_variant,
        }
        resp = (
            self.client.table("phone_details")
            .update(data)
            .eq("product_id", details.product_id)
            .execute()
        )
        return PhoneDetails(**resp.data[0])

    def get_phone_details_batch(self, product_ids: list[str]) -> dict[str, PhoneDetails]:
        """Batch fetch phone details for multiple products. Returns {product_id: PhoneDetails}."""
        if not product_ids:
            return {}
        resp = (
            self.client.table("phone_details")
            .select("*")
            .in_("product_id", product_ids)
            .execute()
        )
        return {row["product_id"]: PhoneDetails(**row) for row in resp.data}

    # ── Transactions ────────────────────────────────────────

    def get_transactions(
        self,
        product_id: str | None = None,
        trans_type: str | None = None,
    ) -> list[Transaction]:
        query = self.client.table("transactions").select("*")
        if product_id:
            query = query.eq("product_id", product_id)
        if trans_type:
            query = query.eq("type", trans_type)
        resp = query.order("created_at", desc=True).execute()
        return [Transaction(**row) for row in resp.data]

    def get_all_transactions(self) -> list[Transaction]:
        resp = (
            self.client.table("transactions")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return [Transaction(**row) for row in resp.data]

    def get_recent_transactions(self, limit: int = 10) -> list[Transaction]:
        resp = (
            self.client.table("transactions")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [Transaction(**row) for row in resp.data]

    def create_transaction(self, transaction: Transaction) -> Transaction:
        data = {
            "product_id": transaction.product_id,
            "type": transaction.type,
            "quantity": transaction.quantity,
            "unit_price": transaction.unit_price,
            "total_price": transaction.total_price,
            "original_price": transaction.original_price,
            "customer_info": transaction.customer_info,
            "notes": transaction.notes,
        }
        if transaction.related_transaction_id:
            data["related_transaction_id"] = transaction.related_transaction_id
        resp = self.client.table("transactions").insert(data).execute()
        return Transaction(**resp.data[0])

    def get_last_sale_for_product(self, product_id: str) -> Transaction | None:
        resp = (
            self.client.table("transactions")
            .select("*")
            .eq("product_id", product_id)
            .eq("type", "sale")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return Transaction(**resp.data[0]) if resp.data else None

    def get_active_claim_for_product(self, product_id: str) -> Transaction | None:
        resp = (
            self.client.table("transactions")
            .select("*")
            .eq("product_id", product_id)
            .eq("type", "claim")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return Transaction(**resp.data[0]) if resp.data else None

    # ── Search ──────────────────────────────────────────────

    def search_products(self, query: str) -> list[Product]:
        resp = (
            self.client.table("products")
            .select("*")
            .or_(f"name.ilike.%{query}%,brand.ilike.%{query}%,model.ilike.%{query}%,notes.ilike.%{query}%")
            .order("created_at", desc=True)
            .execute()
        )
        products = [Product(**row) for row in resp.data]
        found_ids = {p.id for p in products}

        # Also search by IMEI in phone_details
        imei_resp = (
            self.client.table("phone_details")
            .select("product_id")
            .or_(f"imei1.ilike.%{query}%,imei2.ilike.%{query}%")
            .execute()
        )
        imei_product_ids = [
            row["product_id"] for row in imei_resp.data
            if row["product_id"] not in found_ids
        ]
        if imei_product_ids:
            extra_resp = (
                self.client.table("products")
                .select("*")
                .in_("id", imei_product_ids)
                .execute()
            )
            products.extend(Product(**row) for row in extra_resp.data)

        return products

    # ── Dashboard Stats ─────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """Fetch all dashboard stats (products + today's transactions)."""
        from datetime import date, timezone

        # Products stats
        resp = self.client.table("products").select("id, sale_price, quantity, status").execute()
        rows = resp.data
        total_count = len(rows)
        total_value = sum(r["sale_price"] * r["quantity"] for r in rows)
        low_stock = sum(1 for r in rows if 0 < r["quantity"] <= 3 and r["status"] == "in_stock")

        # Today's transactions
        today = date.today().isoformat()
        txn_resp = (
            self.client.table("transactions")
            .select("type, total_price")
            .gte("created_at", today)
            .execute()
        )
        today_sales = [t for t in txn_resp.data if t["type"] == "sale"]
        today_purchases = [t for t in txn_resp.data if t["type"] == "purchase"]

        return {
            "total_count": total_count,
            "total_value": total_value,
            "low_stock_count": low_stock,
            "today_sales_count": len(today_sales),
            "today_sales_amount": sum(t["total_price"] for t in today_sales),
            "today_purchases_count": len(today_purchases),
            "today_purchases_amount": sum(t["total_price"] for t in today_purchases),
        }

    def get_total_product_count(self) -> int:
        resp = self.client.table("products").select("id", count="exact").execute()
        return resp.count or 0

    def get_total_stock_value(self) -> float:
        resp = self.client.table("products").select("sale_price, quantity").execute()
        return sum(row["sale_price"] * row["quantity"] for row in resp.data)

    def get_low_stock_products(self, threshold: int = 3) -> list[Product]:
        resp = (
            self.client.table("products")
            .select("*")
            .lte("quantity", threshold)
            .gt("quantity", 0)
            .eq("status", "in_stock")
            .order("quantity")
            .execute()
        )
        return [Product(**row) for row in resp.data]

    # ── Brand Management ────────────────────────────────────

    def add_brand(self, brand_name: str) -> Subcategory:
        """Add a new brand as a subcategory under 'Branded Accessories'."""
        cat = self.get_category_by_name("Branded Accessories")
        if not cat:
            raise ValueError("Category 'Branded Accessories' not found")
        existing = self.get_subcategory_by_name(cat.id, brand_name)
        if existing:
            return existing
        max_order = max((s.display_order for s in self.get_subcategories(cat.id)), default=0)
        data = {
            "category_id": cat.id,
            "name": brand_name,
            "display_order": max_order + 1,
        }
        resp = self.client.table("subcategories").insert(data).execute()
        self.invalidate_caches()
        return Subcategory(**resp.data[0])

    def remove_brand(self, brand_name: str) -> bool:
        """Remove a brand subcategory and its product types. Returns True if removed."""
        cat = self.get_category_by_name("Branded Accessories")
        if not cat:
            return False
        sub = self.get_subcategory_by_name(cat.id, brand_name)
        if not sub:
            return False
        # Delete attribute definitions for product types under this brand
        pt_ids = [pt.id for pt in self.get_product_types(sub.id)]
        if pt_ids:
            self.client.table("attribute_definitions").delete().in_("product_type_id", pt_ids).execute()
            self.client.table("product_types").delete().eq("subcategory_id", sub.id).execute()
        self.client.table("subcategories").delete().eq("id", sub.id).execute()
        self.invalidate_caches()
        return True

    def get_brand_names(self) -> list[str]:
        """Get all brand names under 'Branded Accessories'."""
        cat = self.get_category_by_name("Branded Accessories")
        if not cat:
            return []
        return [s.name for s in self.get_subcategories(cat.id)]
