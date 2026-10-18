from dataclasses import dataclass
from PySide6.QtGui import QKeySequence


@dataclass(frozen=True)
class Shortcut:
    component: str
    action_id: str
    application: str
    action: str
    keys: tuple[str, ...]
    category: str


def category(component: str, action: str) -> str:
    if component == "kwin":
        return "Desktops & Activities" if any(w in action.casefold() for w in ("desktop", "activity", "overview", "grid")) else "Windows"
    return {"kmix": "Audio & Media", "mediacontrol": "Audio & Media",
            "ksmserver": "Session & Power", "org_kde_powerdevil": "Session & Power",
            "ActivityManager": "Desktops & Activities", "plasmashell": "Plasma"}.get(component, "Applications")


def normalize(sequences) -> tuple[str, ...]:
    result = []
    for sequence in sequences:
        if len(sequence) != 1:
            raise ValueError("Expected a key sequence struct containing one integer array")
        values = [int(value) for value in sequence[0] if value]
        if not values:
            continue
        if len(values) > 4:
            raise ValueError("KDE returned a key sequence longer than four strokes")
        label = QKeySequence(*values).toString(QKeySequence.SequenceFormat.PortableText)
        if label and label not in result:
            result.append(label)
    return tuple(result)


def deduplicate(rows):
    result = {}
    for row in rows:
        identity = (row.component, row.action_id)
        old = result.get(identity)
        if old:
            row = Shortcut(row.component, row.action_id, row.application, row.action,
                           tuple(dict.fromkeys(old.keys + row.keys)), row.category)
        result[identity] = row
    return list(result.values())
