"""Real wire-format test, only on an explicitly supplied isolated session bus."""
import asyncio
import os

import pytest
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

from kde_shortcuts.discovery import discover, INTERFACE, PATH, SERVICE


@pytest.mark.skipif(not os.environ.get("KDE_SHORTCUTS_TEST_BUS"), reason="Run scripts/test.sh under dbus-run-session")
def test_discovery_over_private_dbus():
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
        address = os.environ["KDE_SHORTCUTS_TEST_BUS"]
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
