from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QLabel, QGroupBox, QTextEdit,
    QDialog, QDialogButtonBox, QPushButton, QMessageBox,
    QScrollArea, QFrame,
)
from PySide6.QtCore import Qt
from src.models.attribute import AttributeDefinition
from src.models.product import Product, PhoneDetails
from src.models.category import ProductType, Subcategory
from src.services.inventory_service import InventoryService
from src.ui.components.loading_overlay import LoadingOverlay, WorkerThread
from src.ui.theme import COLORS


class DynamicFormDialog(QDialog):
    """Dialog that auto-generates form fields based on attribute definitions."""

    def __init__(
        self,
        inventory_service: InventoryService,
        category_id: str,
        product: Product | None = None,
        phone_details: PhoneDetails | None = None,
        subcategory_id: str | None = None,
        brand_name: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.category_id = category_id
        self.product = product
        self.phone_details = phone_details
        self.is_edit = product is not None
        self._fixed_subcategory_id = subcategory_id
        self._fixed_brand_name = brand_name
        self._attr_widgets: dict[str, QWidget] = {}
        self._imei_rows: list[tuple[QLineEdit, QLineEdit]] = []  # (imei1, imei2) per unit

        self.setWindowTitle("Edit Product" if self.is_edit else "Add New Product")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        self.form_layout = QVBoxLayout(scroll_content)
        self.form_layout.setSpacing(12)

        # ── Category selector (only for new products) ──
        if not self.is_edit:
            selector_group = QGroupBox("Product Category")
            selector_group.setStyleSheet(
                f"QGroupBox {{ border: 2px solid {COLORS['accent']}80; }}"
                f"QGroupBox::title {{ color: {COLORS['accent']}; }}"
            )
            selector_layout = QFormLayout(selector_group)

            self.product_type_combo = QComboBox()
            self.product_type_combo.currentIndexChanged.connect(self._on_product_type_change)

            if self._fixed_subcategory_id:
                self.subcategory_combo = None
                self.product_type_combo.addItem("-- Select Product Type --", None)
                product_types = self.inventory_service.get_product_types(self._fixed_subcategory_id)
                for pt in product_types:
                    self.product_type_combo.addItem(pt.name, pt.id)
                selector_layout.addRow("Product Type:", self.product_type_combo)
            else:
                self.subcategory_combo = QComboBox()
                self.subcategory_combo.addItem("-- Select Subcategory --", None)
                self.subcategory_combo.currentIndexChanged.connect(self._on_subcategory_change)
                subcategories = self.inventory_service.get_subcategories(self.category_id)
                for sub in subcategories:
                    self.subcategory_combo.addItem(sub.name, sub.id)
                selector_layout.addRow("Subcategory:", self.subcategory_combo)
                selector_layout.addRow("Product Type:", self.product_type_combo)

            self.form_layout.addWidget(selector_group)

        # ── Common fields ──
        common_group = QGroupBox("Product Details")
        common_layout = QFormLayout(common_group)

        self.brand_input = QLineEdit()
        self.model_input = QLineEdit()
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setMaximum(9999999)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setSingleStep(50)
        self.purchase_price_input.setPrefix("Rs. ")
        self.purchase_price_input.setFixedHeight(38)
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMaximum(9999999)
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setSingleStep(50)
        self.sale_price_input.setPrefix("Rs. ")
        self.sale_price_input.setFixedHeight(38)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(99999)
        self.quantity_input.setFixedHeight(38)
        self.quantity_input.setMinimum(1)
        self.quantity_input.setValue(1)
        self.quantity_input.valueChanged.connect(self._on_quantity_change)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        if self._fixed_brand_name:
            self.brand_input.setText(self._fixed_brand_name)
            self.brand_input.setReadOnly(True)
            self.brand_input.setVisible(False)
        else:
            common_layout.addRow("Brand:", self.brand_input)

        common_layout.addRow("Model:", self.model_input)
        common_layout.addRow("Purchase Price:", self.purchase_price_input)
        common_layout.addRow("Sale Price:", self.sale_price_input)
        common_layout.addRow("Quantity:", self.quantity_input)
        common_layout.addRow("Notes:", self.notes_input)

        self.form_layout.addWidget(common_group)

        # ── Phone details section (shown conditionally) ──
        self.phone_group = QGroupBox("Phone Details")
        phone_main_layout = QVBoxLayout(self.phone_group)
        phone_main_layout.setSpacing(10)

        # IMEI section - dynamic rows
        self._imei_container = QWidget()
        self._imei_layout = QVBoxLayout(self._imei_container)
        self._imei_layout.setContentsMargins(0, 0, 0, 0)
        self._imei_layout.setSpacing(6)
        phone_main_layout.addWidget(self._imei_container)

        # Shared phone fields
        self.phone_shared_form = QFormLayout()
        self.phone_shared_form.setSpacing(8)

        self.phone_type_combo = QComboBox()
        self.phone_type_combo.addItems(["used", "box_pack", "keypad"])
        self.has_box_check = QCheckBox("Has Box")
        self.has_charger_check = QCheckBox("Has Charger")
        self.keypad_type_combo = QComboBox()
        self.keypad_type_combo.addItems(["", "keys_only", "keypad_touchscreen"])
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["", "excellent", "good", "fair", "poor"])
        self.storage_input = QSpinBox()
        self.storage_input.setMaximum(2048)
        self.storage_input.setSuffix(" GB")
        self.storage_input.setFixedHeight(38)
        self.ram_input = QSpinBox()
        self.ram_input.setMaximum(64)
        self.ram_input.setSuffix(" GB")
        self.ram_input.setFixedHeight(38)
        self.color_input = QLineEdit()
        self.region_variant_input = QLineEdit()
        self.region_variant_input.setPlaceholderText("e.g. LLA, China (iPhone only)")

        self.phone_shared_form.addRow("Phone Type:", self.phone_type_combo)
        self.phone_shared_form.addRow("", self.has_box_check)
        self.phone_shared_form.addRow("", self.has_charger_check)
        self.phone_shared_form.addRow("Keypad Type:", self.keypad_type_combo)
        self.phone_shared_form.addRow("Condition:", self.condition_combo)
        self.phone_shared_form.addRow("Storage:", self.storage_input)
        self.phone_shared_form.addRow("RAM:", self.ram_input)
        self.phone_shared_form.addRow("Color:", self.color_input)
        self.phone_shared_form.addRow("Region Variant:", self.region_variant_input)
        phone_main_layout.addLayout(self.phone_shared_form)
        
        # Hide Variant initially until Brand is iPhone/Apple
        self.region_variant_input.hide()
        self._set_shared_row_visible("Region Variant:", False)

        self.brand_input.textChanged.connect(self._on_brand_changed)

        self.phone_group.setVisible(False)
        self.form_layout.addWidget(self.phone_group)

        # ── Dynamic attributes section ──
        self.attrs_group = QGroupBox("Specifications")
        self.attrs_form = QFormLayout(self.attrs_group)
        self.form_layout.addWidget(self.attrs_group)

        self.form_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # ── Buttons ──
        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.btn_box.accepted.connect(self._on_save)
        self.btn_box.rejected.connect(self.reject)
        self.save_btn = self.btn_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_btn.setObjectName("primaryBtn")
        layout.addWidget(self.btn_box)

        # ── Loading overlay ──
        self._loading = LoadingOverlay(self)

        # ── Populate if editing ──
        if self.is_edit and self.product:
            self._populate_edit_data()

    # ── IMEI row management ──


    def _on_brand_changed(self, text: str):
        is_iphone = "iphone" in text.lower() or "apple" in text.lower()
        self.region_variant_input.setVisible(is_iphone)
        self._set_shared_row_visible("Region Variant:", is_iphone)
        # Process layout update
        self.region_variant_input.parent().update()

    def _build_imei_rows(self, count: int):
        """Rebuild IMEI input rows to match the given count."""
        # Preserve existing values
        old_values = []
        for imei1_input, imei2_input in self._imei_rows:
            old_values.append((imei1_input.text(), imei2_input.text()))

        # Clear old rows
        while self._imei_layout.count() > 0:
            item = self._imei_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._imei_rows.clear()

        for i in range(count):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            label = QLabel(f"Phone {i + 1}:")
            label.setFixedWidth(65)
            label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']};")
            row_layout.addWidget(label)

            imei1 = QLineEdit()
            imei1.setPlaceholderText("IMEI 1 (15 digits)")
            imei1.setMaxLength(15)
            row_layout.addWidget(imei1)

            imei2 = QLineEdit()
            imei2.setPlaceholderText("IMEI 2 (optional)")
            imei2.setMaxLength(15)
            row_layout.addWidget(imei2)

            self._imei_layout.addWidget(row_widget)
            self._imei_rows.append((imei1, imei2))

            # Restore old values
            if i < len(old_values):
                imei1.setText(old_values[i][0])
                imei2.setText(old_values[i][1])

    def _on_quantity_change(self, value: int):
        """When quantity changes, update IMEI rows if phone section is visible."""
        if self.phone_group.isVisible() and not self.is_edit:
            self._build_imei_rows(value)

    # ── Category / product type callbacks ──

    def _on_subcategory_change(self, index: int):
        self.product_type_combo.clear()
        self.product_type_combo.addItem("-- Select Product Type --", None)
        if self.subcategory_combo is None:
            return
        sub_id = self.subcategory_combo.currentData()
        if sub_id:
            product_types = self.inventory_service.get_product_types(sub_id)
            for pt in product_types:
                self.product_type_combo.addItem(pt.name, pt.id)

    def _on_product_type_change(self, index: int):
        pt_id = self.product_type_combo.currentData()
        if pt_id is not None and pt_id:
            self._load_dynamic_attributes(pt_id)
            if self.subcategory_combo is not None:
                sub_name = self.subcategory_combo.currentText()
            else:
                sub_name = ""
            is_phone = sub_name in ("Used Phones", "Box Pack Phones", "Keypad Phones")
            self.phone_group.setVisible(is_phone)
            if is_phone:
                self._configure_phone_fields(sub_name)
                self._build_imei_rows(self.quantity_input.value())

    def _configure_phone_fields(self, sub_name: str):
        """Show/hide phone fields and auto-set phone type based on subcategory."""
        self.phone_type_combo.clear()
        if sub_name == "Used Phones":
            self.phone_type_combo.addItem("used")
            self.keypad_type_combo.setVisible(False)
            self._set_shared_row_visible("Keypad Type:", False)
        elif sub_name == "Box Pack Phones":
            self.phone_type_combo.addItem("box_pack")
            self.keypad_type_combo.setVisible(False)
            self._set_shared_row_visible("Keypad Type:", False)
        elif sub_name == "Keypad Phones":
            self.phone_type_combo.addItem("keypad")
            self.keypad_type_combo.setVisible(True)
            self._set_shared_row_visible("Keypad Type:", True)
        self.phone_type_combo.setEnabled(False)

    def _set_shared_row_visible(self, label_text: str, visible: bool):
        """Show/hide a form row in the shared phone fields by label text."""
        for i in range(self.phone_shared_form.rowCount()):
            label_item = self.phone_shared_form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.phone_shared_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if label_item and label_item.widget() and label_item.widget().text() == label_text:
                label_item.widget().setVisible(visible)
                if field_item and field_item.widget():
                    field_item.widget().setVisible(visible)
                break

    def _load_dynamic_attributes(self, product_type_id: str):
        self._attr_widgets.clear()
        while self.attrs_form.rowCount() > 0:
            self.attrs_form.removeRow(0)

        attr_defs = self.inventory_service.get_attribute_definitions(product_type_id)
        for attr_def in attr_defs:
            widget = self._create_field_widget(attr_def)
            label_text = attr_def.label
            if attr_def.is_required:
                label_text += " *"
            self.attrs_form.addRow(label_text + ":", widget)
            self._attr_widgets[attr_def.name] = widget

    def _create_field_widget(self, attr_def: AttributeDefinition) -> QWidget:
        if attr_def.field_type == "text":
            return QLineEdit()
        elif attr_def.field_type == "number":
            spin = QSpinBox()
            spin.setMaximum(999999)
            spin.setFixedHeight(38)
            return spin
        elif attr_def.field_type == "boolean":
            return QCheckBox()
        elif attr_def.field_type == "select":
            combo = QComboBox()
            combo.addItem("")
            options = attr_def.options if isinstance(attr_def.options, list) else []
            combo.addItems(options)
            return combo
        return QLineEdit()

    # ── Edit population ──

    def _populate_edit_data(self):
        p = self.product
        if not self._fixed_brand_name:
            self.brand_input.setText(p.brand)
        self.model_input.setText(p.model)
        self.purchase_price_input.setValue(p.purchase_price)
        self.sale_price_input.setValue(p.sale_price)
        self.quantity_input.setValue(p.quantity)
        self.notes_input.setPlainText(p.notes)

        self._load_dynamic_attributes(p.product_type_id)

        for attr_name, widget in self._attr_widgets.items():
            value = p.attributes.get(attr_name, "")
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value) if value else 0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                idx = widget.findText(str(value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)

        if self.phone_details:
            self.phone_group.setVisible(True)
            pd = self.phone_details
            # For editing, show single IMEI row (each phone is its own product)
            self._build_imei_rows(1)
            self._imei_rows[0][0].setText(pd.imei1)
            self._imei_rows[0][1].setText(pd.imei2)
            # Lock phone type
            self.phone_type_combo.clear()
            self.phone_type_combo.addItem(pd.phone_type)
            self.phone_type_combo.setEnabled(False)
            is_keypad = pd.phone_type == "keypad"
            self.keypad_type_combo.setVisible(is_keypad)
            self._set_shared_row_visible("Keypad Type:", is_keypad)
            self.has_box_check.setChecked(pd.has_box)
            self.has_charger_check.setChecked(pd.has_charger)
            if is_keypad:
                idx = self.keypad_type_combo.findText(pd.keypad_type)
                if idx >= 0:
                    self.keypad_type_combo.setCurrentIndex(idx)
            idx = self.condition_combo.findText(pd.condition)
            if idx >= 0:
                self.condition_combo.setCurrentIndex(idx)
            self.storage_input.setValue(pd.storage_gb)
            self.ram_input.setValue(pd.ram_gb)
            self.color_input.setText(pd.color)
            self.region_variant_input.setText(pd.region_variant)
            if "iphone" in (self.product.brand or "").lower() or "apple" in (self.product.brand or "").lower():
                self.region_variant_input.setVisible(True)
                self._set_shared_row_visible("Region Variant:", True)

            # Lock quantity for phone edits (each phone = 1 unit)
            self.quantity_input.setEnabled(False)

    # ── Save ──

    def _get_brand_value(self) -> str:
        if self._fixed_brand_name:
            return self._fixed_brand_name
        return self.brand_input.text().strip()

    def _on_save(self):
        brand = self._get_brand_value()
        model = self.model_input.text().strip()

        if not brand and not model:
            QMessageBox.warning(self, "Validation", "Brand or Model is required.")
            return

        name = f"{brand} {model}".strip()

        # Collect dynamic attributes
        attributes = {}
        for attr_name, widget in self._attr_widgets.items():
            if isinstance(widget, QLineEdit):
                attributes[attr_name] = widget.text().strip()
            elif isinstance(widget, QSpinBox):
                attributes[attr_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                attributes[attr_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                attributes[attr_name] = widget.currentText()

        purchase_price = self.purchase_price_input.value()
        sale_price = self.sale_price_input.value()
        quantity = self.quantity_input.value()
        notes = self.notes_input.toPlainText().strip()

        is_phone = self.phone_group.isVisible()

        # Validate and collect IMEI data for phones
        imei_list = []
        if is_phone:
            for i, (imei1_input, imei2_input) in enumerate(self._imei_rows):
                imei1 = imei1_input.text().strip()
                imei2 = imei2_input.text().strip()
                unit_label = f"Phone {i + 1}" if len(self._imei_rows) > 1 else "IMEI 1"

                if not imei1:
                    QMessageBox.warning(self, "Validation", f"{unit_label}: IMEI 1 is required.")
                    imei1_input.setFocus()
                    return
                if not imei1.isdigit() or len(imei1) != 15:
                    QMessageBox.warning(self, "Validation",
                        f"{unit_label}: IMEI 1 must be exactly 15 digits.\n"
                        f"You entered {len(imei1)} characters.")
                    imei1_input.setFocus()
                    return
                if imei2 and (not imei2.isdigit() or len(imei2) != 15):
                    QMessageBox.warning(self, "Validation",
                        f"{unit_label}: IMEI 2 must be exactly 15 digits or left empty.\n"
                        f"You entered {len(imei2)} characters.")
                    imei2_input.setFocus()
                    return
                imei_list.append((imei1, imei2))

        # Collect shared phone detail
        phone_shared = None
        if is_phone:
            phone_shared = {
                "phone_type": self.phone_type_combo.currentText(),
                "has_box": self.has_box_check.isChecked(),
                "has_charger": self.has_charger_check.isChecked(),
                "keypad_type": self.keypad_type_combo.currentText(),
                "condition": self.condition_combo.currentText(),
                "storage_gb": self.storage_input.value(),
                "ram_gb": self.ram_input.value(),
                "color": self.color_input.text().strip(),
                "region_variant": self.region_variant_input.text().strip(),
            }

        # Disable save and show loading
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")
        self._loading.show_overlay("Saving product...")

        if self.is_edit:
            self.product.name = name
            self.product.brand = brand
            self.product.model = model
            self.product.purchase_price = purchase_price
            self.product.sale_price = sale_price
            self.product.quantity = quantity
            self.product.attributes = attributes
            self.product.notes = notes
            product_obj = self.product

            def do_save():
                self.inventory_service.update_product(product_obj)
                if is_phone and imei_list and phone_shared:
                    self._save_phone_details_bg(
                        product_obj.id, imei_list[0][0], imei_list[0][1], phone_shared
                    )
                return True
        else:
            pt_id = self.product_type_combo.currentData()
            if not pt_id:
                self._loading.hide_overlay()
                self.save_btn.setEnabled(True)
                self.save_btn.setText("Save")
                QMessageBox.warning(
                    self, "Validation",
                    "Please select a Product Type from the dropdown.\n\n"
                    "This determines the category of the product."
                )
                return

            if is_phone and imei_list:
                # Phones: create one product per unit, each with qty=1
                def do_save():
                    for imei1, imei2 in imei_list:
                        product = Product(
                            product_type_id=pt_id,
                            name=name,
                            brand=brand,
                            model=model,
                            purchase_price=purchase_price,
                            sale_price=sale_price,
                            quantity=1,
                            status="in_stock",
                            attributes=attributes,
                            notes=notes,
                        )
                        created = self.inventory_service.create_product(product)
                        self._save_phone_details_bg(
                            created.id, imei1, imei2, phone_shared
                        )
                    return True
            else:
                # Non-phone products: single product with given quantity
                new_product = Product(
                    product_type_id=pt_id,
                    name=name,
                    brand=brand,
                    model=model,
                    purchase_price=purchase_price,
                    sale_price=sale_price,
                    quantity=quantity,
                    status="in_stock",
                    attributes=attributes,
                    notes=notes,
                )

                def do_save():
                    self.inventory_service.create_product(new_product)
                    return True

        self._save_worker = WorkerThread(do_save)
        self._save_worker.finished.connect(self._on_save_success)
        self._save_worker.error.connect(self._on_save_error)
        self._save_worker.start()

    def _save_phone_details_bg(self, product_id: str, imei1: str, imei2: str, shared: dict):
        """Save phone details for a single product (called from background thread)."""
        details = PhoneDetails(
            product_id=product_id,
            imei1=imei1,
            imei2=imei2,
            phone_type=shared["phone_type"],
            has_box=shared["has_box"],
            has_charger=shared["has_charger"],
            keypad_type=shared["keypad_type"],
            condition=shared["condition"],
            storage_gb=shared["storage_gb"],
            ram_gb=shared["ram_gb"],
            color=shared["color"],
            region_variant=shared.get("region_variant", ""),
        )
        existing = self.inventory_service.get_phone_details(product_id)
        if existing:
            details.id = existing.id
            self.inventory_service.update_phone_details(details)
        else:
            self.inventory_service.create_phone_details(details)

    def _on_save_success(self, result):
        self._loading.hide_overlay()
        self.accept()

    def _on_save_error(self, error_msg: str):
        self._loading.hide_overlay()
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Save")
        QMessageBox.critical(self, "Error", f"Failed to save product:\n{error_msg}")
