from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QComboBox, QFrame,
)
from PySide6.QtCore import Qt
from src.services.inventory_service import InventoryService
from src.ui.components.product_table import ProductTable
from src.ui.components.dynamic_form import DynamicFormDialog
from src.ui.components.transaction_dialog import TransactionDialog
from src.ui.components.return_dialog import ReturnDialog
from src.ui.components.claim_dialog import ClaimDialog
from src.ui.components.claim_resolve_dialog import ClaimResolveDialog
from src.ui.components.loading_overlay import LoadingOverlay, run_async
from src.ui.theme import COLORS


class PhonesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.inventory_service = InventoryService()
        self.category = self.inventory_service.get_category_by_name("Phones")
        self.category_id = self.category.id if self.category else ""

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Phones")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};"
        )
        layout.addWidget(title)

        # ── Stat cards ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.card_box_pack = self._create_stat_card(
            "Box Pack Phones", "0", COLORS["green"], COLORS["green_soft"], "\u2709"
        )
        self.card_used = self._create_stat_card(
            "Used Phones", "0", COLORS["accent"], COLORS["accent_soft"], "\u260E"
        )
        self.card_keypad = self._create_stat_card(
            "Keypad Phones", "0", COLORS["yellow"], COLORS["yellow_soft"], "\u2328"
        )
        stats_row.addWidget(self.card_box_pack)
        stats_row.addWidget(self.card_used)
        stats_row.addWidget(self.card_keypad)
        layout.addLayout(stats_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Subcategories")
        self.filter_combo.addItems(["Used Phones", "Box Pack Phones", "Keypad Phones"])
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        add_btn = QPushButton("Add New")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._on_add)
        filter_row.addWidget(add_btn)

        layout.addLayout(filter_row)

        self.table = ProductTable(
            columns=["Brand", "Model", "Variant", "Color", "IMEI 1", "RAM", "Storage",
                     "Qty", "Sale Price", "Status", "Actions"]
        )
        self.table.view_requested.connect(self._on_view)
        self.table.edit_requested.connect(self._on_edit)
        self.table.delete_requested.connect(self._on_delete)
        self.table.buy_requested.connect(self._on_buy)
        self.table.sell_requested.connect(self._on_sell)
        self.table.return_requested.connect(self._on_return)
        self.table.claim_requested.connect(self._on_claim)
        self.table.resolve_claim_requested.connect(self._on_resolve_claim)
        layout.addWidget(self.table)

        self._loading = LoadingOverlay(self)

    def refresh_data(self):
        selected = self.filter_combo.currentText()

        def fetch():
            # Cached hierarchy lookups — no DB cost after first call
            subcategories = self.inventory_service.get_subcategories(self.category_id)
            sub_by_name = {s.name: s for s in subcategories}
            sub_id_to_name = {s.id: s.name for s in subcategories}
            pt_list = self.inventory_service.repo.get_all_product_types()
            pt_to_sub = {pt.id: pt.subcategory_id for pt in pt_list}

            # ONE query to fetch every phone in the category.
            # Stats and filter view are both derived from this single result —
            # saves 3 extra queries per page refresh.
            all_products = self.inventory_service.get_products_by_category(self.category_id)

            # In-memory stats grouping
            stats = {"Used Phones": 0, "Box Pack Phones": 0, "Keypad Phones": 0}
            for p in all_products:
                if p.status != "in_stock":
                    continue
                sub_id = pt_to_sub.get(p.product_type_id)
                sub_name = sub_id_to_name.get(sub_id) if sub_id else None
                if sub_name in stats:
                    stats[sub_name] += 1

            # In-memory filter for the table
            if selected == "All Subcategories":
                products = all_products
            else:
                sub = sub_by_name.get(selected)
                sub_id = sub.id if sub else None
                products = [
                    p for p in all_products
                    if pt_to_sub.get(p.product_type_id) == sub_id
                ] if sub_id else []

            # Enrich with phone details — still one batch query, unavoidable
            if products:
                product_ids = [p.id for p in products]
                details_map = self.inventory_service.get_phone_details_batch(product_ids)
                for p in products:
                    pd = details_map.get(p.id)
                    if pd:
                        p.attributes["imei_1"] = pd.imei1
                        p.attributes["ram"] = f"{pd.ram_gb} GB" if pd.ram_gb else ""
                        p.attributes["storage"] = f"{pd.storage_gb} GB" if pd.storage_gb else ""
                        p.attributes["color"] = pd.color
                        p.attributes["variant"] = getattr(pd, "region_variant", "")
            return {"products": products, "stats": stats}

        run_async(self, fetch, self._on_data_loaded,
                  message="Loading phones...")

    def _on_data_loaded(self, data):
        stats = data["stats"]
        self.card_box_pack._value_label.setText(str(stats["Box Pack Phones"]))
        self.card_used._value_label.setText(str(stats["Used Phones"]))
        self.card_keypad._value_label.setText(str(stats["Keypad Phones"]))
        self.table.load_products(data["products"])

    def _on_add(self):
        try:
            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open form:\n{e}")

    def _on_edit(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            phone_details = self.inventory_service.get_phone_details(product_id)

            dialog = DynamicFormDialog(
                inventory_service=self.inventory_service,
                category_id=self.category_id,
                product=product,
                phone_details=phone_details,
                parent=self,
            )
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit product:\n{e}")

    def _on_delete(self, product_id: str):
        try:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this product?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.inventory_service.delete_product(product_id)
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete product:\n{e}")

    def _on_buy(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = TransactionDialog(product, "purchase", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record purchase:\n{e}")

    def _on_sell(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return

            dialog = TransactionDialog(product, "sale", parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record sale:\n{e}")

    def _on_return(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            dialog = ReturnDialog(product, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record return:\n{e}")

    def _on_claim(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            phone_details = self.inventory_service.get_phone_details(product_id)
            dialog = ClaimDialog(product, phone_details, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit claim:\n{e}")

    def _on_resolve_claim(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            phone_details = self.inventory_service.get_phone_details(product_id)
            dialog = ClaimResolveDialog(product, phone_details, parent=self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to resolve claim:\n{e}")

    def _on_view(self, product_id: str):
        try:
            product = self.table.get_cached_product(product_id) or self.inventory_service.get_product_by_id(product_id)
            if not product: return
            phone_details = self.inventory_service.get_phone_details(product_id)
            from src.ui.components.product_info_dialog import ProductInfoDialog
            dialog = ProductInfoDialog(product, phone_details, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product info:\n{e}")

    def _create_stat_card(self, label: str, value: str, color: str, bg_tint: str, icon: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['bg_card']}; "
            f"border-radius: 12px; border: 1px solid {COLORS['border']}; }}"
        )
        card.setFixedHeight(95)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        icon_badge = QLabel(icon)
        icon_badge.setFixedSize(30, 30)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(
            f"background-color: {bg_tint}; color: {color}; "
            f"border-radius: 8px; font-size: 14px; border: none;"
        )
        top_row.addWidget(icon_badge)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px; "
            f"font-weight: 600; border: none; background: transparent;"
        )
        top_row.addWidget(label_widget)
        top_row.addStretch()
        layout.addLayout(top_row)
        layout.addStretch()

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: 800; "
            f"border: none; background: transparent; letter-spacing: -0.5px;"
        )
        layout.addWidget(value_label)

        card._value_label = value_label
        return card
