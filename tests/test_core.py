import asyncio
from dbus_next import Message, MessageType
from kde_shortcuts.model import Shortcut, category, normalize, deduplicate
from kde_shortcuts.search import search
from kde_shortcuts.discovery import discover


def row(component="kwin", action="Maximize", keys=("Meta+Up",)):
    return Shortcut(component, action, component, action, keys, category(component, action))


def test_normalization():
    assert normalize([[[0x10000000 + 75]], [[0x10000000 + 75]], [[0]]]) == ("Meta+K",)
    assert normalize([[[0x04000000 + 75, 0x04000000 + 67]]]) == ("Ctrl+K, Ctrl+C",)
    assert normalize([[[0x04000000 + 43]]]) == ("Ctrl++",)


def test_categories():
    assert category("kwin", "Switch to Desktop 2") == "Desktops & Activities"
    assert category("kwin", "Window Maximize") == "Windows"
    assert category("unknown", "Launch") == "Applications"


def test_search():
    rows = [row(), row("kmix", "Volume Up", ("Volume Up",))]
    assert search(rows, "mXiZe") == [rows[0]]
    assert search(rows, "audio volume") == [rows[1]]
    assert search(rows, "META UP") == [rows[0]]
    assert search(rows, "xyzxyz") == []
    assert len(search(rows, "")) == 2


def test_duplicates():
    assert deduplicate([row(), row(keys=("Alt+F10",))])[0].keys == ("Meta+Up", "Alt+F10")
    assert len(deduplicate([row(), row("other")])) == 2


class FakeBus:
    def __init__(self, fail=None):
        self.fail = fail
        self.disconnected = False

    async def connect(self):
        return self

    async def call(self, message):
        if message.member == self.fail:
            return Message.new_error(message_with_serial(message), "org.test.Unavailable", "Unavailable")
        data = {"allMainComponents": [["kwin", "KWin", "", ""]],
                "allActionsForComponent": [["kwin", "Window Maximize", "KWin", "Maximize"]],
                "shortcutKeys": [[[0x10000000 + 75]]]}
        return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1,
                       signature="a(ai)" if message.member == "shortcutKeys" else "aas",
                       body=[data[message.member]])

    def disconnect(self):
        self.disconnected = True


def message_with_serial(message):
    message.serial = 1
    return message


def test_discovery_and_errors():
    bus = FakeBus()
    result = asyncio.run(discover(lambda: bus))
    assert result.rows[0].keys == ("Meta+K",)
    assert not result.errors
    assert bus.disconnected
    for member in ("allMainComponents", "allActionsForComponent", "shortcutKeys"):
        result = asyncio.run(discover(lambda: FakeBus(member)))
        assert not result.rows
        assert result.errors


def test_missing_bus():
    def unavailable():
        raise OSError("No session bus")
    result = asyncio.run(discover(unavailable))
    assert not result.rows
    assert "No session bus" in result.errors[0]


def test_cancelled_discovery():
    bus = FakeBus()
    result = asyncio.run(discover(lambda: bus, cancelled=lambda: True))
    assert not result.rows
    assert not result.errors
    assert bus.disconnected


def test_normalization_rejects_malformed_sequences():
    import pytest
    with pytest.raises(ValueError, match="four strokes"):
        normalize([[[1, 2, 3, 4, 5]]])
    with pytest.raises(ValueError, match="struct"):
        normalize([[]])
    assert normalize([]) == ()


def test_unicode_and_multiple_search_tokens():
    from kde_shortcuts.search import score
    assert score("STRASSE", "Straße") == 0
    assert score("  ", "anything") == 0
    assert score("a a", "a") == 0
    assert score("ac", "abc") is not None
    assert search([], "anything") == []
