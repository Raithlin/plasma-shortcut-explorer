"""Read current bindings; never read defaults or mutate KDE configuration."""
import asyncio
from dataclasses import dataclass, field
from dbus_next import Message, MessageType
from dbus_next.aio import MessageBus
from .model import Shortcut, category, normalize, deduplicate

SERVICE = "org.kde.kglobalaccel"
PATH = "/kglobalaccel"
INTERFACE = "org.kde.KGlobalAccel"


@dataclass
class Discovery:
    rows: list = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


async def discover(bus_factory=MessageBus, cancelled=lambda: False, timeout=5, overall_timeout=20):
    result = Discovery()
    bus = None
    try:
        async with asyncio.timeout(overall_timeout):
            bus = bus_factory()
            try:
                await asyncio.wait_for(bus.connect(), timeout)
            except TimeoutError as exc:
                raise RuntimeError(f"Session bus connection timed out after {timeout}s") from exc

            async def call(member, signature="", body=None):
                try:
                    reply = await asyncio.wait_for(bus.call(Message(destination=SERVICE, path=PATH,
                        interface=INTERFACE, member=member, signature=signature, body=body or [])), timeout)
                except TimeoutError as exc:
                    raise RuntimeError(f"{member}: D-Bus request timed out after {timeout}s") from exc
                if reply.message_type == MessageType.ERROR:
                    raise RuntimeError(f"{member}: {reply.error_name}: {reply.body}")
                expected = {"allMainComponents": "aas", "allActionsForComponent": "aas", "shortcutKeys": "a(ai)"}[member]
                if reply.signature != expected or len(reply.body) != 1:
                    raise ValueError(f"{member}: unexpected D-Bus reply signature {reply.signature!r}")
                return reply.body[0]

            components = await call("allMainComponents")
            for component in components:
                if cancelled():
                    break
                try:
                    if len(component) != 4:
                        raise ValueError("Expected a four-field component identity")
                    actions = await call("allActionsForComponent", "as", [component])
                    for action in actions:
                        if cancelled():
                            break
                        try:
                            if len(action) != 4:
                                raise ValueError("Expected a four-field action identity")
                            keys = normalize(await call("shortcutKeys", "as", [action]))
                            if keys:
                                result.rows.append(Shortcut(action[0], action[1], action[2] or action[0],
                                    action[3] or action[1], keys, category(action[0], action[1])))
                        except Exception as exc:
                            result.errors.append(f"{component!r}/{action!r}: {exc}")
                except Exception as exc:
                    result.errors.append(f"{component!r}: {exc}")
    except TimeoutError:
        result.errors.append(f"KDE shortcut discovery exceeded {overall_timeout}s overall")
    except Exception as exc:
        result.errors.append(f"KDE shortcut discovery unavailable: {exc}")
    finally:
        if bus is not None:
            bus.disconnect()
    result.rows = deduplicate(result.rows)
    return result
