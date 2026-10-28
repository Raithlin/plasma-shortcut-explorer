import time

import pytest
from PySide6.QtCore import QObject, Signal, QEvent, Qt, QPoint
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QSizeGrip

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


def test_render_search_and_native_columns(overlay):
    assert not overlay.refresh.isEnabled()
    overlay.loader.deliver(Discovery(rows()))
    assert overlay.refresh.isEnabled()
    assert overlay.tree.topLevelItemCount() == 2
    group = overlay.tree.topLevelItem(1)
    assert group.text(0) == "Windows" and group.childCount() == 2
    item = group.child(0)
    assert [item.text(i) for i in range(3)] == ["Alpha", "KWin", "Meta+A  or  Alt+A"]
    assert "kwin / a" == item.toolTip(0)
    overlay.input.setText("META B")
    assert overlay.tree.topLevelItemCount() == 1
    assert "Beta" in overlay.tree.currentItem().text(0)
    assert overlay.status.text() == "1 of 3 shortcuts shown"
    overlay.input.setText("no such shortcut")
    assert overlay.tree.topLevelItemCount() == 0
    assert "No matching" in overlay.status.text()
    overlay.input.clear()
    assert overlay.status.text() == "3 shortcuts configured"
    overlay.input.setText("   ")
    assert overlay.status.text() == "3 shortcuts configured"


def test_single_configured_shortcut_and_partial_filtered_count(overlay):
    overlay.loader.deliver(Discovery(rows()[:1]))
    assert overlay.status.text() == "1 shortcut configured"
    overlay.input.setText("missing")
    overlay.loader.deliver(Discovery(rows(), errors=["Component unavailable"]))
    assert overlay.status.text() == (
        "0 of 3 shortcuts shown · No matching assigned shortcuts"
        " · Partial discovery: Component unavailable")


@pytest.mark.parametrize("column", [0, 1, 2], ids=["action", "application", "shortcut"])
def test_header_sorting_preserves_groups_selection_and_order_on_render(overlay, qapp, column):
    shortcuts = [
        Shortcut("app", "z", "Alpha app", "Zulu entry", ("Ctrl+B", "Meta+B"), "Applications"),
        Shortcut("app", "a", "Zulu app", "Alpha entry", ("Ctrl+C",), "Applications"),
        Shortcut("app", "m", "Middle app", "Middle", ("Ctrl+A",), "Applications"),
        Shortcut("kwin", "z", "Alpha app", "Zulu entry", ("Meta+A",), "Windows"),
        Shortcut("kwin", "a", "Zulu app", "Alpha entry", ("Alt+A",), "Windows"),
    ]
    overlay.loader.deliver(Discovery(shortcuts))
    overlay.show()
    qapp.processEvents()
    header = overlay.tree.header()
    assert header.isSortIndicatorShown()
    assert header.sortIndicatorSection() == 0
    assert header.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
    assert overlay.selected_shortcut.action == "Alpha entry"
    selected = overlay.selected_shortcut

    def click_header():
        QTest.mouseClick(header.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(
            header.sectionViewportPosition(column) + header.sectionSize(column) // 2,
            header.height() // 2))
        qapp.processEvents()

    def assert_order(descending):
        assert header.sortIndicatorSection() == column
        assert header.sortIndicatorOrder() == (
            Qt.SortOrder.DescendingOrder if descending else Qt.SortOrder.AscendingOrder)
        assert [overlay.tree.topLevelItem(i).text(0) for i in range(2)] == [
            "Applications", "Windows"]
        for index in range(2):
            group = overlay.tree.topLevelItem(index)
            values = [group.child(i).text(column) for i in range(group.childCount())]
            assert values == sorted(values, reverse=descending)

    click_header()
    if header.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder:
        click_header()
    assert_order(False)
    click_header()
    assert_order(True)
    assert overlay.selected_shortcut == selected
    assert overlay.tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == selected
    assert selected.action in overlay.detail_text.text()

    overlay.input.setText("entry")
    assert_order(True)
    assert overlay.tree.topLevelItem(0).childCount() == 2
    assert overlay.tree.currentItem() == overlay.tree.topLevelItem(0).child(0)
    overlay.refresh.click()
    overlay.loader.deliver(Discovery(list(reversed(shortcuts))))
    assert_order(True)
    overlay.input.setText("no matching action")
    assert overlay.tree.topLevelItemCount() == 0
    click_header()
    overlay.input.clear()
    assert_order(False)
    assert overlay.tree.currentItem() == overlay.tree.topLevelItem(0).child(0)


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


def test_native_window_stays_open_when_focus_moves(overlay, qapp, monkeypatch):
    overlay.loader.deliver(Discovery())
    overlay.show()
    qapp.processEvents()
    assert not overlay.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert overlay.windowType() == Qt.WindowType.Window
    monkeypatch.setattr(overlay, "isActiveWindow", lambda: False)
    qapp.sendEvent(overlay, QEvent(QEvent.Type.ActivationChange))
    assert overlay.isVisible()
    assert not overlay.exits


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
    assert overlay.detail_text.text() == "In Plasma’s Shortcuts page: KWin → Alpha."
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


def test_resizing_gives_results_more_space_and_preserves_size(overlay, qapp):
    overlay.loader.deliver(Discovery(rows()))
    overlay.show()
    qapp.processEvents()
    assert overlay.status_bar.findChild(QSizeGrip).isVisible()
    assert overlay.details.height() < 90
    original_tree_height = overlay.tree.height()
    original_action_width = overlay.tree.columnWidth(0)
    original_keys_width = overlay.tree.columnWidth(2)
    overlay.resize(overlay.width() - 100, overlay.height() - 80)
    qapp.processEvents()
    assert overlay.tree.height() < original_tree_height
    assert overlay.tree.columnWidth(0) < original_action_width
    assert overlay.tree.columnWidth(2) == original_keys_width
    resized = overlay.size()
    overlay.hide()
    overlay.show()
    qapp.processEvents()
    assert overlay.size() == resized
    overlay.show_settings()
    qapp.processEvents()
    assert overlay.settings_page.isVisible()
    assert not overlay.status_bar.isVisible()


def test_many_bindings_leave_room_for_action_names(overlay, qapp):
    keys = ("Meta+Ctrl+Shift+Alt+Left", "Meta+Ctrl+Shift+Alt+Right", "Ctrl+F10")
    overlay.loader.deliver(Discovery([
        Shortcut("kwin", "long", "KWin", "Action with several bindings", keys, "Windows")]))
    overlay.show()
    qapp.processEvents()
    assert overlay.tree.columnWidth(0) > overlay.tree.columnWidth(2)
    item = overlay.tree.currentItem()
    assert item.toolTip(2) == "  or  ".join(keys)
    assert item.text(2) == "  or  ".join(keys)
    original_keys_width = overlay.tree.columnWidth(2)
    overlay.resize(680, 520)
    qapp.processEvents()
    assert overlay.tree.columnWidth(2) < original_keys_width
    assert overlay.tree.columnWidth(0) > overlay.tree.columnWidth(2)


@pytest.mark.parametrize("column", [0, 1, 2], ids=["action", "application", "shortcut"])
def test_dragged_column_widths_survive_search_refresh_and_window_resize(overlay, qapp, column):
    overlay.loader.deliver(Discovery(rows()))
    overlay.show()
    qapp.processEvents()
    header = overlay.tree.header()
    original = header.sectionSize(column)
    divider = QPoint(header.sectionViewportPosition(column) + original - 1,
                     header.height() // 2)
    QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=divider)
    QTest.mouseMove(header.viewport(), divider + QPoint(-30, 0))
    QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton,
                       pos=divider + QPoint(-30, 0))
    qapp.processEvents()
    assert header.sectionSize(column) < original
    widths = [header.sectionSize(i) for i in range(3)]
    overlay.input.setText("Meta B")
    overlay.refresh.click()
    overlay.loader.deliver(Discovery(rows()))
    overlay.input.clear()
    overlay.resize(overlay.width() + 100, overlay.height())
    qapp.processEvents()
    assert [header.sectionSize(i) for i in range(3)] == widths
    assert overlay.tree.currentItem().text(0) == "Volume Up"


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


def test_search_shortcuts_preserve_typing_and_return_from_settings(overlay, qapp):
    overlay.loader.deliver(Discovery(rows()))
    overlay.show()
    overlay.activateWindow()
    qapp.processEvents()
    overlay.tree.setFocus()
    QTest.keyClick(overlay.tree, Qt.Key.Key_Slash)
    assert overlay.input.hasFocus()
    assert overlay.input.text() == ""
    QTest.keyClicks(overlay.input, "kwin/alpha")
    assert overlay.input.text() == "kwin/alpha"
    overlay.show_settings()
    QTest.keyClick(overlay.settings_page.configure, Qt.Key.Key_Slash)
    assert overlay.pages.currentIndex() == 0
    assert overlay.input.hasFocus()
    assert overlay.input.selectedText() == "kwin/alpha"
    overlay.refresh.setFocus()
    QTest.keyClick(overlay.refresh, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)
    assert overlay.loader.starts == 2


@pytest.mark.parametrize("spacing", [0, 4])
def test_settings_scroll_at_large_system_font(overlay, qapp, spacing):
    from PySide6.QtGui import QFont
    original = QFont(qapp.font())
    try:
        font = QFont(original)
        font.setPointSize(14)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        qapp.setFont(font)
        overlay.show_settings()
        overlay.resize(540, 400)
        overlay.show()
        qapp.processEvents()
        page = overlay.settings_page
        assert page.verticalScrollBar().maximum() > 0
        assert page.horizontalScrollBar().maximum() == 0
        page.ensureWidgetVisible(page.check_updates)
        qapp.processEvents()
        assert page.verticalScrollBar().value() > 0
        assert page.configure.font().pointSize() == 14
    finally:
        qapp.setFont(original)
