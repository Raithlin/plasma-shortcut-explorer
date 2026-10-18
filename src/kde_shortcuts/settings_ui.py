from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from .config import APP_ID
from .integration import open_shortcut_settings


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
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.message)
        layout.addStretch()

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
