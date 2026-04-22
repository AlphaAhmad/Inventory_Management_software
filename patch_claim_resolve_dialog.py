import re

with open("src/ui/components/claim_resolve_dialog.py", "r") as f:
    text = f.read()

ui_target = """        resolve_layout.addRow("Outcome:", self.outcome_combo)
        resolve_layout.addRow("Notes:", self.notes_input)

        # Explanation labels"""

ui_replacement = """        resolve_layout.addRow("Outcome:", self.outcome_combo)
        resolve_layout.addRow("Notes:", self.notes_input)

        if self.phone_details:
            self.restock_group = QGroupBox("Restock Options (Phone - if Accepted)")
            restock_layout = QFormLayout(self.restock_group)
            self.phone_type_combo = QComboBox()
            self.phone_type_combo.addItem(f"Same as before ({self.phone_details.phone_type})", "")
            self.phone_type_combo.addItem("Used", "used")
            self.phone_type_combo.addItem("Box Pack", "box_pack")
            
            self.condition_combo = QComboBox()
            self.condition_combo.addItems(["", "excellent", "good", "fair", "poor"])
            
            def update_condition_state():
                pt = self.phone_type_combo.currentData() or self.phone_details.phone_type
                is_accepted = self.outcome_combo.currentText() == "Accepted"
                self.restock_group.setEnabled(is_accepted)
                self.condition_combo.setEnabled(pt == "used" and is_accepted)
                if pt != "used":
                    self.condition_combo.setCurrentIndex(0)
                elif self.phone_details.condition and not self.phone_type_combo.currentData():
                    idx = self.condition_combo.findText(self.phone_details.condition)
                    if idx >= 0: self.condition_combo.setCurrentIndex(idx)
                    
            self.phone_type_combo.currentIndexChanged.connect(update_condition_state)
            self.outcome_combo.currentIndexChanged.connect(update_condition_state)
            
            restock_layout.addRow("Restock Type:", self.phone_type_combo)
            restock_layout.addRow("Condition:", self.condition_combo)
            layout.addWidget(self.restock_group)
            update_condition_state()
        else:
            self.restock_group = None

        # Explanation labels"""

text = text.replace(ui_target, ui_replacement)

save_target = """        def do_save():
            self.transaction_service.resolve_claim(
                product_id=product_id,
                accepted=accepted,
                notes=notes,
            )"""

save_replacement = """        def do_save():
            new_type = None
            new_cond = None
            if getattr(self, "restock_group", None) and self.phone_details and accepted:
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
            )"""
text = text.replace(save_target, save_replacement)

with open("src/ui/components/claim_resolve_dialog.py", "w") as f:
    f.write(text)

