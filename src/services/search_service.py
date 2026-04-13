from src.database.repository import Repository
from src.models.product import Product
from src.services.inventory_service import InventoryService


class SearchService:
    def __init__(self):
        # Share the singleton repo so cache invalidation works app-wide
        self.repo = InventoryService().repo

    def search(
        self,
        query: str,
        category_id: str | None = None,
        subcategory_id: str | None = None,
    ) -> list[Product]:
        if not query or not query.strip():
            return []
        return self.repo.search_products(
            query.strip(),
            category_id=category_id,
            subcategory_id=subcategory_id,
        )
