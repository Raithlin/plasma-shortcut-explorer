from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QScrollArea

from .config import APP_ID
from .integration import open_shortcut_settings
from . import __version__
from .updates import UpdateChecker


class SettingsPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        page = QWidget()
        self.setWidget(page)
        layout = QVBoxLayout(page)
        launch = QGroupBox("Launch Shortcut")
        launch_layout = QVBoxLayout(launch)
        layout.addWidget(launch)
        self.binding = QLabel("Reading current bindings…")
        self.binding.setWordWrap(True)
        self.binding.setTextFormat(Qt.TextFormat.PlainText)
        launch_layout.addWidget(self.binding)
        instructions = QLabel("Choose or change the launch key in Plasma's Shortcuts editor. "
            "Select Plasma Shortcut Explorer, or use Add New → Application to add it. "
            "Plasma checks for conflicts before applying your choice.")
        instructions.setWordWrap(True)
        launch_layout.addWidget(instructions)
        self.configure = QPushButton(QIcon.fromTheme("configure-shortcuts"), "&Configure Shortcut…")
        self.configure.clicked.connect(self.open_shortcuts)
        launch_layout.addWidget(self.configure, alignment=Qt.AlignmentFlag.AlignLeading)
        appearance = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance)
        layout.addWidget(appearance)
        description = QLabel("This app follows Qt's system appearance. Change application colors "
            "and style in Plasma's System Settings → Colors & Themes.")
        description.setWordWrap(True)
        appearance_layout.addWidget(description)
        updates = QGroupBox("Updates")
        updates_layout = QVBoxLayout(updates)
        updates_layout.addWidget(QLabel(f"Installed version: {__version__}"))
        layout.addWidget(updates)
        self.update_checker = UpdateChecker(self)
        self.update_url = ""
        self.automatic_updates = QCheckBox("Check for updates &automatically once a day")
        self.automatic_updates.setChecked(self.update_checker.enabled())
        self.automatic_updates.toggled.connect(self.update_checker.set_enabled)
        updates_layout.addWidget(self.automatic_updates)
        self.update_status = QLabel("Checks contact GitHub for the latest stable release.")
        self.update_status.setWordWrap(True)
        self.update_status.setTextFormat(Qt.TextFormat.PlainText)
        updates_layout.addWidget(self.update_status)
        self.check_updates = QPushButton(QIcon.fromTheme("view-refresh"), "Check &Now")
        self.check_updates.clicked.connect(lambda: self.update_checker.check(manual=True))
        updates_layout.addWidget(self.check_updates, alignment=Qt.AlignmentFlag.AlignLeading)
        self.release_button = QPushButton(QIcon.fromTheme("internet-services"), "View &Downloads")
        self.release_button.clicked.connect(self.open_release)
        self.release_button.hide()
        updates_layout.addWidget(self.release_button, alignment=Qt.AlignmentFlag.AlignLeading)
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
            self.message.setText("Opening Plasma's Shortcuts editor. Refresh shortcuts after applying your change.")
        except OSError as exc:
            self.message.setText(str(exc))
