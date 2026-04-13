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
        # Flat pt_id -> (subcategory, category) resolver, built lazily on demand
        self._pt_resolver: dict[str, tuple[Subcategory, Category]] | None = None
        # Product name map cache with TTL
        self._product_name_map: dict[str, str] | None = None
        self._product_name_map_time: float = 0

    # ── Cache Management ─────────────────────────────────────

    def invalidate_caches(self):
        self._categories = None
        self._subcategories = None
        self._product_types = None
        self._pt_resolver = None
        self._product_name_map = None

    def get_product_type_resolver(self) -> dict:
        """Return a dict: product_type_id -> (Subcategory, Category).

        Built once from the cached hierarchy and reused across the app so
        handlers like SearchPage._on_edit don't rebuild 3 maps on every click."""
        if self._pt_resolver is None:
            self._ensure_hierarchy()
            sub_by_id = {s.id: s for s in self._subcategories}
            cat_by_id = {c.id: c for c in self._categories}
            resolver: dict[str, tuple[Subcategory, Category]] = {}
            for pt in self._product_types:
                sub = sub_by_id.get(pt.subcategory_id)
                if sub is None:
                    continue
                cat = cat_by_id.get(sub.category_id)
                if cat is None:
                    continue
                resolver[pt.id] = (sub, cat)
            self._pt_resolver = resolver
        return self._pt_resolver

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

    def delete_subcategory(self, subcategory_id: str) -> int:
        """Delete a subcategory along with its product types, attribute
        definitions, and all products (+ cascading phone_details / transactions).
        Returns the number of products deleted."""
        # Collect product types under this subcategory
        pt_ids = [
            pt.id for pt in self.get_product_types(subcategory_id)
        ]
        product_count = 0
        if pt_ids:
            # Count products first
            prod_resp = (
                self.client.table("products")
                .select("id", count="exact")
                .in_("product_type_id", pt_ids)
                .execute()
            )
            product_count = prod_resp.count or 0
            # Products cascade delete phone_details and transactions (FK ON DELETE CASCADE)
            self.client.table("products").delete().in_("product_type_id", pt_ids).execute()
            # Delete attribute definitions for these product types
            self.client.table("attribute_definitions").delete().in_("product_type_id", pt_ids).execute()
            # Delete product types
            self.client.table("product_types").delete().in_("id", pt_ids).execute()
        # Delete the subcategory itself
        self.client.table("subcategories").delete().eq("id", subcategory_id).execute()
        self.invalidate_caches()
        self._product_name_map = None
        return product_count

    def count_products_in_subcategory(self, subcategory_id: str) -> int:
        """Return how many products exist in a subcategory (used for confirmation)."""
        pt_ids = [pt.id for pt in self.get_product_types(subcategory_id)]
        if not pt_ids:
            return 0
        resp = (
            self.client.table("products")
            .select("id", count="exact")
            .in_("product_type_id", pt_ids)
            .execute()
        )
        return resp.count or 0

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

    def delete_product_type(self, product_type_id: str) -> int:
        """Delete a product type + its attribute definitions + all products under it.
        Returns the number of products deleted."""
        # Count products first
        prod_resp = (
            self.client.table("products")
            .select("id", count="exact")
            .eq("product_type_id", product_type_id)
            .execute()
        )
        product_count = prod_resp.count or 0
        # Products cascade-delete phone_details + transactions
        if product_count > 0:
            self.client.table("products").delete().eq("product_type_id", product_type_id).execute()
        # Delete attribute definitions
        self.client.table("attribute_definitions").delete().eq("product_type_id", product_type_id).execute()
        # Delete the product type itself
        self.client.table("product_types").delete().eq("id", product_type_id).execute()
        self.invalidate_caches()
        self._product_name_map = None
        return product_count

    def count_products_in_product_type(self, product_type_id: str) -> int:
        resp = (
            self.client.table("products")
            .select("id", count="exact")
            .eq("product_type_id", product_type_id)
            .execute()
        )
        return resp.count or 0

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
            "serial_number": details.serial_number,
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
            "serial_number": details.serial_number,
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

    def get_all_transactions(
        self,
        trans_type: str | None = None,
        limit: int | None = 500,
    ) -> list[Transaction]:
        """Fetch transactions. Defaults to the 500 most recent to keep the
        transactions page fast. Pass ``limit=None`` for no limit.
        ``trans_type`` filters server-side (sale, purchase, return, claim, claim_resolved)."""
        query = self.client.table("transactions").select("*")
        if trans_type:
            query = query.eq("type", trans_type)
        query = query.order("created_at", desc=True)
        if limit is not None:
            query = query.limit(limit)
        resp = query.execute()
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

    def get_transaction_by_id(self, transaction_id: str) -> Transaction | None:
        resp = self.client.table("transactions").select("*").eq("id", transaction_id).execute()
        return Transaction(**resp.data[0]) if resp.data else None

    def get_latest_transaction_for_product(self, product_id: str) -> Transaction | None:
        resp = (
            self.client.table("transactions")
            .select("*")
            .eq("product_id", product_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return Transaction(**resp.data[0]) if resp.data else None

    def delete_transaction(self, transaction_id: str) -> None:
        self.client.table("transactions").delete().eq("id", transaction_id).execute()

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

    def search_products(
        self,
        query: str,
        category_id: str | None = None,
        subcategory_id: str | None = None,
    ) -> list[Product]:
        # Build the set of product_type_ids that this search is allowed to return
        allowed_pt_ids: set[str] | None = None
        if subcategory_id:
            self._ensure_hierarchy()
            allowed_pt_ids = {
                pt.id for pt in self._product_types
                if pt.subcategory_id == subcategory_id
            }
            if not allowed_pt_ids:
                return []
        elif category_id:
            self._ensure_hierarchy()
            sub_ids = {
                s.id for s in self._subcategories if s.category_id == category_id
            }
            allowed_pt_ids = {
                pt.id for pt in self._product_types if pt.subcategory_id in sub_ids
            }
            if not allowed_pt_ids:
                return []

        # Text search on products table
        text_query = (
            self.client.table("products")
            .select("*")
            .or_(f"name.ilike.%{query}%,brand.ilike.%{query}%,model.ilike.%{query}%,notes.ilike.%{query}%")
        )
        if allowed_pt_ids is not None:
            text_query = text_query.in_("product_type_id", list(allowed_pt_ids))
        resp = text_query.order("created_at", desc=True).execute()
        products = [Product(**row) for row in resp.data]
        found_ids = {p.id for p in products}

        # Also search by IMEI / serial in phone_details
        imei_resp = (
            self.client.table("phone_details")
            .select("product_id")
            .or_(
                f"imei1.ilike.%{query}%,imei2.ilike.%{query}%,serial_number.ilike.%{query}%"
            )
            .execute()
        )
        imei_product_ids = [
            row["product_id"] for row in imei_resp.data
            if row["product_id"] not in found_ids
        ]
        if imei_product_ids:
            extra_query = (
                self.client.table("products")
                .select("*")
                .in_("id", imei_product_ids)
            )
            if allowed_pt_ids is not None:
                extra_query = extra_query.in_("product_type_id", list(allowed_pt_ids))
            extra_resp = extra_query.execute()
            products.extend(Product(**row) for row in extra_resp.data)

        return products

    # ── Dashboard Stats ─────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """Fetch all dashboard stats (products + today's + monthly profit)."""
        from datetime import date

        # Products stats — also use purchase_price to build cost basis lookup
        resp = self.client.table("products").select(
            "id, purchase_price, sale_price, quantity, status"
        ).execute()
        rows = resp.data
        total_count = len(rows)
        total_value = sum((r["sale_price"] or 0) * (r["quantity"] or 0) for r in rows)
        low_stock = sum(
            1 for r in rows
            if 0 < (r["quantity"] or 0) <= 3 and r["status"] == "in_stock"
        )
        cost_map = {r["id"]: (r["purchase_price"] or 0) for r in rows}

        # Monthly transactions (covers today + the rest of the month in one query)
        today_obj = date.today()
        month_start = today_obj.replace(day=1).isoformat()
        today = today_obj.isoformat()
        month_txn_resp = (
            self.client.table("transactions")
            .select("type, total_price, quantity, product_id, created_at")
            .gte("created_at", month_start)
            .execute()
        )
        month_txns = month_txn_resp.data

        # Today's stats — filter from monthly result
        today_sales = [t for t in month_txns if t["type"] == "sale" and (t["created_at"] or "").startswith(today)]
        today_purchases = [t for t in month_txns if t["type"] == "purchase" and (t["created_at"] or "").startswith(today)]

        # Monthly profit = Revenue - COGS - Returns
        monthly_revenue = 0.0
        monthly_cogs = 0.0
        monthly_returns = 0.0
        for t in month_txns:
            if t["type"] == "sale":
                monthly_revenue += t["total_price"] or 0
                monthly_cogs += cost_map.get(t["product_id"], 0) * (t["quantity"] or 0)
            elif t["type"] == "return":
                monthly_returns += t["total_price"] or 0
        monthly_profit = monthly_revenue - monthly_cogs - monthly_returns

        return {
            "total_count": total_count,
            "total_value": total_value,
            "low_stock_count": low_stock,
            "today_sales_count": len(today_sales),
            "today_sales_amount": sum(t["total_price"] or 0 for t in today_sales),
            "today_purchases_count": len(today_purchases),
            "today_purchases_amount": sum(t["total_price"] or 0 for t in today_purchases),
            "monthly_revenue": monthly_revenue,
            "monthly_cogs": monthly_cogs,
            "monthly_returns": monthly_returns,
            "monthly_profit": monthly_profit,
            "month_label": today_obj.strftime("%B %Y"),
        }

    def get_profit_for_month(self, year: int, month: int) -> dict:
        """Compute profit stats for a specific calendar month."""
        from datetime import date
        month_start = date(year, month, 1).isoformat()
        # Next month start
        if month == 12:
            next_start = date(year + 1, 1, 1).isoformat()
        else:
            next_start = date(year, month + 1, 1).isoformat()

        # Products cost map (current cost basis)
        prod_resp = self.client.table("products").select("id, purchase_price").execute()
        cost_map = {r["id"]: (r["purchase_price"] or 0) for r in prod_resp.data}

        # Transactions in that month
        txn_resp = (
            self.client.table("transactions")
            .select("type, total_price, quantity, product_id")
            .gte("created_at", month_start)
            .lt("created_at", next_start)
            .execute()
        )

        revenue = 0.0
        cogs = 0.0
        returns = 0.0
        for t in txn_resp.data:
            if t["type"] == "sale":
                revenue += t["total_price"] or 0
                cogs += cost_map.get(t["product_id"], 0) * (t["quantity"] or 0)
            elif t["type"] == "return":
                returns += t["total_price"] or 0

        return {
            "revenue": revenue,
            "cogs": cogs,
            "returns": returns,
            "profit": revenue - cogs - returns,
            "month_label": date(year, month, 1).strftime("%B %Y"),
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
