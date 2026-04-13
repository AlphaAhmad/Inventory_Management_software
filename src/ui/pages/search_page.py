from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMessageBox,
)
from PySide6.QtCore import Qt
from src.services.search_service import SearchService
from src.services.inventory_service import InventoryService
from src.ui.components.product_table import ProductTable
from src.ui.components.dynamic_form import DynamicFormDialog
from src.ui.components.transaction_dialog import TransactionDialog
from src.ui.components.return_dialog import ReturnDialog
from src.ui.components.claim_dialog import ClaimDialog
from src.ui.components.claim_resolve_dialog import ClaimResolveDialog
from src.ui.theme import COLORS


class SearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_service = SearchService()
        self.inventory_service = InventoryService()
        self._last_query = ""
        self._last_category_id: str | None = None
        self._last_subcategory_id: str | None = None
        self._last_scope_label: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title_label = QLabel("Search Results")
        self.title_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(self.title_label)

        self.info_label = QLabel("Enter a search term in the search bar above.")
        self.info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        layout.addWidget(self.info_label)

        self.table = ProductTable()
        self.table.view_requested.connect(self._on_view)
        self.table.edit_requested.connect(self._on_edit)
        self.table.delete_requested.connect(self._on_delete)
        self.table.buy_requested.connect(self._on_buy)
        self.table.sell_requested.connect(self._on_sell)
        self.table.return_requested.connect(self._on_return)
        self.table.claim_requested.connect(self._on_claim)
        self.table.resolve_claim_requested.connect(self._on_resolve_claim)
        layout.addWidget(self.table, 1)

    def do_search(
        self,
        query: str,
        category_id: str | None = None,
        subcategory_id: str | None = None,
        scope_label: str = "",
    ):
        self._last_query = query
        self._last_category_id = category_id
        self._last_subcategory_id = subcategory_id
        self._last_scope_label = scope_label

        if scope_label:
            self.title_label.setText(f'Search Results for "{query}" in {scope_label}')
        else:
            self.title_label.setText(f'Search Results for "{query}"')
        try:
            products = self.search_service.search(
                query, category_id=category_id, subcategory_id=subcategory_id
            )
            scope_suffix = f" in {scope_label}" if scope_label else ""
            self.info_label.setText(f"Found {len(products)} result(s){scope_suffix}")
            self.table.load_products(products)
        except Exception as e:
            self.info_label.setText("Search failed")
            QMessageBox.critical(self, "Error", f"Search failed:\n{e}")

    def refresh_data(self):
        if self._last_query:
            self.do_search(
                self._last_query,
                category_id=self._last_category_id,
                subcategory_id=self._last_subcategory_id,
                scope_label=self._last_scope_label,
            )

    def _on_edit(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return

            # O(1) lookup of (Subcategory, Category) for this product's type.
            # Built once and cached, shared across the whole app.
            resolver = self.inventory_service.repo.get_product_type_resolver()
            resolved = resolver.get(product.product_type_id)
            if not resolved:
                return
            sub, cat = resolved

            phone_details = None
            if cat.name == "Phones":
                phone_details = self.inventory_service.get_phone_details(product_id)

            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=sub.category_id,
                product=product,
                phone_details=phone_details,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit:\n{e}")

    def _on_delete(self, product_id: str):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.inventory_service.delete_product(product_id)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed:\n{e}")

    def _on_buy(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            dialog = TransactionDialog(product, "purchase", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def _on_sell(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            dialog = TransactionDialog(product, "sale", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def _on_view(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product: return
            phone_details = self.inventory_service.get_phone_details(product_id)
            from src.ui.components.product_info_dialog import ProductInfoDialog
            dialog = ProductInfoDialog(product, phone_details, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product info:\n{e}")

    def _on_return(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            dialog = ReturnDialog(product, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record return:\n{e}")

    def _on_claim(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            phone_details = self.inventory_service.get_phone_details(product_id)
            dialog = ClaimDialog(product, phone_details, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit claim:\n{e}")

    def _on_resolve_claim(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            phone_details = self.inventory_service.get_phone_details(product_id)
            dialog = ClaimResolveDialog(product, phone_details, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to resolve claim:\n{e}")
