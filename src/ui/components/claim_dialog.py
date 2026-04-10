from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox, QGroupBox,
)
from src.models.product import Product, PhoneDetails
from src.services.transaction_service import TransactionService
from src.ui.components.loading_overlay import LoadingOverlay, WorkerThread
from src.ui.theme import COLORS


class ClaimDialog(QDialog):
    """Dialog for initiating a warranty/defect claim on any product."""

    def __init__(self, product: Product, phone_details: PhoneDetails | None = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.phone_details = phone_details
        self.transaction_service = TransactionService()

        self.setWindowTitle(f"Submit Claim - {product.brand} {product.model}")
        self.setMinimumWidth(420)

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
        if self.phone_details:
            if self.phone_details.serial_number:
                info_layout.addRow("Serial No:", QLabel(self.phone_details.serial_number))
            if self.phone_details.imei1:
                info_layout.addRow("IMEI 1:", QLabel(self.phone_details.imei1))
            if self.phone_details.imei2:
                info_layout.addRow("IMEI 2:", QLabel(self.phone_details.imei2))
        if self._last_sale and self._last_sale.customer_info:
            info_layout.addRow("Sold To:", QLabel(self._last_sale.customer_info))
        layout.addWidget(info_group)

        # Claim details
        claim_group = QGroupBox("Claim Details")
        claim_layout = QFormLayout(claim_group)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Describe the defect or claim reason (required)")

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Customer name")
        if self._last_sale and self._last_sale.customer_info:
            self.customer_input.setText(self._last_sale.customer_info)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Optional notes...")

        claim_layout.addRow("Claim Reason:", self.reason_input)
        claim_layout.addRow("Customer:", self.customer_input)
        claim_layout.addRow("Notes:", self.notes_input)
        layout.addWidget(claim_group)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        self.save_btn = btn_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_btn.setText("Submit Claim")
        self.save_btn.setStyleSheet(
            f"background-color: {COLORS['purple']}; color: #ffffff; border: none; "
            "border-radius: 6px; font-weight: bold; padding: 8px 16px;"
        )
        layout.addWidget(btn_box)

        self._loading = LoadingOverlay(self)

    def _on_save(self):
        reason = self.reason_input.text().strip()
        if not reason:
            QMessageBox.warning(self, "Validation", "Claim reason is required.")
            self.reason_input.setFocus()
            return

        customer = self.customer_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        claim_reason = reason + (f" - {notes}" if notes else "")
        product_id = self.product.id

        original_text = self.save_btn.text()
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")
        self._loading.show_overlay("Submitting claim...")

        def do_save():
            self.transaction_service.record_claim(
                product_id=product_id,
                claim_reason=claim_reason,
                customer_info=customer,
            )
            return True

        def on_success(_):
            self._loading.hide_overlay()
            self.accept()

        def on_error(error_msg):
            self._loading.hide_overlay()
            self.save_btn.setEnabled(True)
            self.save_btn.setText(original_text)
            QMessageBox.critical(self, "Error", f"Claim failed:\n{error_msg}")

        self._save_worker = WorkerThread(do_save)
        self._save_worker.finished.connect(on_success)
        self._save_worker.error.connect(on_error)
        self._save_worker.start()
