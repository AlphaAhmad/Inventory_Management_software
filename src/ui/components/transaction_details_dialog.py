from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QScrollArea, QWidget, QFrame, QPushButton, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from src.models.transaction import Transaction
from src.models.product import Product, PhoneDetails
from src.services.transaction_service import TransactionService
from src.utils.helpers import format_price
from src.ui.theme import COLORS


class TransactionDetailsDialog(QDialog):
    """Read-only dialog showing transaction details + the related product info."""

    reverted = Signal()  # Emitted when the transaction is successfully reverted

    TYPE_COLORS = {
        "purchase": "green",
        "sale": "peach",
        "return": "yellow",
        "claim": "purple",
        "claim_resolved": "cyan",
    }

    def __init__(
        self,
        transaction: Transaction,
        product: Product | None = None,
        phone_details: PhoneDetails | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.transaction = transaction
        self.product = product
        self.phone_details = phone_details

        type_label = transaction.type.replace("_", " ").title()
        self.setWindowTitle(f"Transaction Details - {type_label}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        type_label = self.transaction.type.replace("_", " ").title()
        type_color = COLORS.get(self.TYPE_COLORS.get(self.transaction.type, "accent"), COLORS["accent"])
        header = QLabel(f"{type_label} Transaction")
        header.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {type_color};"
        )
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(12)

        # ── Transaction details group ──
        txn_group = QGroupBox("Transaction")
        txn_form = QFormLayout(txn_group)

        def add_form_row(form, key, val, color=None):
            if val is None or val == "":
                return
            lbl = QLabel(str(val))
            lbl.setWordWrap(True)
            style = f"color: {color or COLORS['text_primary']};"
            lbl.setStyleSheet(style)
            form.addRow(f"{key}:", lbl)

        date_str = self.transaction.created_at[:19].replace("T", " ") if self.transaction.created_at else ""
        add_form_row(txn_form, "Date", date_str)
        add_form_row(txn_form, "Type", type_label, type_color)
        add_form_row(txn_form, "Quantity", self.transaction.quantity)

        # Price labels vary by transaction type
        if self.transaction.type == "sale":
            if self.transaction.original_price:
                add_form_row(txn_form, "Listed Price", format_price(self.transaction.original_price))
                if self.transaction.unit_price != self.transaction.original_price:
                    diff = self.transaction.original_price - self.transaction.unit_price
                    if diff > 0:
                        add_form_row(txn_form, "Discount", f"-{format_price(diff)}", COLORS["red"])
                    else:
                        add_form_row(txn_form, "Markup", f"+{format_price(abs(diff))}", COLORS["green"])
            add_form_row(txn_form, "Sold At", format_price(self.transaction.unit_price))
            add_form_row(txn_form, "Total", format_price(self.transaction.total_price))
        elif self.transaction.type == "return":
            if self.transaction.original_price:
                add_form_row(txn_form, "Original Sale Price", format_price(self.transaction.original_price))
            add_form_row(txn_form, "Refund Amount", format_price(self.transaction.unit_price))
        elif self.transaction.type == "purchase":
            add_form_row(txn_form, "Unit Price", format_price(self.transaction.unit_price))
            add_form_row(txn_form, "Total", format_price(self.transaction.total_price))
        elif self.transaction.type in ("claim", "claim_resolved"):
            pass  # No price for claims

        if self.transaction.customer_info:
            label = "Customer/Supplier"
            if self.transaction.type == "purchase":
                label = "Supplier"
            elif self.transaction.type in ("sale", "return", "claim"):
                label = "Customer"
            add_form_row(txn_form, label, self.transaction.customer_info)

        if self.transaction.notes:
            add_form_row(txn_form, "Notes", self.transaction.notes)

        content_layout.addWidget(txn_group)

        # ── Product info group ──
        if self.product:
            prod_group = QGroupBox("Product")
            prod_form = QFormLayout(prod_group)

            add_form_row(prod_form, "Brand", self.product.brand)
            add_form_row(prod_form, "Model", self.product.model)
            add_form_row(prod_form, "Status", self.product.status.replace("_", " ").title())
            add_form_row(prod_form, "Current Stock", self.product.quantity)
            add_form_row(prod_form, "Purchase Price", format_price(self.product.purchase_price))
            add_form_row(prod_form, "Sale Price", format_price(self.product.sale_price))
            if self.product.notes:
                add_form_row(prod_form, "Notes", self.product.notes)

            content_layout.addWidget(prod_group)

            # ── Phone details ──
            if self.phone_details:
                phone_group = QGroupBox("Device Details")
                phone_form = QFormLayout(phone_group)
                p = self.phone_details
                add_form_row(phone_form, "Type", p.phone_type.replace("_", " ").title())
                if p.condition:
                    add_form_row(phone_form, "Condition", p.condition.title())
                if p.serial_number:
                    add_form_row(phone_form, "Serial No", p.serial_number)
                if p.imei1:
                    add_form_row(phone_form, "IMEI 1", p.imei1)
                if p.imei2:
                    add_form_row(phone_form, "IMEI 2", p.imei2)
                if p.color:
                    add_form_row(phone_form, "Color", p.color)
                if p.region_variant:
                    add_form_row(phone_form, "Variant", p.region_variant)
                if p.storage_gb:
                    add_form_row(phone_form, "Storage", f"{p.storage_gb} GB")
                if p.ram_gb:
                    add_form_row(phone_form, "RAM", f"{p.ram_gb} GB")
                add_form_row(phone_form, "Has Box", "Yes" if p.has_box else "No")
                add_form_row(phone_form, "Has Charger", "Yes" if p.has_charger else "No")
                if p.keypad_type:
                    add_form_row(phone_form, "Keypad Type", p.keypad_type.replace("_", " ").title())
                if p.is_claimed:
                    add_form_row(phone_form, "Claim Pending", "Yes", COLORS["yellow"])
                    if p.claim_reason:
                        add_form_row(phone_form, "Claim Reason", p.claim_reason, COLORS["yellow"])

                content_layout.addWidget(phone_group)

            # ── Other dynamic attributes ──
            if self.product.attributes:
                # Filter out the enriched display fields we put there for the table
                skip_keys = {"imei_1", "ram", "storage"}
                extras = {k: v for k, v in self.product.attributes.items()
                          if v and k not in skip_keys}
                if extras:
                    spec_group = QGroupBox("Specifications")
                    spec_form = QFormLayout(spec_group)
                    for k, v in extras.items():
                        display_key = k.replace("_", " ").title()
                        add_form_row(spec_form, display_key, v)
                    content_layout.addWidget(spec_group)
        else:
            missing = QLabel("Product no longer exists in inventory.")
            missing.setStyleSheet(f"color: {COLORS['text_muted']}; font-style: italic;")
            content_layout.addWidget(missing)

        content_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # ── Buttons: Revert (left) + Close (right) ──
        btn_layout = QHBoxLayout()

        self.revert_btn = QPushButton("\u21BA  Revert Transaction")
        self.revert_btn.setMinimumWidth(170)
        self.revert_btn.setToolTip(
            "Undo this transaction as if it never happened. "
            "Only the most recent transaction for a product can be reverted."
        )
        self.revert_btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['red']}; color: #ffffff; "
            f"border: none; border-radius: 6px; font-weight: bold; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: #ff85a0; }}"
            f"QPushButton:disabled {{ background-color: {COLORS['bg_lighter']}; "
            f"color: {COLORS['text_muted']}; }}"
        )
        self.revert_btn.clicked.connect(self._on_revert_clicked)
        # Only enable if the product still exists — the latest-check happens server-side.
        self.revert_btn.setEnabled(self.product is not None)
        btn_layout.addWidget(self.revert_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_revert_clicked(self):
        type_label = self.transaction.type.replace("_", " ").title()
        product_label = ""
        if self.product:
            product_label = f"\n\nProduct: {self.product.brand} {self.product.model}".strip()

        # Per-type description of what will happen
        effect_lines = {
            "sale": "The sold quantity will be added back to stock. "
                    "If the product was fully sold, it will return to in-stock.",
            "purchase": "The purchased quantity will be removed from stock.",
            "return": "The returned unit will be removed from stock. "
                      "Note: the product's purchase price (cost basis) was overwritten "
                      "when the return was recorded and cannot be restored automatically.",
            "claim": "The product will return to 'sold' status and the claim flag will be cleared.",
            "claim_resolved": "The product will return to 'claimed' status. "
                              "If the claim was accepted, the restocked unit will be removed.",
        }
        effect = effect_lines.get(self.transaction.type, "The transaction will be deleted.")

        confirm = QMessageBox.question(
            self, "Revert Transaction?",
            f"Are you sure you want to revert this {type_label} transaction?{product_label}\n\n"
            f"{effect}\n\n"
            f"The transaction record will be permanently deleted. "
            f"Only the most recent transaction for this product can be reverted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            TransactionService().revert_transaction(self.transaction.id)
        except Exception as e:
            QMessageBox.critical(self, "Revert Failed", str(e))
            return

        QMessageBox.information(
            self, "Reverted",
            f"{type_label} transaction reverted successfully."
        )
        self.reverted.emit()
        self.accept()
