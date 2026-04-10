from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QScrollArea, QWidget, QFrame, QPushButton, QHBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from src.models.product import Product, PhoneDetails
from src.utils.helpers import format_price
from src.ui.theme import COLORS

class ProductInfoDialog(QDialog):
    """Read-only dialog to show all product details."""

    def __init__(self, product: Product, phone_details: PhoneDetails | None = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.phone_details = phone_details
        
        self.setWindowTitle("Product Info")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header_lbl = QLabel(f"{self.product.brand} {self.product.model}".strip() or "Product Details")
        header_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS.get('accent', '#fff')};")
        layout.addWidget(header_lbl)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        form = QFormLayout(scroll_content)
        form.setSpacing(12)
        
        def add_row(key, val):
            if val is not None and val != "":
                if "compatible" in key.lower() or "\n" in str(val):
                    text_edit = QTextEdit()
                    text_edit.setReadOnly(True)
                    text_edit.setPlainText(str(val))
                    text_edit.setFixedHeight(100) # Give it a fixed scrollable height
                    text_edit.setStyleSheet(f"color: {COLORS.get('text_primary', '#fff')}; background: transparent; border: 1px solid #333;")
                    form.addRow(f"{key}:", text_edit)
                else:
                    lbl_val = QLabel(str(val))
                    lbl_val.setWordWrap(True)
                    lbl_val.setStyleSheet(f"color: {COLORS.get('text_primary', '#fff')};")
                    form.addRow(f"{key}:", lbl_val)

        # Common attributes
        add_row("Status", self.product.status.replace("_", " ").title())
        add_row("Quantity", self.product.quantity)
        add_row("Purchase Price", format_price(self.product.purchase_price))
        add_row("Sale Price", format_price(self.product.sale_price))
        add_row("Notes", self.product.notes)
        
        # Phone details
        if self.phone_details:
            form.addRow(QLabel(""), QLabel("")) # spacing
            type_lbl = QLabel("Device Details")
            type_lbl.setStyleSheet(f"font-weight: bold; color: {COLORS.get('peach', '#fcb045')};")
            form.addRow(type_lbl)
            
            p = self.phone_details
            add_row("Type", p.phone_type.replace("_", " ").title())
            if p.condition: add_row("Condition", p.condition.title())
            if p.serial_number: add_row("Serial No", p.serial_number)
            if p.imei1: add_row("IMEI 1", p.imei1)
            if p.imei2: add_row("IMEI 2", p.imei2)
            if p.color: add_row("Color", p.color)
            if p.region_variant: add_row("Variant", p.region_variant)
            if p.storage_gb: add_row("Storage", f"{p.storage_gb} GB")
            if p.ram_gb: add_row("RAM", f"{p.ram_gb} GB")
            add_row("Has Box", "Yes" if p.has_box else "No")
            add_row("Has Charger", "Yes" if p.has_charger else "No")
            if p.keypad_type: add_row("Keypad Type", p.keypad_type.replace("_", " ").title())
            if p.is_claimed:
                add_row("Claim Pending", "Yes")
                add_row("Claim Reason", p.claim_reason)

        # Other dynamic attributes
        if self.product.attributes:
            form.addRow(QLabel(""), QLabel("")) # spacing
            spec_lbl = QLabel("Specifications")
            spec_lbl.setStyleSheet(f"font-weight: bold; color: {COLORS.get('green', '#00ff00')};")
            form.addRow(spec_lbl)
            
            for k, v in self.product.attributes.items():
                if v:
                    display_key = k.replace("_", " ").title()
                    add_row(display_key, v)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
