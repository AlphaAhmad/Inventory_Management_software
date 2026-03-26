from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMessageBox,
)
from PySide6.QtCore import Qt
from src.services.search_service import SearchService
from src.services.inventory_service import InventoryService
from src.ui.components.product_table import ProductTable
from src.ui.components.dynamic_form import DynamicFormDialog
from src.ui.components.transaction_dialog import TransactionDialog
from src.ui.theme import COLORS


class SearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_service = SearchService()
        self.inventory_service = InventoryService()
        self._last_query = ""
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
        layout.addWidget(self.table, 1)

    def do_search(self, query: str):
        self._last_query = query
        self.title_label.setText(f'Search Results for "{query}"')
        try:
            products = self.search_service.search(query)
            self.info_label.setText(f"Found {len(products)} result(s)")
            self.table.load_products(products)
        except Exception as e:
            self.info_label.setText("Search failed")
            QMessageBox.critical(self, "Error", f"Search failed:\n{e}")

    def refresh_data(self):
        if self._last_query:
            self.do_search(self._last_query)

    def _on_edit(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            # We need to figure out the category_id for this product
            all_pt = self.inventory_service.repo.get_all_product_types()
            pt_map = {pt.id: pt for pt in all_pt}
            pt = pt_map.get(product.product_type_id)
            if not pt:
                return
            all_sub = self.inventory_service.repo.get_all_subcategories()
            sub_map = {s.id: s for s in all_sub}
            sub = sub_map.get(pt.subcategory_id)
            if not sub:
                return

            phone_details = None
            categories = self.inventory_service.get_categories()
            cat_map = {c.id: c for c in categories}
            cat = cat_map.get(sub.category_id)
            if cat and cat.name == "Phones":
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
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            dialog = TransactionDialog(product, "purchase", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def _on_sell(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                return
            dialog = TransactionDialog(product, "sale", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def _on_view(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product: return
            phone_details = self.inventory_service.get_phone_details(product_id)
            from src.ui.components.product_info_dialog import ProductInfoDialog
            dialog = ProductInfoDialog(product, phone_details, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product info:\n{e}")
