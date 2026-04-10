from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout, QWidget, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from src.models.product import Product
from src.utils.helpers import format_price
from src.ui.theme import COLORS


class ProductTable(QTableWidget):
    view_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    buy_requested = Signal(str)
    sell_requested = Signal(str)
    return_requested = Signal(str)
    claim_requested = Signal(str)
    resolve_claim_requested = Signal(str)

    DEFAULT_COLUMNS = ["Brand", "Model", "Qty", "Purchase Price", "Sale Price", "Status", "Actions"]

    def __init__(self, columns: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.columns = columns or self.DEFAULT_COLUMNS
        self._products: list[Product] = []

        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.verticalHeader().setDefaultSectionSize(48)

        header = self.horizontalHeader()
        actions_col = len(self.columns) - 1
        for i in range(actions_col):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(actions_col, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(actions_col, 340)
        
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
    def _on_cell_double_clicked(self, row: int, col: int):
        product = self.get_product_at_row(row)
        if product:
            self.view_requested.emit(product.id)

    def load_products(self, products: list[Product]):
        # Sort: in_stock first, then claimed, then sold (bottom)
        # Preserves the original order within each group via stable sort.
        status_order = {"in_stock": 0, "claimed": 1, "sold": 2}
        products = sorted(products, key=lambda p: status_order.get(p.status, 99))

        self._products = products
        self.setSortingEnabled(False)
        self.setRowCount(len(products))

        for row, product in enumerate(products):
            col = 0
            for header_name in self.columns:
                if header_name == "Brand":
                    self.setItem(row, col, QTableWidgetItem(product.brand))
                elif header_name == "Model":
                    self.setItem(row, col, QTableWidgetItem(product.model))
                elif header_name == "Qty":
                    item = QTableWidgetItem()
                    item.setData(Qt.ItemDataRole.DisplayRole, product.quantity)
                    if product.quantity <= 3 and product.quantity > 0:
                        item.setForeground(QColor(COLORS["yellow"]))
                    elif product.quantity == 0:
                        item.setForeground(QColor(COLORS["red"]))
                    else:
                        item.setForeground(QColor(COLORS["text_primary"]))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(row, col, item)
                elif header_name == "Purchase Price":
                    item = QTableWidgetItem(format_price(product.purchase_price))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.setItem(row, col, item)
                elif header_name == "Sale Price":
                    item = QTableWidgetItem(format_price(product.sale_price))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    item.setForeground(QColor(COLORS["green"]))
                    self.setItem(row, col, item)
                elif header_name == "Status":
                    status_text = product.status.replace("_", " ").upper()
                    item = QTableWidgetItem(status_text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if product.status == "in_stock":
                        item.setForeground(QColor(COLORS["green"]))
                    elif product.status == "sold":
                        item.setForeground(QColor(COLORS["red"]))
                    elif product.status == "claimed":
                        item.setForeground(QColor(COLORS["yellow"]))
                    self.setItem(row, col, item)
                elif header_name == "Actions":
                    self._add_action_buttons(row, col, product)
                else:
                    attr_val = product.attributes.get(header_name.lower().replace(" ", "_"), "")
                    self.setItem(row, col, QTableWidgetItem(str(attr_val)))
                col += 1

        self.setSortingEnabled(True)

    def _add_action_buttons(self, row: int, col: int, product: Product):
        widget = QWidget()
        widget.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(5)

        product_id = product.id

        # Edit -- always shown
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("tblEdit")
        edit_btn.setFixedSize(55, 30)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(product_id))
        layout.addWidget(edit_btn)

        if product.status == "in_stock":
            # Sell
            sell_btn = QPushButton("Sell")
            sell_btn.setObjectName("tblSell")
            sell_btn.setFixedSize(50, 30)
            sell_btn.clicked.connect(lambda: self.sell_requested.emit(product_id))
            layout.addWidget(sell_btn)

        elif product.status == "sold":
            # Return
            return_btn = QPushButton("Return")
            return_btn.setObjectName("tblReturn")
            return_btn.setFixedSize(65, 30)
            return_btn.clicked.connect(lambda: self.return_requested.emit(product_id))
            layout.addWidget(return_btn)
            # Claim
            claim_btn = QPushButton("Claim")
            claim_btn.setObjectName("tblClaim")
            claim_btn.setFixedSize(60, 30)
            claim_btn.clicked.connect(lambda: self.claim_requested.emit(product_id))
            layout.addWidget(claim_btn)
            # Stock In (manual restock)
            buy_btn = QPushButton("Stock In")
            buy_btn.setObjectName("tblStockIn")
            buy_btn.setFixedSize(70, 30)
            buy_btn.clicked.connect(lambda: self.buy_requested.emit(product_id))
            layout.addWidget(buy_btn)

        elif product.status == "claimed":
            # Resolve
            resolve_btn = QPushButton("Resolve")
            resolve_btn.setObjectName("tblResolve")
            resolve_btn.setFixedSize(70, 30)
            resolve_btn.clicked.connect(lambda: self.resolve_claim_requested.emit(product_id))
            layout.addWidget(resolve_btn)

        # Delete -- always shown
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("tblDelete")
        del_btn.setFixedSize(60, 30)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(product_id))
        layout.addWidget(del_btn)

        self.setCellWidget(row, col, widget)

    def get_product_at_row(self, row: int) -> Product | None:
        if 0 <= row < len(self._products):
            return self._products[row]
        return None
