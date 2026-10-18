import time

import pytest
from PySide6.QtCore import QObject, Signal, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from kde_shortcuts import ui
from kde_shortcuts.discovery import Discovery
from kde_shortcuts.model import Shortcut


class ControlledLoader(QObject):
    loaded = Signal(object)
    finished = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.running = False
        self.starts = 0
        self.interrupted = False

    def isRunning(self):
        return self.running

    def start(self):
        self.running = True
        self.starts += 1

    def requestInterruption(self):
        self.interrupted = True

    def deliver(self, result):
        self.running = False
        self.loaded.emit(result)
        self.finished.emit()


def rows():
    return [Shortcut("kwin", "a", "KWin", "Alpha", ("Meta+A", "Alt+A"), "Windows"),
            Shortcut("kwin", "b", "KWin", "Beta", ("Meta+B",), "Windows"),
            Shortcut("kmix", "c", "Volume", "Volume Up", ("Volume Up",), "Audio & Media")]


@pytest.fixture
def overlay(qapp, monkeypatch):
    monkeypatch.setattr(ui, "Loader", ControlledLoader)
    exits = []
    monkeypatch.setattr(ui.QGuiApplication, "quit", lambda: exits.append(True))
    window = ui.Overlay()
    window.exits = exits
    yield window
    window.hide()
    window.deleteLater()
    qapp.processEvents()


def test_render_search_and_keycaps(overlay):
    assert not overlay.refresh.isEnabled()
    overlay.loader.deliver(Discovery(rows()))
    assert overlay.refresh.isEnabled()
    assert overlay.tree.topLevelItemCount() == 2
    group = overlay.tree.topLevelItem(1)
    assert group.text(0) == "Windows" and group.childCount() == 2
    item = group.child(0)
    caps = overlay.tree.itemWidget(item, 1).findChildren(QLabel)
    assert [cap.text() for cap in caps] == ["Meta+A", "Alt+A"]
    assert "kwin / a" == item.toolTip(0)
    overlay.input.setText("META B")
    assert overlay.tree.topLevelItemCount() == 1
    assert "Beta" in overlay.tree.currentItem().text(0)
    overlay.input.setText("no such shortcut")
    assert overlay.tree.topLevelItemCount() == 0
    assert "No matching" in overlay.status.text()
    overlay.input.clear()
    assert "3 configured" in overlay.status.text()


def test_refresh_rereads_and_reports_errors(overlay):
    overlay.reload()  # A second refresh cannot start a concurrent worker.
    assert overlay.loader.starts == 1
    overlay.loader.deliver(Discovery(rows()))
    overlay.refresh.click()
    assert overlay.loader.starts == 2
    assert not overlay.refresh.isEnabled()
    overlay.loader.deliver(Discovery(errors=["Service missing", "Permission denied"]))
    assert overlay.tree.topLevelItemCount() == 0
    assert "Service missing" in overlay.status.text()
    assert "Permission denied" in overlay.status.toolTip()
    overlay.refresh.click()
    overlay.loader.deliver(Discovery(rows()[:1]))
    assert "Partial discovery" not in overlay.status.text()
    assert overlay.status.toolTip() == ""


def test_keyboard_navigation_and_escape(overlay, qapp):
    overlay.loader.deliver(Discovery(rows()[:2]))
    overlay.show()
    overlay.activateWindow()
    qapp.processEvents()
    overlay.input.setFocus()
    QTest.keyClick(overlay.input, Qt.Key.Key_Down)
    assert overlay.tree.hasFocus()
    assert "Beta" in overlay.tree.currentItem().text(0)
    overlay.input.setFocus()
    QTest.keyClick(overlay.input, Qt.Key.Key_Up)
    assert "Alpha" in overlay.tree.currentItem().text(0)
    QTest.keyClick(overlay.tree, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert overlay.input.hasFocus()
    QTest.keyClick(overlay.input, Qt.Key.Key_Escape)
    assert not overlay.isVisible()
    assert overlay.loader.interrupted and overlay.exits


def test_focus_loss_closes_only_visible_inactive_window(overlay, qapp, monkeypatch):
    overlay.loader.deliver(Discovery())
    overlay.show()
    qapp.processEvents()
    monkeypatch.setattr(overlay, "isActiveWindow", lambda: True)
    qapp.sendEvent(overlay, QEvent(QEvent.Type.ActivationChange))
    assert overlay.isVisible()
    monkeypatch.setattr(overlay, "isActiveWindow", lambda: False)
    qapp.sendEvent(overlay, QEvent(QEvent.Type.ActivationChange))
    assert not overlay.isVisible()
    before = len(overlay.exits)
    qapp.sendEvent(overlay, QEvent(QEvent.Type.ActivationChange))
    assert len(overlay.exits) == before


def test_close_during_discovery_waits_for_worker(overlay):
    overlay.close()
    assert overlay.loader.interrupted
    assert not overlay.exits
    overlay.loader.deliver(Discovery())
    assert len(overlay.exits) == 1


def test_primary_screen_fallback(overlay, qapp, monkeypatch):
    monkeypatch.setattr(ui.QGuiApplication, "screenAt", lambda point: None)
    overlay.show()
    qapp.processEvents()
    assert overlay.width() <= ui.WIDTH
    assert overlay.height() <= ui.HEIGHT


def test_real_worker_emits_discovery_and_stops(qapp, monkeypatch):
    async def discovery(**kwargs):
        assert not kwargs["cancelled"]()
        return Discovery(rows())
    monkeypatch.setattr(ui, "discover", discovery)
    loader = ui.Loader()
    received = []
    loader.loaded.connect(received.append)
    loader.start()
    deadline = time.monotonic() + 3
    while not received and time.monotonic() < deadline:
        QTest.qWait(10)
    assert loader.wait(1000)
    assert received[0].rows == rows()


def test_selection_shows_details_without_opening_editor(overlay, monkeypatch, qapp):
    calls = []
    monkeypatch.setattr(ui, "open_shortcut_settings", calls.append)
    overlay.loader.deliver(Discovery(rows()[:2]))
    overlay.show()
    overlay.activateWindow()
    qapp.processEvents()
    assert "Alpha" in overlay.detail_text.text()
    assert "Meta+A  or  Alt+A" in overlay.detail_text.text()
    QTest.keyClick(overlay.input, Qt.Key.Key_Down)
    assert overlay.selected_shortcut.action == "Beta"
    assert "Beta" in overlay.detail_text.text()
    first = overlay.tree.topLevelItem(0).child(0)
    QTest.mouseClick(overlay.tree.viewport(), Qt.MouseButton.LeftButton,
                     pos=overlay.tree.visualItemRect(first).center())
    assert overlay.selected_shortcut.action == "Alpha"
    assert not calls
    overlay.edit_button.click()
    assert calls == ["kwin"]
    overlay.input.setText("no matching action")
    assert overlay.selected_shortcut is None
    assert overlay.details.isHidden()
    overlay.edit_selected()
    assert calls == ["kwin"]


def test_edit_failure_is_visible_and_category_has_no_action(overlay, monkeypatch):
    overlay.loader.deliver(Discovery(rows()))
    def fail(component):
        raise OSError("Editor unavailable")
    monkeypatch.setattr(ui, "open_shortcut_settings", fail)
    overlay.edit_button.click()
    assert overlay.status.text() == "Editor unavailable"
    overlay.tree.setCurrentItem(overlay.tree.topLevelItem(0))
    assert overlay.selected_shortcut is None
    assert overlay.details.isHidden()
