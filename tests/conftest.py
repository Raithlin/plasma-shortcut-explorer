import os

# Deterministic headless default; set QT_QPA_PLATFORM=wayland explicitly for a live check.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def isolated_update_preferences(tmp_path, monkeypatch):
    from kde_shortcuts import updates
    monkeypatch.setattr(updates, "QSettings", lambda *args: QSettings(
        str(tmp_path / "updates.ini"), QSettings.Format.IniFormat))


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app

