from src.database.repository import Repository
from src.models.product import Product


class SearchService:
    def __init__(self):
        self.repo = Repository()

    def search(self, query: str) -> list[Product]:
        if not query or not query.strip():
            return []
        return self.repo.search_products(query.strip())
