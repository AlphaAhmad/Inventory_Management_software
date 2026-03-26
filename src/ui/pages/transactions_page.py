from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.services.inventory_service import InventoryService
from src.services.transaction_service import TransactionService
from src.utils.helpers import format_price
from src.ui.components.loading_overlay import LoadingOverlay, run_async
from src.ui.theme import COLORS


class TransactionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.inventory_service = InventoryService()
        self.transaction_service = TransactionService()

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Transaction History")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};"
        )
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Purchase", "Sale", "Return", "Claim", "Claim Resolved"])
        self.filter_combo.currentIndexChanged.connect(lambda: self.refresh_data())
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Product", "Type", "Qty", "Unit Price", "Total", "Customer"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        self._loading = LoadingOverlay(self)

    def refresh_data(self):
        selected_filter = self.filter_combo.currentText()

        def fetch():
            transactions = self.transaction_service.get_all_transactions()
            filter_map = {
                "Purchase": "purchase", "Sale": "sale", "Return": "return",
                "Claim": "claim", "Claim Resolved": "claim_resolved",
            }
            if selected_filter in filter_map:
                target = filter_map[selected_filter]
                transactions = [t for t in transactions if t.type == target]
            transactions.sort(key=lambda t: t.created_at, reverse=True)
            name_map = self.transaction_service.get_product_name_map()
            return (transactions, name_map)

        run_async(self, fetch, self._populate_table,
                  message="Loading transactions...")

    def _populate_table(self, result):
        transactions, name_map = result

        type_colors = {
            "purchase": QColor(COLORS["green"]),
            "sale": QColor(COLORS["peach"]),
            "return": QColor(COLORS["yellow"]),
            "claim": QColor(COLORS["purple"]),
            "claim_resolved": QColor(COLORS["cyan"]),
        }

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(transactions))

        for row, txn in enumerate(transactions):
            row_color = type_colors.get(txn.type, QColor(COLORS["text_primary"]))

            date_str = txn.created_at[:10] if txn.created_at else ""
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setForeground(row_color)
            self.table.setItem(row, 0, date_item)

            product_name = name_map.get(txn.product_id, "Unknown")
            product_item = QTableWidgetItem(product_name)
            product_item.setForeground(row_color)
            self.table.setItem(row, 1, product_item)

            type_text = txn.type.replace("_", " ").title()
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setForeground(row_color)
            self.table.setItem(row, 2, type_item)

            qty_item = QTableWidgetItem()
            qty_item.setData(Qt.ItemDataRole.DisplayRole, txn.quantity)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_item.setForeground(row_color)
            self.table.setItem(row, 3, qty_item)

            unit_price_item = QTableWidgetItem(format_price(txn.unit_price))
            unit_price_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            unit_price_item.setForeground(row_color)
            self.table.setItem(row, 4, unit_price_item)

            total_item = QTableWidgetItem(format_price(txn.total_price))
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            total_item.setForeground(row_color)
            self.table.setItem(row, 5, total_item)

            customer_item = QTableWidgetItem(txn.customer_info or "")
            customer_item.setForeground(row_color)
            self.table.setItem(row, 6, customer_item)

        self.table.setSortingEnabled(True)
