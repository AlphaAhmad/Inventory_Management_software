from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import date
from src.services.inventory_service import InventoryService
from src.services.transaction_service import TransactionService
from src.utils.helpers import format_price
from src.ui.components.loading_overlay import LoadingOverlay, run_async
from src.ui.theme import COLORS


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_service = InventoryService()
        self.transaction_service = TransactionService()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(0)

        # ── Header ──
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet(
            f"font-size: 26px; font-weight: 800; color: {COLORS['text_primary']}; "
            f"letter-spacing: -0.5px;"
        )
        header_layout.addWidget(title)

        subtitle = QLabel("Overview of your inventory")
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {COLORS['text_muted']}; padding-top: 8px;"
        )
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(24)

        # ── Row 1: Main Stat Cards ──
        cards_row1 = QHBoxLayout()
        cards_row1.setSpacing(16)

        self.card_total = self._create_stat_card(
            "Total Products", "0", COLORS["accent"], COLORS["accent_soft"], "\u2630"
        )
        self.card_value = self._create_stat_card(
            "Stock Value", "Rs. 0", COLORS["green"], COLORS["green_soft"], "\u2191"
        )

        cards_row1.addWidget(self.card_total)
        cards_row1.addWidget(self.card_value)

        main_layout.addLayout(cards_row1)
        main_layout.addSpacing(16)

        # ── Row 2: Today's Stats ──
        cards_row2 = QHBoxLayout()
        cards_row2.setSpacing(16)

        self.card_today_sales = self._create_today_card(
            "Today's Sales", "Rs. 0", "0 transactions",
            COLORS["green"], COLORS["green_soft"], "\u2197"
        )
        self.card_today_purchases = self._create_today_card(
            "Today's Purchases", "Rs. 0", "0 transactions",
            COLORS["peach"], "#ffab7622", "\u2196"
        )
        self.card_monthly_profit = self._create_profit_card()

        cards_row2.addWidget(self.card_today_sales)
        cards_row2.addWidget(self.card_today_purchases)
        cards_row2.addWidget(self.card_monthly_profit)

        main_layout.addLayout(cards_row2)
        main_layout.addSpacing(28)

        # ── Recent Activity Header ──
        activity_header = QHBoxLayout()
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']};"
        )
        activity_header.addWidget(activity_title)

        self.activity_count_label = QLabel("Last 10 transactions")
        self.activity_count_label.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_muted']}; padding-top: 4px;"
        )
        activity_header.addWidget(self.activity_count_label)
        activity_header.addStretch()
        main_layout.addLayout(activity_header)
        main_layout.addSpacing(12)

        # ── Transactions Table ──
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels(
            ["Date", "Product", "Type", "Qty", "Amount"]
        )
        self.transactions_table.setAlternatingRowColors(True)
        self.transactions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.transactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.setShowGrid(False)

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.transactions_table.verticalHeader().setDefaultSectionSize(42)
        main_layout.addWidget(self.transactions_table, 1)

        # ── Empty state ──
        self.empty_label = QLabel("No recent transactions yet.\nStart adding products and recording sales!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14px; padding: 60px;"
        )
        self.empty_label.setVisible(False)
        main_layout.addWidget(self.empty_label)

        # ── Error state ──
        self.error_label = QLabel("Unable to connect to database.\nCheck your internet and .env settings.")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet(
            f"color: {COLORS['red']}; font-size: 14px; padding: 60px;"
        )
        self.error_label.setVisible(False)
        main_layout.addWidget(self.error_label)

        # ── Loading Overlay ──
        self._loading = LoadingOverlay(self)

    def _create_stat_card(
        self, label: str, value: str, color: str, bg_tint: str, icon: str
    ) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['bg_card']}; "
            f"border-radius: 12px; border: 1px solid {COLORS['border']}; }}"
        )
        card.setFixedHeight(110)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        icon_badge = QLabel(icon)
        icon_badge.setFixedSize(32, 32)
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
            f"color: {color}; font-size: 26px; font-weight: 800; "
            f"border: none; background: transparent; letter-spacing: -0.5px;"
        )
        layout.addWidget(value_label)

        card._value_label = value_label
        return card

    def _create_today_card(
        self, label: str, value: str, sub_text: str,
        color: str, bg_tint: str, icon: str
    ) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['bg_card']}; "
            f"border-radius: 12px; border: 1px solid {COLORS['border']}; }}"
        )
        card.setFixedHeight(100)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Left: icon badge
        icon_badge = QLabel(icon)
        icon_badge.setFixedSize(48, 48)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(
            f"background-color: {bg_tint}; color: {color}; "
            f"border-radius: 12px; font-size: 22px; border: none;"
        )
        layout.addWidget(icon_badge)

        # Right: text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px; "
            f"font-weight: 600; border: none; background: transparent;"
        )
        text_layout.addWidget(label_widget)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 800; "
            f"border: none; background: transparent; letter-spacing: -0.5px;"
        )
        text_layout.addWidget(value_label)

        sub_label = QLabel(sub_text)
        sub_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; "
            f"border: none; background: transparent;"
        )
        text_layout.addWidget(sub_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        card._value_label = value_label
        card._sub_label = sub_label
        return card

    def _create_profit_card(self) -> QFrame:
        """Profit card with a month dropdown in the header."""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['bg_card']}; "
            f"border-radius: 12px; border: 1px solid {COLORS['border']}; }}"
        )
        card.setFixedHeight(100)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Left: icon badge
        icon_badge = QLabel("\u2605")
        icon_badge.setFixedSize(48, 48)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(
            f"background-color: {COLORS['accent_soft']}; color: {COLORS['accent']}; "
            f"border-radius: 12px; font-size: 22px; border: none;"
        )
        layout.addWidget(icon_badge)

        # Middle: value
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        label_widget = QLabel("Monthly Profit")
        label_widget.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px; "
            f"font-weight: 600; border: none; background: transparent;"
        )
        text_layout.addWidget(label_widget)

        value_label = QLabel("Rs. 0")
        value_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 22px; font-weight: 800; "
            f"border: none; background: transparent; letter-spacing: -0.5px;"
        )
        text_layout.addWidget(value_label)

        sub_label = QLabel("This month")
        sub_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; "
            f"border: none; background: transparent;"
        )
        text_layout.addWidget(sub_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Right: month dropdown
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(140)
        self.month_combo.setStyleSheet(
            f"QComboBox {{ font-size: 12px; padding: 4px 8px; "
            f"border-radius: 6px; min-height: 28px; }}"
        )
        today = date.today()
        for i in range(5):
            # Go back i months
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            label = date(y, m, 1).strftime("%B %Y")
            self.month_combo.addItem(label, (y, m))
        self.month_combo.currentIndexChanged.connect(self._on_profit_month_changed)
        layout.addWidget(self.month_combo, alignment=Qt.AlignmentFlag.AlignVCenter)

        card._value_label = value_label
        card._sub_label = sub_label
        return card

    def _on_profit_month_changed(self, index: int):
        """Fetch profit for the selected month in the background."""
        data = self.month_combo.currentData()
        if not data:
            return
        year, month = data

        from src.ui.components.loading_overlay import run_async

        def fetch_month():
            return self.inventory_service.get_profit_for_month(year, month)

        def on_result(result):
            self._update_profit_card(result)

        run_async(self, fetch_month, on_result, message="Loading profit...")

    def _update_profit_card(self, profit_data: dict):
        profit = profit_data.get("profit", 0) or 0
        revenue = profit_data.get("revenue", 0) or 0
        cogs = profit_data.get("cogs", 0) or 0
        returns = profit_data.get("returns", 0) or 0
        month_label = profit_data.get("month_label", "")

        profit_color = COLORS['green'] if profit >= 0 else COLORS['red']
        self.card_monthly_profit._value_label.setText(format_price(profit))
        self.card_monthly_profit._value_label.setStyleSheet(
            f"color: {profit_color}; font-size: 22px; font-weight: 800; "
            f"border: none; background: transparent; letter-spacing: -0.5px;"
        )
        self.card_monthly_profit._sub_label.setText(
            f"Rev {format_price(revenue)}"
        )
        self.card_monthly_profit.setToolTip(
            f"Profit Breakdown ({month_label})\n"
            f"Revenue:  {format_price(revenue)}\n"
            f"COGS:    -{format_price(cogs)}\n"
            f"Returns: -{format_price(returns)}\n"
            f"{'─' * 24}\n"
            f"Profit:   {format_price(profit)}"
        )

    # ── Data ──

    def refresh_data(self):
        self.error_label.setVisible(False)

        def fetch():
            stats = self.inventory_service.get_dashboard_stats()
            recent = self.transaction_service.get_recent_transactions(limit=10)
            name_map = self.transaction_service.get_product_name_map() if recent else {}
            return {"stats": stats, "recent": recent, "name_map": name_map}

        run_async(self, fetch, self._update_dashboard,
                  on_error=self._on_load_error,
                  message="Loading dashboard...")

    def _update_dashboard(self, data):
        stats = data["stats"]
        recent = data["recent"]
        name_map = data["name_map"]

        # Update stat cards
        self.card_total._value_label.setText(f"{stats['total_count']:,}")
        self.card_value._value_label.setText(format_price(stats['total_value']))

        # Update today cards
        self.card_today_sales._value_label.setText(
            format_price(stats.get('today_sales_amount', 0))
        )
        self.card_today_sales._sub_label.setText(
            f"{stats.get('today_sales_count', 0)} transaction(s)"
        )
        self.card_today_purchases._value_label.setText(
            format_price(stats.get('today_purchases_amount', 0))
        )
        self.card_today_purchases._sub_label.setText(
            f"{stats.get('today_purchases_count', 0)} transaction(s)"
        )

        # Monthly profit — reuse the shared updater method
        self._update_profit_card({
            "profit": stats.get("monthly_profit", 0),
            "revenue": stats.get("monthly_revenue", 0),
            "cogs": stats.get("monthly_cogs", 0),
            "returns": stats.get("monthly_returns", 0),
            "month_label": stats.get("month_label", "This month"),
        })
        # Reset dropdown to current month (index 0) without re-fetching
        self.month_combo.blockSignals(True)
        self.month_combo.setCurrentIndex(0)
        self.month_combo.blockSignals(False)

        # Update transactions table
        if not recent:
            self.transactions_table.setVisible(False)
            self.empty_label.setVisible(True)
            self.activity_count_label.setText("No transactions yet")
            return

        self.transactions_table.setVisible(True)
        self.empty_label.setVisible(False)
        self.activity_count_label.setText(f"Last {len(recent)} transaction(s)")
        self.transactions_table.setRowCount(len(recent))

        for row, txn in enumerate(recent):
            date_str = txn.created_at[:10] if txn.created_at else ""
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_table.setItem(row, 0, date_item)

            name = name_map.get(txn.product_id, "Unknown")
            self.transactions_table.setItem(row, 1, QTableWidgetItem(name))

            type_text = txn.type.replace("_", " ").upper()
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_color_map = {
                "sale": COLORS["green"],
                "purchase": COLORS["accent"],
                "return": COLORS["yellow"],
                "claim": COLORS["purple"],
                "claim_resolved": COLORS["cyan"],
            }
            type_item.setForeground(QColor(type_color_map.get(txn.type, COLORS["text_primary"])))
            self.transactions_table.setItem(row, 2, type_item)

            qty_item = QTableWidgetItem(str(txn.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_table.setItem(row, 3, qty_item)

            price_item = QTableWidgetItem(format_price(txn.total_price))
            price_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.transactions_table.setItem(row, 4, price_item)

    def _on_load_error(self, error_msg: str):
        self.error_label.setVisible(True)
        self.transactions_table.setVisible(False)
        self.empty_label.setVisible(False)
