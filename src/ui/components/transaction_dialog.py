from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt
from src.models.product import Product
from src.services.transaction_service import TransactionService
from src.utils.helpers import format_price
from src.ui.components.loading_overlay import LoadingOverlay, WorkerThread


class TransactionDialog(QDialog):
    """Dialog for recording a Buy (purchase) or Sell (sale) transaction."""

    def __init__(self, product: Product, transaction_type: str, parent=None):
        super().__init__(parent)
        self.product = product
        self.transaction_type = transaction_type
        self.transaction_service = TransactionService()

        title = "Record Purchase" if transaction_type == "purchase" else "Record Sale"
        self.setWindowTitle(f"{title} - {product.name}")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        from src.ui.theme import COLORS

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_group = QGroupBox("Product")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Brand:", QLabel(self.product.brand or "\u2014"))
        info_layout.addRow("Model:", QLabel(self.product.model or "\u2014"))
        info_layout.addRow("Current Stock:", QLabel(str(self.product.quantity)))
        layout.addWidget(info_group)

        trans_group = QGroupBox("Transaction Details")
        trans_layout = QFormLayout(trans_group)

        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(99999)
        self.quantity_input.setValue(1)
        self.quantity_input.setFixedHeight(38)
        self.quantity_input.valueChanged.connect(self._update_total)

        if self.transaction_type == "sale":
            # Original price (read-only, shows the fixed sale price)
            self.original_price_label = QLabel(format_price(self.product.sale_price))
            self.original_price_label.setStyleSheet(
                f"font-weight: 600; color: {COLORS['text_secondary']};"
            )
            trans_layout.addRow("Listed Price:", self.original_price_label)

        # Actual selling/buying price (editable)
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setMaximum(9999999)
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setSingleStep(50)
        self.unit_price_input.setPrefix("Rs. ")
        self.unit_price_input.setFixedHeight(38)
        if self.transaction_type == "sale":
            self.unit_price_input.setValue(self.product.sale_price)
        else:
            self.unit_price_input.setValue(self.product.purchase_price)
        self.unit_price_input.valueChanged.connect(self._update_total)

        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Discount label (only for sales)
        if self.transaction_type == "sale":
            self.discount_label = QLabel()
            self.discount_label.setStyleSheet(f"font-weight: 600;")

        self._update_total()

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Optional - customer/supplier name")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Optional notes...")

        trans_layout.addRow("Quantity:", self.quantity_input)
        price_label = "Sold At:" if self.transaction_type == "sale" else "Price:"
        trans_layout.addRow(price_label, self.unit_price_input)
        if self.transaction_type == "sale":
            trans_layout.addRow("Discount:", self.discount_label)
        trans_layout.addRow("Total:", self.total_label)
        trans_layout.addRow("Customer/Supplier:", self.customer_input)
        trans_layout.addRow("Notes:", self.notes_input)
        layout.addWidget(trans_group)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        self.save_btn = btn_box.button(QDialogButtonBox.StandardButton.Save)
        if self.transaction_type == "purchase":
            self.save_btn.setObjectName("successBtn")
            self.save_btn.setText("Record Purchase")
        else:
            from src.ui.theme import COLORS
            self.save_btn.setStyleSheet(
                f"background-color: {COLORS['peach']}; color: #11111b; border: none; "
                "border-radius: 6px; font-weight: bold; padding: 8px 16px;"
            )
            self.save_btn.setText("Record Sale")
        layout.addWidget(btn_box)

        self._loading = LoadingOverlay(self)

    def _update_total(self):
        from src.ui.theme import COLORS
        qty = self.quantity_input.value()
        sold_price = self.unit_price_input.value()
        total = qty * sold_price
        self.total_label.setText(format_price(total))

        if self.transaction_type == "sale":
            original = self.product.sale_price
            diff = original - sold_price
            if diff > 0:
                self.discount_label.setText(f"-{format_price(diff)} per unit")
                self.discount_label.setStyleSheet(f"font-weight: 600; color: {COLORS['red']};")
            elif diff < 0:
                self.discount_label.setText(f"+{format_price(abs(diff))} per unit")
                self.discount_label.setStyleSheet(f"font-weight: 600; color: {COLORS['green']};")
            else:
                self.discount_label.setText("No discount")
                self.discount_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_muted']};")

    def _on_save(self):
        quantity = self.quantity_input.value()
        unit_price = self.unit_price_input.value()

        if quantity <= 0:
            QMessageBox.warning(self, "Validation", "Quantity must be at least 1.")
            return
        if unit_price <= 0:
            QMessageBox.warning(self, "Validation", "Price must be greater than 0.")
            return

        customer_info = self.customer_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        product_id = self.product.id
        txn_type = self.transaction_type

        original_text = self.save_btn.text()
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")
        self._loading.show_overlay("Recording transaction...")

        def do_save():
            if txn_type == "purchase":
                self.transaction_service.record_purchase(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    customer_info=customer_info,
                    notes=notes,
                )
            else:
                self.transaction_service.record_sale(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    original_price=self.product.sale_price,
                    customer_info=customer_info,
                    notes=notes,
                )
            return True

        def on_success(_):
            self._loading.hide_overlay()
            self.accept()

        def on_error(error_msg):
            self._loading.hide_overlay()
            self.save_btn.setEnabled(True)
            self.save_btn.setText(original_text)
            QMessageBox.critical(self, "Error", f"Transaction failed:\n{error_msg}")

        self._save_worker = WorkerThread(do_save)
        self._save_worker.finished.connect(on_success)
        self._save_worker.error.connect(on_error)
        self._save_worker.start()
