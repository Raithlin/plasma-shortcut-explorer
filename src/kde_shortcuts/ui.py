import asyncio
from PySide6.QtCore import Qt, QThread, Signal, QEvent
from PySide6.QtGui import QGuiApplication, QCursor, QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton, QStackedWidget, QFrame,
    QHeaderView, QStatusBar, QAbstractItemView)
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
        super().__init__()
        self.setWindowTitle("Plasma Shortcut Explorer")
        self.resize(WIDTH, HEIGHT)
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolbar = QWidget()
        header = QHBoxLayout(toolbar)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search actions, applications, or shortcuts")
        self.input.setAccessibleName("Search shortcuts")
        self.input.setToolTip("Focus search with / or Ctrl+F")
        self.input.setClearButtonEnabled(True)
        self.input.addAction(QIcon.fromTheme("edit-find"), QLineEdit.ActionPosition.LeadingPosition)
        header.addWidget(self.input, 1)
        self.page_title = QLabel("Settings")
        self.page_title.hide()
        header.addWidget(self.page_title, 1)
        self.refresh = QPushButton(QIcon.fromTheme("view-refresh"), "&Refresh")
        self.refresh.setToolTip("Read current shortcuts again (Ctrl+R)")
        header.addWidget(self.refresh)
        self.settings_button = QPushButton(QIcon.fromTheme("configure"), "&Settings")
        self.settings_button.setToolTip("Settings (Ctrl+,)")
        self.settings_button.clicked.connect(self.toggle_settings)
        header.addWidget(self.settings_button)
        layout.addWidget(toolbar)
        self.pages = QStackedWidget()
        explorer = QWidget()
        content = QVBoxLayout(explorer)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        self.pages.addWidget(explorer)
        layout.addWidget(self.pages, 1)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Action", "Application", "Shortcut"])
        self.tree.setAccessibleName("Assigned global shortcuts")
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.columns_resized = False
        self.resizing_columns = False
        self.tree.header().sectionResized.connect(self.column_resized)
        self.tree.header().setSectionsClickable(True)
        self.tree.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.tree.header().setSortIndicatorShown(True)
        self.tree.header().sortIndicatorChanged.connect(self.sort_results)
        self.tree.viewport().installEventFilter(self)
        self.tree.setRootIsDecorated(False)
        self.tree.setItemsExpandable(False)
        self.tree.setIndentation(0)
        content.addWidget(self.tree, 1)
        self.details = QFrame()
        details_layout = QHBoxLayout(self.details)
        self.detail_text = QLabel()
        self.detail_text.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_text.setWordWrap(True)
        details_layout.addWidget(self.detail_text, 1)
        self.edit_button = QPushButton(QIcon.fromTheme("document-edit"), "&Edit in Plasma…")
        self.edit_button.clicked.connect(self.edit_selected)
        details_layout.addWidget(self.edit_button)
        self.details.hide()
        content.addWidget(self.details)
        self.tree.currentItemChanged.connect(self.selection_changed)
        self.settings_page = SettingsPage()
        self.pages.addWidget(self.settings_page)
        self.update_banner = QPushButton()
        self.update_banner.setIcon(QIcon.fromTheme("software-update-available"))
        self.update_banner.hide()
        self.update_banner.clicked.connect(self.show_settings)
        self.settings_page.update_checker.checked.connect(self.show_update)
        layout.addWidget(self.update_banner)
        self.status_bar = QStatusBar()
        self.status = QLabel("Reading current KDE shortcuts…")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status_bar.addWidget(self.status, 1)
        layout.addWidget(self.status_bar)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.show_settings)
        QShortcut(QKeySequence("/"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.reload)
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
                f"In Plasma’s Shortcuts page: {row.application} → {row.action}.")
            self.detail_text.setToolTip(f"{row.component} / {row.action_id}")

    def edit_selected(self):
        row = getattr(self, "selected_shortcut", None)
        if row is None:
            return
        try:
            open_shortcut_settings(row.component)
        except OSError as error:
            self.status.setText(str(error))

    def focus_search(self):
        self.show_explorer()
        self.input.setFocus()
        self.input.selectAll()

    def show_explorer(self):
        self.pages.setCurrentIndex(0)
        self.input.show()
        self.refresh.show()
        self.page_title.hide()
        self.status_bar.show()
        self.settings_button.setText("&Settings")
        self.settings_button.setIcon(QIcon.fromTheme("configure"))
        self.settings_button.setToolTip("Settings (Ctrl+,)")
        self.input.setFocus()

    def show_settings(self):
        self.pages.setCurrentIndex(1)
        self.input.hide()
        self.refresh.hide()
        self.page_title.show()
        self.status_bar.hide()
        self.settings_button.setText("&Back")
        self.settings_button.setIcon(QIcon.fromTheme("go-previous"))
        self.settings_button.setToolTip("Back to shortcuts")
        self.settings_page.configure.setFocus()

    def toggle_settings(self):
        if self.pages.currentIndex() == 0:
            self.show_settings()
        else:
            self.show_explorer()

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
        for row in matches:
            if row.category not in groups:
                group = QTreeWidgetItem(self.tree, [row.category])
                group.setFlags(Qt.ItemFlag.ItemIsEnabled)
                font = group.font(0)
                font.setBold(True)
                group.setFont(0, font)
                group.setFirstColumnSpanned(True)
                group.setExpanded(True)
                groups[row.category] = group
            item = QTreeWidgetItem(groups[row.category],
                                   [row.action, row.application, "  or  ".join(row.keys)])
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            item.setToolTip(0, f"{row.component} / {row.action_id}")
            item.setToolTip(1, row.application)
            item.setToolTip(2, "  or  ".join(row.keys))
        self.sort_results()
        self.resize_columns()
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0).child(0))
        errors = getattr(self, "errors", [])
        count = f"{len(self.rows)} shortcut{'s' if len(self.rows) != 1 else ''} configured"
        if self.input.text().strip():
            count = f"{len(matches)} of {len(self.rows)} shortcuts shown"
        if not matches:
            count += " · No matching assigned shortcuts"
        if errors:
            count += f" · Partial discovery: {errors[0]}"
        self.status.setText(count)
        self.status.setToolTip("\n".join(errors))

    def sort_results(self):
        # Sort shortcuts within each category, keeping category headings in place.
        header = self.tree.header()
        for index in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(index).sortChildren(
                header.sortIndicatorSection(), header.sortIndicatorOrder())

    def resize_columns(self):
        # Keep action names usable at narrow widths; full text is in tooltips.
        # Once the user adjusts a column, leave the first two widths alone.
        if self.columns_resized or self.resizing_columns:
            return
        self.resizing_columns = True
        width = self.tree.viewport().width()
        self.tree.setColumnWidth(1, min(self.tree.sizeHintForColumn(1), int(width * 0.25)))
        keys_width = min(self.tree.sizeHintForColumn(2), int(width * 0.35))
        self.tree.setColumnWidth(0, max(self.tree.header().minimumSectionSize(),
                                      width - self.tree.columnWidth(1) - keys_width))
        self.resizing_columns = False

    def column_resized(self, column):
        if column != 2 and not self.resizing_columns:
            self.columns_resized = True

    def eventFilter(self, obj, event):
        if obj is self.tree.viewport() and event.type() == QEvent.Type.Resize:
            self.resize_columns()
        if obj is self.input and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.tree.setFocus()
            QGuiApplication.sendEvent(self.tree, event)
            return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.resize(min(self.width(), geometry.width()), min(self.height(), geometry.height()))
        self.move(geometry.center() - self.rect().center())
        if self.pages.currentIndex() == 0:
            self.input.setFocus()
        else:
            self.settings_page.configure.setFocus()

    def closeEvent(self, event):
        # Keep the worker alive until completion; exit without destroying a running QThread.
        self.hide()
        self.settings_page.update_checker.cancel()
        self.loader.requestInterruption()
        self.loader.finished.connect(QGuiApplication.quit)
        if not self.loader.isRunning():
            QGuiApplication.quit()
        event.accept()
