import asyncio
from PySide6.QtCore import Qt, QThread, Signal, QEvent, QSize
from PySide6.QtGui import QGuiApplication, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton)
from .config import WIDTH, HEIGHT
from .discovery import discover
from .search import search


class Loader(QThread):
    loaded = Signal(object)

    def run(self):
        self.loaded.emit(asyncio.run(discover(cancelled=self.isInterruptionRequested)))


class Overlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Shortcut Explorer")
        self.resize(WIDTH, HEIGHT)
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        title = QLabel("Shortcut Explorer")
        title.setStyleSheet("font-size: 22px; font-weight: 600")
        layout.addWidget(title)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search actions, apps, keys…")
        self.input.setClearButtonEnabled(True)
        layout.addWidget(self.input)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setColumnWidth(0, 420)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(12)
        layout.addWidget(self.tree)
        self.status = QLabel("Reading current KDE shortcuts…")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("↑ ↓ Navigate    •    Esc Close"))
        bottom.addStretch()
        self.refresh = QPushButton("Refresh")
        bottom.addWidget(self.refresh)
        layout.addLayout(bottom)
        self.setStyleSheet("QLineEdit { padding: 10px; } QTreeWidget { border: 0; } QTreeWidget::item { padding: 6px; }")
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.input.setFocus)
        self.input.textChanged.connect(self.render)
        self.input.installEventFilter(self)
        self.refresh.clicked.connect(self.reload)
        QShortcut(QKeySequence("Escape"), self, activated=self.close)
        self.loader = Loader(self)
        self.loader.loaded.connect(self.loaded)
        self.reload()

    def reload(self):
        if self.loader.isRunning():
            return
        self.refresh.setEnabled(False)
        self.status.setText("Reading current KDE shortcuts…")
        self.loader.start()

    def loaded(self, result):
        self.rows = result.rows
        self.errors = result.errors
        self.refresh.setEnabled(True)
        self.render()

    def render(self):
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
            item.setSizeHint(0, QSize(0, 42))
            item.setToolTip(0, f"{row.component} / {row.action_id}")
            caps = QWidget()
            box = QHBoxLayout(caps)
            box.setContentsMargins(2, 2, 2, 2)
            for key in row.keys:
                label = QLabel(key)
                label.setStyleSheet("border: 1px solid palette(mid); border-radius: 4px; padding: 3px 6px; background: palette(alternate-base)")
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
        self.input.setFocus()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow() and self.isVisible():
            self.close()
        super().changeEvent(event)

    def closeEvent(self, event):
        # Keep the worker alive until completion; exit without destroying a running QThread.
        self.hide()
        self.loader.requestInterruption()
        if self.loader.isRunning():
            self.loader.finished.connect(QGuiApplication.quit)
        else:
            QGuiApplication.quit()
        event.accept()
