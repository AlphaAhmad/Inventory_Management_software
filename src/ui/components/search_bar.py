from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal


class SearchBar(QLineEdit):
    search_triggered = Signal(str)

    def __init__(self, placeholder="Search all products...", parent=None):
        super().__init__(parent)
        self.setObjectName("searchBar")
        self.setPlaceholderText(placeholder)
        self.returnPressed.connect(self._on_return)

    def _on_return(self):
        text = self.text().strip()
        if text:
            self.search_triggered.emit(text)
