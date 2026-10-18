import json

import pytest
from PySide6.QtCore import QLockFile, QTimer

from kde_shortcuts import app
from kde_shortcuts.discovery import Discovery
from kde_shortcuts.model import Shortcut


@pytest.mark.parametrize("errors,code", [([], 0), (["Missing KDE service"], 1)])
def test_diagnostics_are_json_with_status(monkeypatch, capsys, errors, code):
    async def discover():
        return Discovery([Shortcut("kwin", "a", "KWin", "Action", ("Meta+A",), "Windows")], errors)
    monkeypatch.setattr(app, "discover", discover)
    assert app.main(["--diagnose"]) == code
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"] == errors
    assert payload["rows"][0]["keys"] == ["Meta+A"]


def test_help_never_starts_gui(capsys):
    with pytest.raises(SystemExit) as exc:
        app.main(["--help"])
    assert exc.value.code == 0
    assert "--diagnose" in capsys.readouterr().out


@pytest.fixture
def runtime(qapp, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "QApplication", lambda argv: qapp)
    monkeypatch.setattr(app.QStandardPaths, "writableLocation", lambda location: str(tmp_path))
    return tmp_path


def test_second_instance_does_not_open_window(runtime, monkeypatch):
    from kde_shortcuts import ui
    lock = QLockFile(str(runtime / "kde-shortcut-explorer.lock"))
    assert lock.tryLock(0)
    def unexpected_window():
        pytest.fail("Second instance must not create an overlay")
    monkeypatch.setattr(ui, "Overlay", unexpected_window)
    try:
        assert app.main([]) == 0
    finally:
        lock.unlock()


@pytest.mark.parametrize("mode", [[], ["--settings"]])
def test_real_application_lifecycle(runtime, qapp, monkeypatch, mode):
    from kde_shortcuts import ui
    from test_ui import ControlledLoader
    monkeypatch.setattr(ui, "Loader", ControlledLoader)
    observed = []
    original_overlay = ui.Overlay

    def window():
        widget = original_overlay()
        widget.loader.deliver(Discovery())
        def close():
            observed.append((widget.isVisible(), widget.pages.currentIndex()))
            widget.close()
        QTimer.singleShot(20, close)
        return widget

    monkeypatch.setattr(ui, "Overlay", window)
    assert app.main(mode) == 0
    assert observed == [(True, int(bool(mode)))]
    assert qapp.desktopFileName() == app.APP_ID
    assert not (runtime / "kde-shortcut-explorer.lock").exists()


def test_diagnostics_and_settings_are_mutually_exclusive():
    with pytest.raises(SystemExit) as exc:
        app.main(["--diagnose", "--settings"])
    assert exc.value.code == 2
