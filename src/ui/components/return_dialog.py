from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QComboBox, QLineEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox,
)
from src.models.product import Product
from src.services.transaction_service import TransactionService
from src.services.inventory_service import InventoryService
from src.utils.helpers import format_price
from src.ui.components.loading_overlay import LoadingOverlay, WorkerThread
from src.ui.theme import COLORS


class ReturnDialog(QDialog):
    """Dialog for recording a product return."""

    def __init__(self, product: Product, parent=None):
        super().__init__(parent)
        self.product = product
        self.transaction_service = TransactionService()
        self.inventory_service = InventoryService()
        self.phone_details = self.inventory_service.get_phone_details(product.id)

        self.setWindowTitle(f"Record Return - {product.brand} {product.model}")
        self.setMinimumWidth(420)

        # Pre-fetch last sale info
        self._last_sale = self.transaction_service.get_last_sale_for_product(product.id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Product info
        info_group = QGroupBox("Product")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Brand:", QLabel(self.product.brand or "\u2014"))
        info_layout.addRow("Model:", QLabel(self.product.model or "\u2014"))
        if self._last_sale:
            sold_at = QLabel(format_price(self._last_sale.unit_price))
            sold_at.setStyleSheet(f"font-weight: 600; color: {COLORS['peach']};")
            info_layout.addRow("Sold At:", sold_at)
            if self._last_sale.customer_info:
                info_layout.addRow("Sold To:", QLabel(self._last_sale.customer_info))
        layout.addWidget(info_group)

        # Return details
        return_group = QGroupBox("Return Details")
        return_layout = QFormLayout(return_group)

        self.refund_input = QDoubleSpinBox()
        self.refund_input.setMaximum(9999999)
        self.refund_input.setDecimals(2)
        self.refund_input.setSingleStep(50)
        self.refund_input.setPrefix("Rs. ")
        self.refund_input.setFixedHeight(38)
        if self._last_sale:
            self.refund_input.setValue(self._last_sale.unit_price)

        self.reason_combo = QComboBox()
        self.reason_combo.addItems(["Defective", "Changed Mind", "Wrong Item", "Other"])

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Customer name")
        if self._last_sale and self._last_sale.customer_info:
            self.customer_input.setText(self._last_sale.customer_info)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Optional notes...")

        return_layout.addRow("Refund Amount:", self.refund_input)
        return_layout.addRow("Reason:", self.reason_combo)
        return_layout.addRow("Customer:", self.customer_input)
        return_layout.addRow("Notes:", self.notes_input)
        layout.addWidget(return_group)

        self.restock_group = QGroupBox("Restock Options")
        restock_layout = QFormLayout(self.restock_group)
        
        self.phone_type_combo = QComboBox()
        if self.phone_details:
            self.phone_type_combo.addItem(f"Same as before ({self.phone_details.phone_type})", "")
            self.phone_type_combo.addItem("Used", "used")
            self.phone_type_combo.addItem("Box Pack", "box_pack")
        else:
            self.phone_type_combo.addItem("New in stock", "new")
            self.phone_type_combo.addItem("Used/Opened", "used")
            
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["", "excellent", "good", "fair", "poor"])
        
        def update_condition_state():
            if self.phone_details:
                pt = self.phone_type_combo.currentData() or self.phone_details.phone_type
                self.condition_combo.setEnabled(pt == "used")
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                elif self.phone_details.condition and not self.phone_type_combo.currentData():
                    idx = self.condition_combo.findText(self.phone_details.condition)
                    if idx >= 0: self.condition_combo.setCurrentIndex(idx)
            else:
                pt = self.phone_type_combo.currentData()
                self.condition_combo.setEnabled(pt == "used")
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                
        self.phone_type_combo.currentIndexChanged.connect(update_condition_state)
        
        if self.phone_details:
            restock_layout.addRow("Restock Type:", self.phone_type_combo)
        else:
            restock_layout.addRow("Restock As:", self.phone_type_combo)
            
        restock_layout.addRow("Condition:", self.condition_combo)
        layout.addWidget(self.restock_group)
        update_condition_state()

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        self.save_btn = btn_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_btn.setText("Record Return")
        self.save_btn.setStyleSheet(
            f"background-color: {COLORS['yellow']}; color: #11111b; border: none; "
            "border-radius: 6px; font-weight: bold; padding: 8px 16px;"
        )
        layout.addWidget(btn_box)

        self._loading = LoadingOverlay(self)

    def _on_save(self):
        refund = self.refund_input.value()
        reason = self.reason_combo.currentText()
        customer = self.customer_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        return_reason = f"Return: {reason}" + (f" - {notes}" if notes else "")
        product_id = self.product.id

        original_text = self.save_btn.text()
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")
        self._loading.show_overlay("Recording return...")

        def do_save():
            new_type = None
            new_cond = None
            if getattr(self, "restock_group", None):
                if self.phone_type_combo.currentData():
                    new_type = self.phone_type_combo.currentData()
                if self.condition_combo.isEnabled():
                    new_cond = self.condition_combo.currentText()
            
            self.transaction_service.record_return(
                product_id=product_id,
                refund_amount=refund,
                customer_info=customer,
                return_reason=return_reason,
                new_phone_type=new_type,
                new_condition=new_cond,
            )
            return True

        def on_success(_):
            self._loading.hide_overlay()
            self.accept()

        def on_error(error_msg):
            self._loading.hide_overlay()
            self.save_btn.setEnabled(True)
            self.save_btn.setText(original_text)
            QMessageBox.critical(self, "Error", f"Return failed:\n{error_msg}")

        self._save_worker = WorkerThread(do_save)
        self._save_worker.finished.connect(on_success)
        self._save_worker.error.connect(on_error)
        self._save_worker.start()
