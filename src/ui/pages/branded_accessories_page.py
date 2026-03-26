from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QComboBox,
)
from PySide6.QtCore import Qt
from src.services.inventory_service import InventoryService
from src.ui.components.product_table import ProductTable
from src.ui.components.dynamic_form import DynamicFormDialog
from src.ui.components.transaction_dialog import TransactionDialog
from src.ui.components.return_dialog import ReturnDialog
from src.ui.components.claim_dialog import ClaimDialog
from src.ui.components.claim_resolve_dialog import ClaimResolveDialog
from src.ui.components.loading_overlay import LoadingOverlay, run_async
from src.ui.theme import COLORS


class BrandedAccessoriesPage(QWidget):
    def __init__(self, brand_name: str, parent=None):
        super().__init__(parent)

        self.brand_name = brand_name
        self.inventory_service = InventoryService()
        self.category = self.inventory_service.get_category_by_name("Branded Accessories")
        self.category_id = self.category.id if self.category else ""

        self.subcategory = None
        if self.category_id:
            subcategories = self.inventory_service.get_subcategories(self.category_id)
            self.subcategory = next(
                (s for s in subcategories if s.name == brand_name), None
            )
        self.subcategory_id = self.subcategory.id if self.subcategory else ""

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(f"{self.brand_name} Accessories")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};"
        )
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Product Types")
        if self.subcategory_id:
            product_types = self.inventory_service.get_product_types(self.subcategory_id)
            for pt in product_types:
                self.filter_combo.addItem(pt.name, pt.id)
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        add_btn = QPushButton("Add New")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._on_add)
        filter_row.addWidget(add_btn)

        layout.addLayout(filter_row)

        self.table = ProductTable(
            columns=["Model", "Qty", "Purchase Price",
                     "Sale Price", "Status", "Actions"]
        )
        self.table.view_requested.connect(self._on_view)
        self.table.edit_requested.connect(self._on_edit)
        self.table.delete_requested.connect(self._on_delete)
        self.table.buy_requested.connect(self._on_buy)
        self.table.sell_requested.connect(self._on_sell)
        self.table.return_requested.connect(self._on_return)
        self.table.claim_requested.connect(self._on_claim)
        self.table.resolve_claim_requested.connect(self._on_resolve_claim)
        layout.addWidget(self.table)

        self._loading = LoadingOverlay(self)

    def refresh_data(self):
        selected_text = self.filter_combo.currentText()
        pt_id = self.filter_combo.currentData()

        def fetch():
            if selected_text == "All Product Types":
                return self.inventory_service.get_products_by_subcategory(
                    self.subcategory_id
                )
            if pt_id:
                return self.inventory_service.get_products_by_type(pt_id)
            return []

        run_async(self, fetch, lambda products: self.table.load_products(products),
                  message=f"Loading {self.brand_name}...")

    def _on_add(self):
        try:
            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                subcategory_id=self.subcategory_id,
                brand_name=self.brand_name,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open form:\n{e}")

    def _on_edit(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                product=product,
                subcategory_id=self.subcategory_id,
                brand_name=self.brand_name,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit product:\n{e}")

    def _on_delete(self, product_id: str):
        try:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this product?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.inventory_service.delete_product(product_id)
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete product:\n{e}")

    def _on_buy(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = TransactionDialog(product, "purchase", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record purchase:\n{e}")

    def _on_sell(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = TransactionDialog(product, "sale", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record sale:\n{e}")

    def _on_return(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            dialog = ReturnDialog(product, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record return:\n{e}")

    def _on_claim(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            dialog = ClaimDialog(product, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit claim:\n{e}")

    def _on_resolve_claim(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            dialog = ClaimResolveDialog(product, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to resolve claim:\n{e}")

    def _on_view(self, product_id: str):
        try:
            product = self.inventory_service.get_product_by_id(product_id)
            if not product: return
            from src.ui.components.product_info_dialog import ProductInfoDialog
            dialog = ProductInfoDialog(product, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product info:\n{e}")
