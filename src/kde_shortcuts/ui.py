import asyncio
from PySide6.QtCore import Qt, QThread, Signal, QEvent, QSize
from PySide6.QtGui import QGuiApplication, QCursor, QKeySequence, QShortcut, QPalette
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton, QStackedWidget, QFrame)
from .config import WIDTH, HEIGHT
from .settings_ui import SettingsPage
from .integration import open_shortcut_settings
from .discovery import discover
from .search import search


class Loader(QThread):
    loaded = Signal(object)

    def run(self):
        self.loaded.emit(asyncio.run(discover(cancelled=self.isInterruptionRequested)))


class Overlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Plasma Shortcut Explorer")
        self.resize(WIDTH, HEIGHT)
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        title = QLabel("Plasma Shortcut Explorer")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.toggle_settings)
        header.addWidget(self.settings_button)
        layout.addLayout(header)
        self.pages = QStackedWidget()
        explorer = QWidget()
        content = QVBoxLayout(explorer)
        content.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(explorer)
        layout.addWidget(self.pages)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search actions, apps, keys…")
        self.input.setClearButtonEnabled(True)
        self.input.setTextMargins(8, 6, 8, 6)
        self.input.setMinimumHeight(38)
        content.addWidget(self.input)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.setColumnCount(2)
        self.tree.setColumnWidth(0, 420)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(12)
        content.addWidget(self.tree)
        self.details = QFrame()
        self.details.setFrameShape(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(self.details)
        self.detail_text = QLabel()
        self.detail_text.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_text.setWordWrap(True)
        details_layout.addWidget(self.detail_text)
        self.edit_button = QPushButton("Edit in Plasma…")
        self.edit_button.clicked.connect(self.edit_selected)
        details_layout.addWidget(self.edit_button)
        self.details.hide()
        content.addWidget(self.details)
        self.tree.currentItemChanged.connect(self.selection_changed)
        self.status = QLabel("Reading current KDE shortcuts…")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        content.addWidget(self.status)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("↑ ↓ Navigate    •    Esc Close"))
        bottom.addStretch()
        self.refresh = QPushButton("Refresh")
        bottom.addWidget(self.refresh)
        content.addLayout(bottom)
        self.settings_page = SettingsPage()
        self.pages.addWidget(self.settings_page)
        self.update_banner = QPushButton()
        self.update_banner.hide()
        self.update_banner.clicked.connect(self.show_settings)
        self.settings_page.update_checker.checked.connect(self.show_update)
        layout.addWidget(self.update_banner)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.show_settings)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.input.setFocus)
        self.input.textChanged.connect(self.render)
        self.input.installEventFilter(self)
        self.refresh.clicked.connect(self.reload)
        QShortcut(QKeySequence("Escape"), self, activated=self.close)
        self.loader = Loader(self)
        self.loader.loaded.connect(self.loaded)
        self.reload()

    def show_update(self, message, url):
        self.update_banner.setText(message + " View in Settings…")
        self.update_banner.setVisible(bool(url))

    def selection_changed(self, current, previous=None):
        row = current.data(0, Qt.ItemDataRole.UserRole) if current else None
        self.selected_shortcut = row
        self.details.setVisible(row is not None)
        if row is not None:
            self.detail_text.setText(
                f"{row.action}\n{row.application} · {row.category}\n"
                f"{'  or  '.join(row.keys)}\n"
                f"In Plasma’s Shortcuts page, find {row.application}, then {row.action}.")
            self.detail_text.setToolTip(f"{row.component} / {row.action_id}")

    def edit_selected(self):
        row = getattr(self, "selected_shortcut", None)
        if row is None:
            return
        try:
            open_shortcut_settings(row.component)
        except OSError as error:
            self.status.setText(str(error))

    def show_settings(self):
        self.pages.setCurrentIndex(1)
        self.settings_button.setText("Back to shortcuts")
        self.settings_page.configure.setFocus()

    def toggle_settings(self):
        if self.pages.currentIndex() == 0:
            self.show_settings()
        else:
            self.pages.setCurrentIndex(0)
            self.settings_button.setText("Settings")
            self.input.setFocus()

    def reload(self):
        if self.loader.isRunning():
            return
        self.refresh.setEnabled(False)
        self.status.setText("Reading current KDE shortcuts…")
        self.loader.start()

    def loaded(self, result):
        self.rows = result.rows
        self.errors = result.errors
        self.settings_page.set_shortcuts(result.rows, result.errors)
        self.refresh.setEnabled(True)
        self.render()

    def render(self):
        self.selection_changed(None)
        self.tree.clear()
        matches = search(self.rows, self.input.text())
        groups = {}
        first = None
        for row in matches:
            if row.category not in groups:
                group = QTreeWidgetItem(self.tree, [row.category])
                group.setFlags(Qt.ItemFlag.ItemIsEnabled)
                font = group.font(0)
                font.setBold(True)
                group.setFont(0, font)
                group.setExpanded(True)
                groups[row.category] = group
            item = QTreeWidgetItem(groups[row.category], [f"{row.action}  ·  {row.application}"])
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            item.setSizeHint(0, QSize(0, 42))
            item.setToolTip(0, f"{row.component} / {row.action_id}")
            caps = QWidget()
            box = QHBoxLayout(caps)
            box.setContentsMargins(2, 2, 2, 2)
            for key in row.keys:
                label = QLabel(key)
                label.setFrameShape(QFrame.Shape.StyledPanel)
                label.setMargin(4)
                label.setAutoFillBackground(True)
                label.setBackgroundRole(QPalette.ColorRole.AlternateBase)
                box.addWidget(label)
            box.addStretch()
            self.tree.setItemWidget(item, 1, caps)
            first = first or item
        if first:
            self.tree.setCurrentItem(first)
        errors = getattr(self, "errors", [])
        self.status.setText(f"{len(matches)} configured actions" + (f" · Partial discovery: {errors[0]}" if errors else "" if matches else " · No matching assigned shortcuts"))
        self.status.setToolTip("\n".join(errors))

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.tree.setFocus()
            QGuiApplication.sendEvent(self.tree, event)
            return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.resize(min(WIDTH, geometry.width()), min(HEIGHT, geometry.height()))
        self.move(geometry.center() - self.rect().center())
        if self.pages.currentIndex() == 0:
            self.input.setFocus()
        else:
            self.settings_page.configure.setFocus()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow() and self.isVisible():
            self.close()
        super().changeEvent(event)

    def closeEvent(self, event):
        # Keep the worker alive until completion; exit without destroying a running QThread.
        self.hide()
        self.settings_page.update_checker.cancel()
        self.loader.requestInterruption()
        self.loader.finished.connect(QGuiApplication.quit)
        if not self.loader.isRunning():
            QGuiApplication.quit()
        event.accept()
