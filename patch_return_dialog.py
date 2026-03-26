import re

with open("src/ui/components/return_dialog.py", "r") as f:
    text = f.read()

# Add InventoryService import
import_target = "from src.services.transaction_service import TransactionService"
import_replacement = "from src.services.transaction_service import TransactionService\nfrom src.services.inventory_service import InventoryService"
text = text.replace(import_target, import_replacement)

# Add phone_details fetch
init_target = """        self.transaction_service = TransactionService()"""
init_replacement = """        self.transaction_service = TransactionService()
        self.inventory_service = InventoryService()
        self.phone_details = self.inventory_service.get_phone_details(product.id)"""
text = text.replace(init_target, init_replacement)

# Add restock options UI
ui_target = """        return_layout.addRow("Refund Amount:", self.refund_input)
        return_layout.addRow("Reason:", self.reason_combo)
        return_layout.addRow("Customer:", self.customer_input)
        return_layout.addRow("Notes:", self.notes_input)
        layout.addWidget(return_group)"""

ui_replacement = """        return_layout.addRow("Refund Amount:", self.refund_input)
        return_layout.addRow("Reason:", self.reason_combo)
        return_layout.addRow("Customer:", self.customer_input)
        return_layout.addRow("Notes:", self.notes_input)
        layout.addWidget(return_group)

        if self.phone_details:
            self.restock_group = QGroupBox("Restock Options (Phone)")
            restock_layout = QFormLayout(self.restock_group)
            
            self.phone_type_combo = QComboBox()
            self.phone_type_combo.addItem(f"Same as before ({self.phone_details.phone_type})", "")
            self.phone_type_combo.addItem("Used", "used")
            self.phone_type_combo.addItem("Box Pack", "box_pack")
            
            self.condition_combo = QComboBox()
            self.condition_combo.addItems(["", "excellent", "good", "fair", "poor"])
            
            def update_condition_state():
                pt = self.phone_type_combo.currentData() or self.phone_details.phone_type
                self.condition_combo.setEnabled(pt == "used")
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                elif self.phone_details.condition and not self.phone_type_combo.currentData():
                    idx = self.condition_combo.findText(self.phone_details.condition)
                    if idx >= 0: self.condition_combo.setCurrentIndex(idx)
                    
            self.phone_type_combo.currentIndexChanged.connect(update_condition_state)
            
            restock_layout.addRow("Restock Type:", self.phone_type_combo)
            restock_layout.addRow("Condition:", self.condition_combo)
            layout.addWidget(self.restock_group)
            update_condition_state()
        else:
            self.restock_group = None"""
            
text = text.replace(ui_target, ui_replacement)

# Update save logic
save_target = """        def do_save():
            self.transaction_service.record_return(
                product_id=product_id,
                refund_amount=refund,
                customer_info=customer,
                return_reason=return_reason,
            )"""
            
save_replacement = """        def do_save():
            new_type = None
            new_cond = None
            if getattr(self, "restock_group", None) and self.phone_details:
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
            )"""
text = text.replace(save_target, save_replacement)

with open("src/ui/components/return_dialog.py", "w") as f:
    f.write(text)

