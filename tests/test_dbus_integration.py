"""Real wire-format test on a bus created solely for this test."""
import asyncio
import os
import select
import subprocess

import pytest
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

from kde_shortcuts.discovery import discover, INTERFACE, PATH, SERVICE


@pytest.fixture
def private_bus(tmp_path):
    daemon = subprocess.Popen(
        ["dbus-daemon", "--session", "--nofork", "--print-address=1",
         f"--address=unix:dir={tmp_path}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        readable, _, _ = select.select([daemon.stdout], [], [], 5)
        if not readable:
            raise RuntimeError("Private test D-Bus daemon did not start")
        address = daemon.stdout.readline().strip()
        if not address.startswith("unix:"):
            raise RuntimeError("Private test D-Bus daemon returned no address")
        assert address != os.environ.get("DBUS_SESSION_BUS_ADDRESS")
        yield address
    finally:
        daemon.terminate()
        try:
            daemon.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            daemon.kill()
            daemon.communicate()


def test_discovery_over_private_dbus(private_bus):
    class Registry(ServiceInterface):
        def __init__(self):
            super().__init__(INTERFACE)
            self.calls = []

        @method()
        def allMainComponents(self) -> 'aas':
            self.calls.append("components")
            return [["example", "Example", "", ""]]

        @method()
        def allActionsForComponent(self, identity: 'as') -> 'aas':
            assert identity == ["example", "Example", "", ""]
            self.calls.append("actions")
            return [["example", "open", "Example", "Open"]]

        @method()
        def shortcutKeys(self, identity: 'as') -> 'a(ai)':
            assert identity == ["example", "open", "Example", "Open"]
            self.calls.append("keys")
            return [[[0x10000000 + 75, 0, 0, 0]], [[0x04000000 + 75, 0x04000000 + 67, 0, 0]]]

    async def check():
        address = private_bus
        service = await MessageBus(bus_address=address).connect()
        registry = Registry()
        service.export(PATH, registry)
        await service.request_name(SERVICE)
        try:
            result = await discover(lambda: MessageBus(bus_address=address))
            assert not result.errors
            assert result.rows[0].keys == ("Meta+K", "Ctrl+K, Ctrl+C")
            assert registry.calls == ["components", "actions", "keys"]
        finally:
            service.disconnect()
            await service.wait_for_disconnect()
    asyncio.run(check())
