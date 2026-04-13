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


class GlassProtectorsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.inventory_service = InventoryService()
        self.category = self.inventory_service.get_category_by_name("Glass Protectors")
        self.category_id = self.category.id if self.category else ""

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Glass Protectors")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};"
        )
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Subcategories")
        self.filter_combo.addItems(["iPhone Glass", "Android Glass"])
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        add_type_btn = QPushButton("+ Add Glass Type")
        add_type_btn.setObjectName("secondaryBtn")
        add_type_btn.clicked.connect(self._on_add_product_type)
        filter_row.addWidget(add_type_btn)

        remove_type_btn = QPushButton("- Remove Glass Type")
        remove_type_btn.setObjectName("dangerBtn")
        remove_type_btn.clicked.connect(self._on_remove_product_type)
        filter_row.addWidget(remove_type_btn)

        add_btn = QPushButton("Add New Product")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._on_add)
        filter_row.addWidget(add_btn)

        layout.addLayout(filter_row)

        self.table = ProductTable(
            columns=["Brand", "Model", "Qty", "Purchase Price",
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

    def _on_add_product_type(self):
        from PySide6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
        from src.models.category import ProductType
        from src.models.attribute import AttributeDefinition

        # Pick which subcategory to add under
        subs = self.inventory_service.get_subcategories(self.category_id)
        sub_names = [s.name for s in subs]
        if not sub_names:
            QMessageBox.warning(self, "Error", "No subcategories found.")
            return

        sub_name, ok = QInputDialog.getItem(
            self, "Add Glass Type",
            "Add under which subcategory?",
            sub_names, 0, False,
        )
        if not ok:
            return
        sub = next((s for s in subs if s.name == sub_name), None)
        if not sub:
            return

        name, ok = QInputDialog.getText(
            self, "Add Glass Type",
            f"Enter new glass type name under '{sub_name}'\n(e.g. OG Glass, Youksh Privacy, Blue Shark):",
        )
        if not (ok and name.strip()):
            return
        name = name.strip()

        try:
            # Check duplicate
            existing_pts = self.inventory_service.get_product_types(sub.id)
            if any(pt.name.lower() == name.lower() for pt in existing_pts):
                QMessageBox.information(self, "Exists", f"Glass type '{name}' already exists.")
                return

            pt = ProductType(subcategory_id=sub.id, name=name)
            created_pt = self.inventory_service.create_product_type(pt)

            # Add standard glass protector attributes
            attrs = [
                AttributeDefinition(
                    product_type_id=created_pt.id, name="compatible_model",
                    label="Compatible Model", field_type="text",
                    is_required=True, display_order=1,
                ),
            ]
            for attr in attrs:
                self.inventory_service.create_attribute_definition(attr)

            QMessageBox.information(self, "Success", f"Glass type '{name}' added under {sub_name}!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add glass type:\n{e}")

    def _on_remove_product_type(self):
        from PySide6.QtWidgets import QInputDialog

        # First pick subcategory
        subs = self.inventory_service.get_subcategories(self.category_id)
        sub_names = [s.name for s in subs]
        if not sub_names:
            QMessageBox.warning(self, "Error", "No subcategories found.")
            return

        sub_name, ok = QInputDialog.getItem(
            self, "Remove Glass Type",
            "From which subcategory?",
            sub_names, 0, False,
        )
        if not ok:
            return
        sub = next((s for s in subs if s.name == sub_name), None)
        if not sub:
            return

        # Then pick product type within that subcategory
        pts = self.inventory_service.get_product_types(sub.id)
        if not pts:
            QMessageBox.information(self, "Empty", f"No glass types found under '{sub_name}'.")
            return

        pt_names = [pt.name for pt in pts]
        pt_name, ok = QInputDialog.getItem(
            self, "Remove Glass Type",
            f"Select glass type to remove from '{sub_name}':",
            pt_names, 0, False,
        )
        if not ok:
            return
        pt = next((p for p in pts if p.name == pt_name), None)
        if not pt:
            return

        try:
            product_count = self.inventory_service.count_products_in_product_type(pt.id)
            warning = f"Are you sure you want to remove glass type '{pt_name}'?"
            if product_count > 0:
                warning += (
                    f"\n\nThis will permanently delete {product_count} product(s) "
                    f"and their transaction history. This cannot be undone."
                )
            reply = QMessageBox.question(
                self, "Confirm Remove", warning,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            deleted = self.inventory_service.delete_product_type(pt.id)
            self.refresh_data()
            QMessageBox.information(
                self, "Removed",
                f"Glass type '{pt_name}' removed. {deleted} product(s) deleted."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove glass type:\n{e}")

    def refresh_data(self):
        selected = self.filter_combo.currentText()

        def fetch():
            if selected == "All Subcategories":
                return self.inventory_service.get_products_by_category(self.category_id)
            subcategories = self.inventory_service.get_subcategories(self.category_id)
            sub = next((s for s in subcategories if s.name == selected), None)
            if sub:
                return self.inventory_service.get_products_by_subcategory(sub.id)
            return []

        run_async(self, fetch, lambda products: self.table.load_products(products),
                  message="Loading glass protectors...")

    def _on_add(self):
        try:
            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open form:\n{e}")

    def _on_edit(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                product=product,
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
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
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product: return
            from src.ui.components.product_info_dialog import ProductInfoDialog
            dialog = ProductInfoDialog(product, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product info:\n{e}")
