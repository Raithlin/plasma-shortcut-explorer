import asyncio

import pytest
from dbus_next import Message, MessageType

from kde_shortcuts.discovery import discover

COMPONENT = ["example", "Example", "", ""]
ACTION = ["example", "open", "Example", "Open"]


class Bus:
    def __init__(self, components=None, actions=None, keys=None):
        self.components = [COMPONENT] if components is None else components
        self.actions = [ACTION] if actions is None else actions
        self.keys = [[[0x10000000 + 75]]] if keys is None else keys
        self.calls = []
        self.disconnected = False

    async def connect(self):
        return self

    async def call(self, message):
        self.calls.append(message)
        # Verify the actual request wire contract, not just method names.
        assert message.destination == "org.kde.kglobalaccel"
        assert message.path == "/kglobalaccel"
        assert message.interface == "org.kde.KGlobalAccel"
        if message.member == "allMainComponents":
            assert message.signature == "" and message.body == []
            signature, value = "aas", self.components
        elif message.member == "allActionsForComponent":
            assert message.signature == "as" and message.body == [COMPONENT]
            signature, value = "aas", self.actions
        else:
            assert message.member == "shortcutKeys"
            assert message.signature == "as" and len(message.body[0]) == 4
            signature, value = "a(ai)", self.keys
        return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1,
                       signature=signature, body=[value])

    def disconnect(self):
        self.disconnected = True


def test_unassigned_and_empty_registry():
    for bus in (Bus(keys=[]), Bus(keys=[[[0, 0, 0, 0]]]), Bus(components=[])):
        result = asyncio.run(discover(lambda: bus))
        assert not result.rows and not result.errors
        assert bus.disconnected


def test_fallback_labels_and_duplicates():
    bus = Bus(actions=[["example", "open", "", ""], ["example", "open", "", ""]])
    result = asyncio.run(discover(lambda: bus))
    assert len(result.rows) == 1
    assert result.rows[0].application == "example"
    assert result.rows[0].action == "open"


def test_malformed_action_keeps_other_actions():
    bus = Bus(actions=[[], ACTION])
    result = asyncio.run(discover(lambda: bus))
    assert len(result.rows) == len(result.errors) == 1
    assert "four-field action" in result.errors[0]


def test_malformed_component_keeps_other_components():
    bus = Bus(components=[[], COMPONENT])
    result = asyncio.run(discover(lambda: bus))
    assert len(result.rows) == len(result.errors) == 1
    assert "four-field component" in result.errors[0]


def test_bad_keys_are_reported():
    bus = Bus(keys=[[[1, 2, 3, 4, 5]]])
    result = asyncio.run(discover(lambda: bus))
    assert not result.rows
    assert "four strokes" in result.errors[0]


def test_cancel_between_actions():
    bus = Bus(actions=[ACTION, ["example", "second", "Example", "Second"]])
    result = asyncio.run(discover(lambda: bus, cancelled=lambda: len(bus.calls) >= 3))
    assert len(result.rows) == 1 and not result.errors
    assert len(bus.calls) == 3
    assert bus.disconnected


def test_connection_failure():
    class Unavailable(Bus):
        async def connect(self):
            raise ConnectionError("Session bus disconnected")
    result = asyncio.run(discover(Unavailable))
    assert not result.rows
    assert "Session bus disconnected" in result.errors[0]


def test_timeout_cleans_up():
    class Slow(Bus):
        async def call(self, message):
            await asyncio.sleep(10)
    bus = Slow()
    result = asyncio.run(discover(lambda: bus, timeout=0.01))
    assert not result.rows and "timed out" in result.errors[0]
    assert bus.disconnected


def test_connect_timeout_cleans_up():
    class SlowConnect(Bus):
        async def connect(self):
            await asyncio.sleep(10)
    bus = SlowConnect()
    result = asyncio.run(discover(lambda: bus, timeout=0.01))
    assert "Session bus connection timed out" in result.errors[0]
    assert bus.disconnected


def test_incompatible_reply():
    class Incompatible(Bus):
        async def call(self, message):
            return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1,
                           signature="s", body=["wrong shape"])
    result = asyncio.run(discover(Incompatible))
    assert "unexpected D-Bus reply signature" in result.errors[0]


@pytest.mark.parametrize("member", ["allMainComponents", "allActionsForComponent", "shortcutKeys"])
def test_missing_method(member):
    class Missing(Bus):
        async def call(self, message):
            if message.member == member:
                message.serial = 1
                return Message.new_error(message, "org.freedesktop.DBus.Error.UnknownMethod", member)
            return await super().call(message)
    result = asyncio.run(discover(Missing))
    assert not result.rows
    assert "UnknownMethod" in result.errors[0]
