from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox

from .config import APP_ID
from .integration import open_shortcut_settings
from . import __version__
from .updates import UpdateChecker


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        heading = QLabel("Launch shortcut")
        font = heading.font()
        font.setPointSize(12)
        font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)
        self.binding = QLabel("Reading current bindings…")
        self.binding.setWordWrap(True)
        self.binding.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.binding)
        instructions = QLabel("Choose or change the launch key in Plasma's Shortcuts editor. "
            "Select Plasma Shortcut Explorer, or use Add New → Application to add it. "
            "Plasma checks for conflicts before applying your choice.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.configure = QPushButton("Configure launch shortcut in Plasma…")
        self.configure.clicked.connect(self.open_shortcuts)
        layout.addWidget(self.configure, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(24)
        appearance = QLabel("Appearance")
        appearance.setFont(font)
        layout.addWidget(appearance)
        description = QLabel("This app follows Qt's system appearance. Change application colors "
            "and style in Plasma's System Settings → Colors & Themes.")
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addSpacing(16)
        updates = QLabel(f"Updates · installed version {__version__}")
        updates.setFont(font)
        layout.addWidget(updates)
        self.update_checker = UpdateChecker(self)
        self.update_url = ""
        self.automatic_updates = QCheckBox("Check automatically once a day")
        self.automatic_updates.setChecked(self.update_checker.enabled())
        self.automatic_updates.toggled.connect(self.update_checker.set_enabled)
        layout.addWidget(self.automatic_updates)
        self.update_status = QLabel("Checks contact GitHub for the latest stable release.")
        self.update_status.setWordWrap(True)
        self.update_status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.update_status)
        self.check_updates = QPushButton("Check now")
        self.check_updates.clicked.connect(lambda: self.update_checker.check(manual=True))
        layout.addWidget(self.check_updates, alignment=Qt.AlignmentFlag.AlignLeft)
        self.release_button = QPushButton("View release downloads…")
        self.release_button.clicked.connect(self.open_release)
        self.release_button.hide()
        layout.addWidget(self.release_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.update_checker.checked.connect(self.show_update)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.message)
        layout.addStretch()

    def show_update(self, message, url):
        self.update_status.setText(message)
        self.update_url = url
        self.release_button.setVisible(bool(url))

    def open_release(self):
        if self.update_url and not QDesktopServices.openUrl(QUrl(self.update_url)):
            self.update_status.setText("Could not open the browser. Visit github.com/Raithlin/plasma-shortcut-explorer/releases.")

    def set_shortcuts(self, rows, errors):
        bindings = tuple(dict.fromkeys(key for row in rows
            if row.component in (APP_ID, APP_ID + ".desktop") and row.action_id == "_launch"
            for key in row.keys))
        if errors:
            text = "Shortcut discovery is incomplete. Check the current launch key in Plasma's Shortcuts editor."
        elif bindings:
            text = "Current launch shortcut: " + "  or  ".join(bindings)
        else:
            text = "No shortcut found for this app's launcher. If you use a custom command shortcut, manage it in Plasma."
        self.binding.setText(text)

    def open_shortcuts(self):
        try:
            open_shortcut_settings()
            self.message.setText("Opening Plasma's Shortcuts editor. Reopen the app after applying your change.")
        except OSError as exc:
            self.message.setText(str(exc))
