from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLineEdit, QPushButton, QLabel,
    QScrollArea, QFrame, QMessageBox, QInputDialog,
    QComboBox, QDialog, QDialogButtonBox,
)
from PySide6.QtCore import Qt
from src.ui.theme import get_stylesheet, COLORS, NAV_ICONS
from src.services.inventory_service import InventoryService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mobile Shop Inventory Manager")
        self.setMinimumSize(1280, 750)
        self.setStyleSheet(get_stylesheet())

        self._nav_buttons: list[QPushButton] = []
        self._current_nav_index = 0
        self._pages: dict[int, QWidget] = {}
        self._page_factories: list[callable] = []
        self._brand_names: list[str] = []

        self.inventory_service = InventoryService()

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top bar ──
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        logo_label = QLabel("\u25C8")
        logo_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 24px; border: none; background: transparent;"
        )
        brand_layout.addWidget(logo_label)

        app_name = QLabel("Inventory Manager")
        app_name.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 17px; "
            f"font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent;"
        )
        brand_layout.addWidget(app_name)

        top_layout.addLayout(brand_layout)
        top_layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("   Search products, brands, models...")
        self.search_bar.setFixedWidth(420)
        self.search_bar.returnPressed.connect(self._on_search)
        top_layout.addWidget(self.search_bar)

        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # ── Body: sidebar + content ──
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar_container = QWidget()
        self._sidebar_container_layout = QVBoxLayout(self._sidebar_container)
        self._sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(self._sidebar_container)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("border: none;")
        body_layout.addWidget(self.stack, 1)

        main_layout.addWidget(body, 1)

        self._load_brands_and_build()

    def _load_brands_and_build(self):
        try:
            self._brand_names = self.inventory_service.get_brand_names()
        except Exception:
            self._brand_names = []

        self._build_sidebar()
        self._register_pages()

        if self._nav_buttons:
            self._on_nav_click(0)

    def _build_sidebar(self):
        for i in reversed(range(self._sidebar_container_layout.count())):
            w = self._sidebar_container_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._nav_buttons.clear()

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        scroll = QScrollArea()
        scroll.setObjectName("sidebar")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("sidebar")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(0)

        nav_items = [
            ("OVERVIEW", ["Dashboard"]),
            ("INVENTORY", ["Phones", "Glass Protectors"]),
            ("BRANDS", self._brand_names),
            ("MORE", ["Camera Lens", "Accessories", "Phone Cases", "Tablets"]),
            ("RECORDS", ["Transactions"]),
        ]

        for section_label, items in nav_items:
            label = QLabel(section_label)
            label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 10px; "
                f"font-weight: 700; padding: 16px 6px 6px 6px; border: none; "
                f"letter-spacing: 1.5px; background: transparent;"
            )
            layout.addWidget(label)

            if section_label == "BRANDS":
                mgmt_row = QHBoxLayout()
                mgmt_row.setContentsMargins(6, 2, 6, 4)
                mgmt_row.setSpacing(4)

                add_brand_btn = QPushButton("+ Add")
                add_brand_btn.setFixedHeight(24)
                add_brand_btn.setStyleSheet(
                    f"font-size: 10px; padding: 2px 8px; "
                    f"background: {COLORS['green_soft']}; color: {COLORS['green']}; "
                    f"border: 1px solid {COLORS['green']}40; border-radius: 4px;"
                )
                add_brand_btn.clicked.connect(self._on_add_brand)
                mgmt_row.addWidget(add_brand_btn)

                remove_brand_btn = QPushButton("- Remove")
                remove_brand_btn.setFixedHeight(24)
                remove_brand_btn.setStyleSheet(
                    f"font-size: 10px; padding: 2px 8px; "
                    f"background: {COLORS['red_soft']}; color: {COLORS['red']}; "
                    f"border: 1px solid {COLORS['red']}40; border-radius: 4px;"
                )
                remove_brand_btn.clicked.connect(self._on_remove_brand)
                mgmt_row.addWidget(remove_brand_btn)
                mgmt_row.addStretch()
                layout.addLayout(mgmt_row)

            for item_name in items:
                icon = NAV_ICONS.get(item_name, "\u2726")
                btn = QPushButton(f"  {icon}   {item_name}")
                btn.setCheckable(True)
                btn.setAutoExclusive(True)
                btn.setFixedHeight(36)
                idx = len(self._nav_buttons)
                btn.clicked.connect(lambda checked, i=idx: self._on_nav_click(i))
                layout.addWidget(btn)
                self._nav_buttons.append(btn)

        layout.addStretch()

        ver_label = QLabel("v1.0.0")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; "
            f"padding: 12px; border: none; background: transparent;"
        )
        layout.addWidget(ver_label)

        scroll.setWidget(content)

        wrapper_layout = QVBoxLayout(sidebar)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll)

        self._sidebar_container_layout.addWidget(sidebar)

    def _register_pages(self):
        """Register lazy page factories. Pages created on first navigation."""
        while self.stack.count() > 0:
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self._pages.clear()
        self._page_factories.clear()

        from src.ui.pages.dashboard_page import DashboardPage
        from src.ui.pages.phones_page import PhonesPage
        from src.ui.pages.glass_protectors_page import GlassProtectorsPage
        from src.ui.pages.branded_accessories_page import BrandedAccessoriesPage
        from src.ui.pages.lens_page import LensPage
        from src.ui.pages.accessories_page import AccessoriesPage
        from src.ui.pages.cases_page import CasesPage
        from src.ui.pages.tablets_page import TabletsPage
        from src.ui.pages.transactions_page import TransactionsPage
        from src.ui.pages.search_page import SearchPage

        factories = []
        factories.append(lambda: DashboardPage())
        factories.append(lambda: PhonesPage())
        factories.append(lambda: GlassProtectorsPage())
        for brand in self._brand_names:
            factories.append(lambda b=brand: BrandedAccessoriesPage(brand_name=b))
        factories.append(lambda: LensPage())
        factories.append(lambda: AccessoriesPage())
        factories.append(lambda: CasesPage())
        factories.append(lambda: TabletsPage())
        factories.append(lambda: TransactionsPage())

        self._page_factories = factories

        for _ in factories:
            self.stack.addWidget(QWidget())

        self.search_page = SearchPage()
        self.stack.addWidget(self.search_page)

    def _get_or_create_page(self, index: int) -> QWidget:
        if index in self._pages:
            return self._pages[index]
        if index < 0 or index >= len(self._page_factories):
            return self.stack.widget(index)

        try:
            page = self._page_factories[index]()
            old = self.stack.widget(index)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.stack.insertWidget(index, page)
            self._pages[index] = page
            return page
        except Exception as e:
            QMessageBox.critical(
                self, "Connection Error",
                f"Failed to load page:\n\n{str(e)}\n\n"
                "Please check your .env file and internet connection."
            )
            return self.stack.widget(index)

    def _on_nav_click(self, index: int):
        if 0 <= index < len(self._page_factories):
            page = self._get_or_create_page(index)
            self.stack.setCurrentIndex(index)
            self._current_nav_index = index
            if hasattr(page, "refresh_data"):
                page.refresh_data()

    def _on_search(self):
        query = self.search_bar.text().strip()
        if query:
            for btn in self._nav_buttons:
                btn.setChecked(False)
            search_idx = self.stack.indexOf(self.search_page)
            self.stack.setCurrentIndex(search_idx)
            self.search_page.do_search(query)

    # ── Brand Management ─────────────────────────────────────

    def _on_add_brand(self):
        name, ok = QInputDialog.getText(self, "Add Brand", "Enter brand name:")
        if ok and name.strip():
            name = name.strip()
            if name in self._brand_names:
                QMessageBox.information(self, "Info", f"Brand '{name}' already exists.")
                return
            try:
                self.inventory_service.add_brand(name)
                self._rebuild_after_brand_change()
                QMessageBox.information(self, "Success", f"Brand '{name}' added successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add brand:\n{e}")

    def _on_remove_brand(self):
        if not self._brand_names:
            QMessageBox.information(self, "Info", "No brands to remove.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Remove Brand")
        dialog.setFixedWidth(300)
        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(QLabel("Select brand to remove:"))
        combo = QComboBox()
        combo.addItems(self._brand_names)
        dlg_layout.addWidget(combo)
        warn = QLabel("Warning: This will remove the brand and all its product types.")
        warn.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px;")
        warn.setWordWrap(True)
        dlg_layout.addWidget(warn)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlg_layout.addWidget(buttons)

        if dialog.exec():
            brand = combo.currentText()
            reply = QMessageBox.question(
                self, "Confirm",
                f"Are you sure you want to remove brand '{brand}'?\n\n"
                "This will delete all product types under this brand.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.inventory_service.remove_brand(brand)
                    self._rebuild_after_brand_change()
                    QMessageBox.information(self, "Success", f"Brand '{brand}' removed.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to remove brand:\n{e}")

    def _rebuild_after_brand_change(self):
        self.inventory_service.invalidate_caches()
        self._brand_names = self.inventory_service.get_brand_names()
        self._build_sidebar()
        self._register_pages()
        if self._nav_buttons:
            self._on_nav_click(0)
