from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QTextEdit, QDialogButtonBox, QMessageBox, QGroupBox,
)
from src.models.product import Product, PhoneDetails
from src.services.transaction_service import TransactionService
from src.services.inventory_service import InventoryService
from src.ui.components.loading_overlay import LoadingOverlay, WorkerThread
from src.ui.theme import COLORS


class ClaimResolveDialog(QDialog):
    """Dialog for resolving a warranty/defect claim."""

    def __init__(self, product: Product, phone_details: PhoneDetails | None = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.phone_details = phone_details
        self.transaction_service = TransactionService()

        self.setWindowTitle(f"Resolve Claim - {product.brand} {product.model}")
        self.setMinimumWidth(420)
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
            if self.phone_details.imei1:
                info_layout.addRow("IMEI 1:", QLabel(self.phone_details.imei1))
            if self.phone_details.claim_reason:
                reason_label = QLabel(self.phone_details.claim_reason)
                reason_label.setWordWrap(True)
                reason_label.setStyleSheet(f"color: {COLORS['yellow']};")
                info_layout.addRow("Claim Reason:", reason_label)
        layout.addWidget(info_group)

        # Resolution
        resolve_group = QGroupBox("Resolution")
        resolve_layout = QFormLayout(resolve_group)

        self.outcome_combo = QComboBox()
        self.outcome_combo.addItems(["Accepted", "Rejected"])

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Resolution notes...")

        resolve_layout.addRow("Outcome:", self.outcome_combo)
        resolve_layout.addRow("Notes:", self.notes_input)

        self.restock_group = QGroupBox("Restock Options (if Accepted)")
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
            is_accepted = self.outcome_combo.currentText() == "Accepted"
            self.restock_group.setEnabled(is_accepted)
            if self.phone_details:
                pt = self.phone_type_combo.currentData() or self.phone_details.phone_type
                self.condition_combo.setEnabled(pt == "used" and is_accepted)
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                elif self.phone_details.condition and not self.phone_type_combo.currentData():
                    idx = self.condition_combo.findText(self.phone_details.condition)
                    if idx >= 0: self.condition_combo.setCurrentIndex(idx)
            else:
                pt = self.phone_type_combo.currentData()
                self.condition_combo.setEnabled(pt == "used" and is_accepted)
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                    
        self.phone_type_combo.currentIndexChanged.connect(update_condition_state)
        self.outcome_combo.currentIndexChanged.connect(update_condition_state)
        
        if self.phone_details:
            restock_layout.addRow("Restock Type:", self.phone_type_combo)
        else:
            restock_layout.addRow("Restock As:", self.phone_type_combo)
        
        restock_layout.addRow("Condition:", self.condition_combo)
        layout.addWidget(self.restock_group)
        update_condition_state()

        # Explanation labels
        accepted_info = QLabel(
            "Accepted: Product returns to inventory (in stock, qty = 1)"
        )
        accepted_info.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        accepted_info.setWordWrap(True)
        resolve_layout.addRow("", accepted_info)

        rejected_info = QLabel(
            "Rejected: Product goes back to customer (stays sold, qty = 0)"
        )
        rejected_info.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px;")
        rejected_info.setWordWrap(True)
        resolve_layout.addRow("", rejected_info)

        layout.addWidget(resolve_group)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        self.save_btn = btn_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_btn.setText("Resolve Claim")
        self.save_btn.setStyleSheet(
            f"background-color: {COLORS['peach']}; color: #11111b; border: none; "
            "border-radius: 6px; font-weight: bold; padding: 8px 16px;"
        )
        layout.addWidget(btn_box)

        self._loading = LoadingOverlay(self)

    def _on_save(self):
        accepted = self.outcome_combo.currentText() == "Accepted"
        notes = self.notes_input.toPlainText().strip()
        product_id = self.product.id

        original_text = self.save_btn.text()
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")
        self._loading.show_overlay("Resolving claim...")

        def do_save():
            new_type = None
            new_cond = None
            if getattr(self, "restock_group", None) and accepted:
                if self.phone_type_combo.currentData():
                    new_type = self.phone_type_combo.currentData()
                if self.condition_combo.isEnabled():
                    new_cond = self.condition_combo.currentText()
            
            self.transaction_service.resolve_claim(
                product_id=product_id,
                accepted=accepted,
                notes=notes,
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
            QMessageBox.critical(self, "Error", f"Resolve failed:\n{error_msg}")

        self._save_worker = WorkerThread(do_save)
        self._save_worker.finished.connect(on_success)
        self._save_worker.error.connect(on_error)
        self._save_worker.start()
