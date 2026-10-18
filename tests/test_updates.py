import json

import pytest
from PySide6.QtCore import QByteArray, QObject, Signal
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtTest import QTest

from kde_shortcuts import updates, settings_ui
from test_ui import overlay  # noqa: F401 - shared overlay fixture


class Reply(QObject):
    readyRead = Signal()
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.data = b""
        self.status = 200
        self.failure = QNetworkReply.NetworkError.NoError
        self.aborted = False

    def setReadBufferSize(self, size):
        self.limit = size

    def readAll(self):
        data, self.data = self.data, b""
        return QByteArray(data)

    def attribute(self, attr):
        return self.status

    def error(self):
        return self.failure

    def abort(self):
        self.aborted = True
        self.failure = QNetworkReply.NetworkError.OperationCanceledError
        self.finished.emit()

    def deliver(self, data):
        self.data = data
        self.readyRead.emit()
        if not self.aborted:
            self.finished.emit()


class Manager:
    def __init__(self):
        self.requests = []

    def get(self, request):
        self.requests.append(request)
        self.reply = Reply()
        return self.reply


def payload(tag="v0.2.0", **kwargs):
    return json.dumps(dict(tag_name=tag, draft=False, prerelease=False, **kwargs)).encode()


@pytest.fixture
def checker(qapp):
    manager = Manager()
    instance = updates.UpdateChecker(manager=manager, clock=lambda: 100000)
    instance.notices = []
    instance.checked.connect(lambda *notice: instance.notices.append(notice))
    yield instance
    instance.cancel()


@pytest.mark.parametrize("tag,current,newer", [
    ("v0.2.0", "0.1.0", True), ("v0.10.0", "0.9.0", True),
    ("v0.1.0", "0.1.0", False), ("v0.1.0", "0.2.0", False),
])
def test_version_comparison(tag, current, newer):
    message, url = updates.release_notice(tag, current)
    assert bool(url) == newer
    assert current in message


@pytest.mark.parametrize("tag", [None, 2, "v0.2.0-rc1", "v0.2", "https://evil.example", "v1.2.3/other"])
def test_invalid_release_versions(tag):
    with pytest.raises(ValueError):
        updates.release_notice(tag)


def test_check_is_async_bounded_and_uses_fixed_public_endpoint(checker, qapp):
    checker.check()
    request = checker.manager.requests[0]
    assert request.url().toString() == updates.API_URL
    assert request.transferTimeout() == 10000
    assert {b"accept", b"user-agent"} <= {bytes(name).lower() for name in request.rawHeaderList()}
    assert request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute) == QNetworkRequest.RedirectPolicy.SameOriginRedirectPolicy
    assert checker.reply.limit == updates.MAX_RESPONSE + 1
    # The request has not finished; the GUI event loop and another check still work.
    QTest.qWait(1)
    checker.check(manual=True)
    assert len(checker.manager.requests) == 1
    assert checker.reply is not None and "Checking" in checker.notices[-1][0]
    checker.reply.deliver(payload())
    assert checker.reply is None and not checker.timer.isActive()
    assert checker.notices[-1][1] == updates.RELEASES_URL + "/tag/v0.2.0"
    checker.check()
    assert len(checker.manager.requests) == 1  # Cached notice, no new request.
    assert checker.notices[-1][1]
    checker.check(manual=True)
    assert len(checker.manager.requests) == 2


def test_disabled_checks_manual_override_and_cancel(checker):
    checker.set_enabled(False)
    checker.check()
    assert not checker.manager.requests
    checker.check(manual=True)
    reply = checker.reply
    checker.set_enabled(False)
    assert reply.aborted and checker.reply is None
    assert "Could not check" in checker.notices[-1][0]
    checker.set_enabled(True)
    checker.settings.setValue("updates/lastAttempt", 0)
    checker.check()
    checker.timer.timeout.emit()
    assert checker.manager.reply.aborted


def test_daily_retry_and_clock_change(checker):
    checker.check()
    checker.reply.status = 404
    checker.reply.deliver(b"")
    assert "No published release" in checker.notices[-1][0]
    checker.check()
    assert len(checker.manager.requests) == 1
    checker.clock = lambda: 200000
    checker.check()
    assert len(checker.manager.requests) == 2
    checker.reply.deliver(payload())
    checker.clock = lambda: 100000
    checker.check()
    assert len(checker.manager.requests) == 3  # A backward clock cannot defer forever.


@pytest.mark.parametrize("body", [b"not JSON", b"[]", b"null", payload("bad"),
    b'{"tag_name":"v1.0.0","draft":true,"prerelease":false}',
    b'{"tag_name":"v1.0.0","draft":false,"prerelease":true}', b"x" * (updates.MAX_RESPONSE + 1)])
def test_bad_release_metadata_never_offers_link(checker, body):
    checker.check()
    checker.reply.deliver(body)
    assert not checker.notices[-1][1]
    assert "Could not" in checker.notices[-1][0]


def test_corrupt_cache_is_discarded(checker):
    checker.settings.setValue("updates/lastAttempt", 100000)
    checker.settings.setValue("updates/latestTag", "bad")
    checker.check()
    assert not checker.settings.contains("updates/latestTag")
    assert not checker.manager.requests


def test_settings_controls_and_update_banner(overlay, qapp, monkeypatch):
    page = overlay.settings_page
    calls = []
    monkeypatch.setattr(page.update_checker, "check", lambda **kwargs: calls.append(kwargs))
    page.check_updates.click()
    assert calls == [{"manual": True}]
    page.automatic_updates.setChecked(False)
    assert not page.update_checker.enabled()
    page.update_checker.checked.emit(*updates.release_notice("v0.2.0"))
    assert not page.release_button.isHidden() and not overlay.update_banner.isHidden()
    overlay.update_banner.click()
    assert overlay.pages.currentIndex() == 1
    opened = []
    monkeypatch.setattr(settings_ui.QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    page.release_button.click()
    assert opened == [updates.RELEASES_URL + "/tag/v0.2.0"]
    monkeypatch.setattr(settings_ui.QDesktopServices, "openUrl", lambda url: False)
    page.release_button.click()
    assert "Could not open" in page.update_status.text()
    page.update_checker.checked.emit("Up to date", "")
    assert page.release_button.isHidden() and overlay.update_banner.isHidden()
    page.open_release()
    assert len(opened) == 1
