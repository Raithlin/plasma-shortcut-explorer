"""Run with QT_QPA_PLATFORM=offscreen; no real session bus needed."""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from kde_shortcuts.ui import Overlay
from kde_shortcuts.discovery import Discovery
from kde_shortcuts.model import Shortcut

app = QApplication([])
completed = False
app.setQuitOnLastWindowClosed(False)
window = Overlay()


def check():
    global completed
    if window.loader.isRunning():
        QTimer.singleShot(50, check)
        return
    window.loaded(Discovery([Shortcut("test", "search", "Example", "Test action", ("Meta+K",), "Applications")]))
    assert window.tree.topLevelItemCount() == 1
    assert window.tree.topLevelItem(0).childCount() == 1
    window.input.setText("no match")
    assert window.tree.topLevelItemCount() == 0
    window.input.clear()
    window.grab().save("/tmp/kde-shortcuts-smoke.png")
    window.loaded(Discovery(errors=["Service unavailable"]))
    assert "Service unavailable" in window.status.text()
    completed = True
    window.close()

window.show()
QTimer.singleShot(50, check)
QTimer.singleShot(15000, app.quit)
app.exec()
assert completed, "UI smoke check timed out"
