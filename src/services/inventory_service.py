from src.database.repository import Repository
from src.models.product import Product, PhoneDetails
from src.models.category import Category, Subcategory, ProductType
from src.models.attribute import AttributeDefinition
from src.models.transaction import Transaction


class InventoryService:
    _shared_repo: Repository | None = None

    def __init__(self):
        # Share a single Repository instance across all services/pages
        if InventoryService._shared_repo is None:
            InventoryService._shared_repo = Repository()
        self.repo = InventoryService._shared_repo

    # ── Category Hierarchy ──────────────────────────────────

    def get_categories(self) -> list[Category]:
        return self.repo.get_categories()

    def get_subcategories(self, category_id: str) -> list[Subcategory]:
        return self.repo.get_subcategories(category_id)

    def get_product_types(self, subcategory_id: str) -> list[ProductType]:
        return self.repo.get_product_types(subcategory_id)

    def get_attribute_definitions(self, product_type_id: str) -> list[AttributeDefinition]:
        return self.repo.get_attribute_definitions(product_type_id)


    def create_subcategory(self, subcategory) -> 'Subcategory':
        return self.repo.create_subcategory(subcategory)

    def delete_subcategory(self, subcategory_id: str) -> int:
        return self.repo.delete_subcategory(subcategory_id)

    def count_products_in_subcategory(self, subcategory_id: str) -> int:
        return self.repo.count_products_in_subcategory(subcategory_id)

    def create_product_type(self, product_type) -> 'ProductType':
        return self.repo.create_product_type(product_type)

    def delete_product_type(self, product_type_id: str) -> int:
        return self.repo.delete_product_type(product_type_id)

    def count_products_in_product_type(self, product_type_id: str) -> int:
        return self.repo.count_products_in_product_type(product_type_id)

    def create_attribute_definition(self, attr) -> 'AttributeDefinition':
        return self.repo.create_attribute_definition(attr)

    def get_category_by_name(self, name: str) -> Category | None:
        return self.repo.get_category_by_name(name)

    # ── Products ────────────────────────────────────────────

    def get_products_by_category(self, category_id: str) -> list[Product]:
        return self.repo.get_products_by_category(category_id)

    def get_products_by_subcategory(self, subcategory_id: str) -> list[Product]:
        return self.repo.get_products_by_subcategory(subcategory_id)

    def get_products_by_type(self, product_type_id: str) -> list[Product]:
        return self.repo.get_products(product_type_id=product_type_id)

    def get_product_by_id(self, product_id: str) -> Product | None:
        return self.repo.get_product_by_id(product_id)

    def get_all_products(self) -> list[Product]:
        return self.repo.get_all_products()

    def get_product_name_map(self) -> dict[str, str]:
        return self.repo.get_product_name_map()

    def create_product(self, product: Product) -> Product:
        created_product = self.repo.create_product(product)

        # Automatically create a purchase transaction for the new product
        # This tracks that the item was acquired/added today
        transaction = Transaction(
            product_id=created_product.id,
            type="purchase",
            quantity=created_product.quantity,
            unit_price=created_product.purchase_price,
            total_price=created_product.quantity * created_product.purchase_price,
        )
        self.repo.create_transaction(transaction)

        return created_product

    def update_product(self, product: Product) -> Product:
        return self.repo.update_product(product)

    def delete_product(self, product_id: str) -> None:
        # Get all transactions for this product
        transactions = self.repo.get_transactions(product_id=product_id, trans_type="purchase")

        # Delete the purchase transaction(s) that track this product being added
        for txn in transactions:
            self.repo.delete_transaction(txn.id)

        # Then delete the product itself (which will cascade delete remaining transactions)
        self.repo.delete_product(product_id)

    # ── Phone Details ───────────────────────────────────────

    def get_phone_details(self, product_id: str) -> PhoneDetails | None:
        return self.repo.get_phone_details(product_id)

    def create_phone_details(self, details: PhoneDetails) -> PhoneDetails:
        return self.repo.create_phone_details(details)

    def update_phone_details(self, details: PhoneDetails) -> PhoneDetails:
        return self.repo.update_phone_details(details)

    def get_phone_details_batch(self, product_ids: list[str]) -> dict[str, 'PhoneDetails']:
        return self.repo.get_phone_details_batch(product_ids)

    # ── Dashboard Stats ─────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        return self.repo.get_dashboard_stats()

    def get_profit_for_month(self, year: int, month: int) -> dict:
        return self.repo.get_profit_for_month(year, month)

    def get_total_product_count(self) -> int:
        return self.repo.get_total_product_count()

    def get_total_stock_value(self) -> float:
        return self.repo.get_total_stock_value()

    def get_low_stock_products(self, threshold: int = 3) -> list[Product]:
        return self.repo.get_low_stock_products(threshold)

    # ── Brand Management ────────────────────────────────────

    def get_brand_names(self) -> list[str]:
        return self.repo.get_brand_names()

    def add_brand(self, brand_name: str) -> Subcategory:
        return self.repo.add_brand(brand_name)

    def remove_brand(self, brand_name: str) -> bool:
        return self.repo.remove_brand(brand_name)

    # ── Cache Management ────────────────────────────────────

    def invalidate_caches(self):
        self.repo.invalidate_caches()
