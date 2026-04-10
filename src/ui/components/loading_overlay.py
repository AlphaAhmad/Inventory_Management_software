from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect, QEvent
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from src.ui.theme import COLORS


class WorkerThread(QThread):
    """Runs a callable in a background thread and emits result or error."""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with spinning animation."""

    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self._message = message
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setVisible(False)
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Type.Resize:
            self.resize(self.parent().size())
        return False

    def show_overlay(self, message: str = None):
        if message:
            self._message = message
        if self.parent():
            self.resize(self.parent().size())
            self.raise_()
        self.setVisible(True)
        self._timer.start(30)

    def hide_overlay(self):
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent background
        painter.fillRect(self.rect(), QColor(15, 15, 23, 160))

        center = self.rect().center()

        # Track circle
        track_pen = QPen(QColor(COLORS['border']), 3)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        arc_rect = QRect(center.x() - 22, center.y() - 32, 44, 44)
        painter.drawEllipse(arc_rect)

        # Spinning arc
        pen = QPen(QColor(COLORS['accent']), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(arc_rect, self._angle * 16, 270 * 16)

        # Loading text
        font = painter.font()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text_secondary']))
        text_rect = QRect(center.x() - 100, center.y() + 22, 200, 30)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._message)

        painter.end()


def run_async(parent, fn, on_success, on_error=None, message="Loading..."):
    """Helper to run a function asynchronously with a loading overlay.

    Args:
        parent: The parent widget (must have ._loading attribute)
        fn: The callable to run in background (no Qt widget access!)
        on_success: Callback(result) on main thread
        on_error: Optional callback(error_msg) on main thread
        message: Loading overlay message
    """
    overlay = getattr(parent, '_loading', None)
    if overlay:
        overlay.show_overlay(message)

    worker = WorkerThread(fn)

    # Keep a list of active workers on the parent so multiple concurrent
    # async calls don't overwrite each other and trigger GC mid-run.
    if not hasattr(parent, '_active_workers'):
        parent._active_workers = []
    parent._active_workers.append(worker)

    def _cleanup():
        try:
            parent._active_workers.remove(worker)
        except (ValueError, AttributeError):
            pass
        worker.deleteLater()

    def _on_done(result):
        if overlay:
            overlay.hide_overlay()
        try:
            on_success(result)
        finally:
            _cleanup()

    def _on_err(error_msg):
        if overlay:
            overlay.hide_overlay()
        try:
            if on_error:
                on_error(error_msg)
            else:
                QMessageBox.critical(parent, "Error", error_msg)
        finally:
            _cleanup()

    worker.finished.connect(_on_done)
    worker.error.connect(_on_err)
    worker.start()
