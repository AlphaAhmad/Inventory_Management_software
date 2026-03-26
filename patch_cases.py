import re

with open("src/ui/pages/cases_page.py", "r") as f:
    text = f.read()

# Replace hardcoded combo with dynamic loading
target1 = """        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Subcategories")
        self.filter_combo.addItems([
            "TPU Bumper Case", "Original Branded Case", "Local Branded Case"
        ])
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        add_btn = QPushButton("Add New")"""

replacement1 = """        self.filter_combo = QComboBox()
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)
        
        self._load_subcategories()

        filter_row.addStretch()

        add_sub_btn = QPushButton("Add Subcategory")
        add_sub_btn.setObjectName("secondaryBtn")
        add_sub_btn.clicked.connect(self._on_add_subcategory)
        filter_row.addWidget(add_sub_btn)

        add_btn = QPushButton("Add New Product")"""

new_methods = """
    def _load_subcategories(self):
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("All Subcategories")
        if self.category_id:
            subs = self.inventory_service.get_subcategories(self.category_id)
            for s in subs:
                self.filter_combo.addItem(s.name, s.id)
        self.filter_combo.blockSignals(False)

    def _on_add_subcategory(self):
        from PySide6.QtWidgets import QInputDialog
        from src.models.category import Subcategory, ProductType
        from src.models.attribute import AttributeDefinition
        
        name, ok = QInputDialog.getText(self, "Add Subcategory", "Enter subcategory name (e.g. Silicone Case):")
        if ok and name.strip():
            try:
                # Create Subcategory
                sub = Subcategory(category_id=self.category_id, name=name.strip())
                created_sub = self.inventory_service.create_subcategory(sub)
                
                # Create generic Product Type for it
                pt = ProductType(subcategory_id=created_sub.id, name=f"General {name.strip()}")
                created_pt = self.inventory_service.create_product_type(pt)
                
                # Add basic attributes for Case
                attrs = [
                    AttributeDefinition(product_type_id=created_pt.id, name="compatible_model", label="Compatible Model", field_type="text", is_required=True, display_order=1),
                    AttributeDefinition(product_type_id=created_pt.id, name="color", label="Color", field_type="text", display_order=2),
                    AttributeDefinition(product_type_id=created_pt.id, name="case_material", label="Material", field_type="select", options=["Soft TPU", "Hard TPU", "MagSafe TPU", "Silicone", "Leather"], display_order=3)
                ]
                for attr in attrs:
                    self.inventory_service.create_attribute_definition(attr)
                
                self._load_subcategories()
                self.filter_combo.setCurrentText(name.strip())
                QMessageBox.information(self, "Success", f"Subcategory '{name.strip()}' added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add subcategory: {e}")
"""

text = text.replace(target1, replacement1)
text = text.replace("    def refresh_data(self):", new_methods + "\n    def refresh_data(self):")

with open("src/ui/pages/cases_page.py", "w") as f:
    f.write(text)

