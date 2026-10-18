"""Asynchronous, rate-limited checks of public GitHub release metadata."""
import json
import re
import time

from PySide6.QtCore import QObject, QSettings, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import __version__

REPOSITORY = "Raithlin/plasma-shortcut-explorer"
RELEASES_URL = f"https://github.com/{REPOSITORY}/releases"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
INTERVAL = 24 * 60 * 60
MAX_RESPONSE = 64 * 1024


def release_notice(tag, current=__version__):
    """Compare this project's stable three-part versions numerically."""
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Unexpected release version")
    latest = tuple(map(int, tag[1:].split(".")))
    installed = tuple(map(int, current.split(".")))
    if latest > installed:
        return f"Version {tag[1:]} is available (installed: {current}).", f"{RELEASES_URL}/tag/{tag}"
    return f"You’re up to date (installed: {current}).", ""


class UpdateChecker(QObject):
    checked = Signal(str, str)

    def __init__(self, parent=None, *, settings=None, manager=None, clock=time.time):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings("Raithlin", "PlasmaShortcutExplorer")
        self.manager = manager if manager is not None else QNetworkAccessManager(self)
        self.clock = clock
        self.reply = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.cancel)

    def enabled(self):
        return self.settings.value("updates/automatic", True, type=bool)

    def set_enabled(self, enabled):
        self.settings.setValue("updates/automatic", enabled)
        if not enabled:
            self.cancel()

    def check(self, manual=False):
        if self.reply is not None:
            return
        if not manual:
            if not self.enabled():
                return
            last = self.settings.value("updates/lastAttempt", 0, type=float)
            if 0 <= self.clock() - last < INTERVAL:
                tag = self.settings.value("updates/latestTag", "", type=str)
                if tag:
                    try:
                        self.checked.emit(*release_notice(tag))
                    except ValueError:
                        self.settings.remove("updates/latestTag")
                return
        self.settings.setValue("updates/lastAttempt", self.clock())
        request = QNetworkRequest(QUrl(API_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", f"Plasma-Shortcut-Explorer/{__version__}".encode())
        request.setTransferTimeout(10000)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.SameOriginRedirectPolicy)
        self.data = bytearray()
        self.reply = self.manager.get(request)
        self.reply.setReadBufferSize(MAX_RESPONSE + 1)
        self.reply.readyRead.connect(self.read)
        self.reply.finished.connect(self.finished)
        self.timer.start(10000)
        self.checked.emit("Checking for updates…", "")

    def read(self):
        self.data.extend(bytes(self.reply.readAll()))
        if len(self.data) > MAX_RESPONSE and self.timer.isActive():
            self.reply.abort()

    def cancel(self):
        if self.reply is not None:
            self.reply.abort()

    def finished(self):
        self.timer.stop()
        reply = self.reply
        self.read()
        self.reply = None
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        try:
            if status == 404:
                self.checked.emit("No published release is available yet.", "")
                self.settings.remove("updates/latestTag")
            elif reply.error() != QNetworkReply.NetworkError.NoError:
                self.checked.emit("Could not check for updates. Try again later.", "")
            else:
                if len(self.data) > MAX_RESPONSE:
                    raise ValueError("Release response too large")
                payload = json.loads(self.data)
                if not isinstance(payload, dict) or payload.get("draft") is not False or payload.get("prerelease") is not False:
                    raise ValueError("Not a stable release")
                tag = payload.get("tag_name")
                notice = release_notice(tag)
                self.settings.setValue("updates/latestTag", tag)
                self.checked.emit(*notice)
        except (ValueError, TypeError):
            self.checked.emit("Could not read GitHub’s release information. Try again later.", "")
        finally:
            reply.deleteLater()
