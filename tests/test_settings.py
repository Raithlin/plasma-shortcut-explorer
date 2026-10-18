import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtTest import QTest

from kde_shortcuts import integration, ui
from kde_shortcuts.config import APP_ID
from kde_shortcuts.discovery import Discovery
from kde_shortcuts.model import Shortcut
from test_ui import ControlledLoader


@pytest.fixture
def window(qapp, monkeypatch):
    monkeypatch.setattr(ui, "Loader", ControlledLoader)
    monkeypatch.setattr(ui.QGuiApplication, "quit", lambda: None)
    widget = ui.Overlay()
    widget.loader.deliver(Discovery())
    yield widget
    widget.hide()
    widget.deleteLater()
    qapp.processEvents()


def test_settings_navigation_and_escape(window, qapp):
    window.show()
    window.activateWindow()
    qapp.processEvents()
    QTest.keyClick(window.input, Qt.Key.Key_Comma, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 1
    assert window.settings_page.configure.hasFocus()
    window.settings_button.click()
    assert window.pages.currentIndex() == 0 and window.input.hasFocus()
    window.settings_button.click()
    assert window.pages.currentIndex() == 1
    QTest.keyClick(window.settings_page.configure, Qt.Key.Key_Escape)
    assert not window.isVisible()


def test_system_palette_is_not_overridden(window, qapp):
    original = QPalette(qapp.palette())
    try:
        assert window.palette().resolveMask() == 0
        for text, color in (("#eeeeee", "#202326"), ("#202326", "#eeeeee")):
            palette = QPalette(original)
            palette.setColor(QPalette.ColorRole.WindowText, QColor(text))
            palette.setColor(QPalette.ColorRole.Window, QColor(color))
            qapp.setPalette(palette)
            qapp.processEvents()
            assert window.palette().color(QPalette.ColorRole.Window).name() == color
            assert window.settings_page.binding.palette().color(QPalette.ColorRole.WindowText).name() == text
            assert qapp.palette() == palette
    finally:
        qapp.setPalette(original)


@pytest.mark.parametrize("component", [APP_ID, APP_ID + ".desktop"])
def test_settings_reads_only_its_launcher(window, component):
    row = Shortcut(component, "_launch", "App", "Launch", ("Meta+K", "Alt+K"), "Applications")
    unrelated = Shortcut("other", "_launch", "Other", "Launch", ("Meta+X",), "Applications")
    window.loaded(Discovery([row, row, unrelated]))
    assert window.settings_page.binding.text() == "Current launch shortcut: Meta+K  or  Alt+K"
    window.loaded(Discovery(errors=["KDE unavailable"]))
    assert "incomplete" in window.settings_page.binding.text()
    window.loaded(Discovery([unrelated]))
    assert "No shortcut found" in window.settings_page.binding.text()


def test_settings_opens_native_editor_and_displays_failure(window, monkeypatch):
    from kde_shortcuts import settings_ui
    calls = []
    monkeypatch.setattr(settings_ui, "open_shortcut_settings", lambda: calls.append(True))
    window.settings_page.configure.click()
    assert calls and "Opening Plasma" in window.settings_page.message.text()
    def fail():
        raise OSError("Editor is missing")
    monkeypatch.setattr(settings_ui, "open_shortcut_settings", fail)
    window.settings_page.configure.click()
    assert window.settings_page.message.text() == "Editor is missing"


@pytest.mark.parametrize("preferred", ["systemsettings", "kcmshell6"])
def test_native_editor_uses_verified_kcm(preferred, monkeypatch):
    monkeypatch.setattr(integration, "which", lambda name: "/usr/bin/" + name if name == preferred else None)
    calls = []
    monkeypatch.setattr(integration.QProcess, "startDetached", lambda executable, args: (
        calls.append((executable, args)) or (True, 123)))
    integration.open_shortcut_settings()
    assert calls == [("/usr/bin/" + preferred, ["kcm_keys"])]


def test_native_editor_missing_or_failed(monkeypatch):
    monkeypatch.setattr(integration, "which", lambda name: None)
    with pytest.raises(OSError, match="not found"):
        integration.open_shortcut_settings()
    monkeypatch.setattr(integration, "which", lambda name: "/usr/bin/systemsettings")
    monkeypatch.setattr(integration.QProcess, "startDetached", lambda *args: (False, 0))
    with pytest.raises(OSError, match="Could not open"):
        integration.open_shortcut_settings()


@pytest.mark.parametrize("component, expected", [
    ("kwin", ["kcm_keys", "--args", "kwin"]),
    ("KDE Keyboard Layout Switcher", ["kcm_keys"]),
])
def test_native_editor_component_target(component, expected, monkeypatch):
    monkeypatch.setattr(integration, "which", lambda name: "/usr/bin/" + name)
    calls = []
    monkeypatch.setattr(integration.QProcess, "startDetached", lambda exe, args: (
        calls.append(args) or (True, 123)))
    integration.open_shortcut_settings(component)
    assert calls == [expected]
