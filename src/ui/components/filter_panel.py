from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton,
)
from PySide6.QtCore import Signal
from src.models.category import Subcategory, ProductType


class FilterPanel(QWidget):
    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Filter:"))

        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setMinimumWidth(150)
        self.subcategory_combo.addItem("All Subcategories", "")
        self.subcategory_combo.currentIndexChanged.connect(lambda: self.filter_changed.emit())
        layout.addWidget(self.subcategory_combo)

        self.product_type_combo = QComboBox()
        self.product_type_combo.setMinimumWidth(150)
        self.product_type_combo.addItem("All Types", "")
        self.product_type_combo.currentIndexChanged.connect(lambda: self.filter_changed.emit())
        layout.addWidget(self.product_type_combo)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(120)
        self.status_combo.addItems(["All Status", "In Stock", "Sold", "Claimed"])
        self.status_combo.currentIndexChanged.connect(lambda: self.filter_changed.emit())
        layout.addWidget(self.status_combo)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def set_subcategories(self, subcategories: list[Subcategory]):
        self.subcategory_combo.blockSignals(True)
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem("All Subcategories", "")
        for sub in subcategories:
            self.subcategory_combo.addItem(sub.name, sub.id)
        self.subcategory_combo.blockSignals(False)

    def set_product_types(self, product_types: list[ProductType]):
        self.product_type_combo.blockSignals(True)
        self.product_type_combo.clear()
        self.product_type_combo.addItem("All Types", "")
        for pt in product_types:
            self.product_type_combo.addItem(pt.name, pt.id)
        self.product_type_combo.blockSignals(False)

    def get_selected_subcategory_id(self) -> str:
        return self.subcategory_combo.currentData() or ""

    def get_selected_product_type_id(self) -> str:
        return self.product_type_combo.currentData() or ""

    def get_selected_status(self) -> str:
        status_map = {"All Status": "", "In Stock": "in_stock", "Sold": "sold", "Claimed": "claimed"}
        return status_map.get(self.status_combo.currentText(), "")

    def _reset(self):
        self.subcategory_combo.setCurrentIndex(0)
        self.product_type_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.filter_changed.emit()
