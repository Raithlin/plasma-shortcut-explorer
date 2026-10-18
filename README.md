# KDE Plasma Shortcut Explorer

A small Python/Qt overlay showing **your configured KDE global shortcuts**.
Search action names, apps, categories, and key combinations. No default shortcut
list, config-file edits, X11 tools, or automatic shortcut registration.

## Development

Arch/EndeavourOS with Plasma 6 and a running user session bus is required for live
results. Install Python and the normal Qt Wayland runtime through your package
manager if absent. Then:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/kde-shortcuts
.venv/bin/kde-shortcuts --diagnose
.venv/bin/pytest
```

PySide6 Essentials (Qt Widgets) and dbus-next are the only direct Python runtime dependencies. Discovery runs in
a worker; the UI remains responsive. Diagnostics emit JSON and return nonzero
for partial or complete discovery failures. No session bus means an explanatory
empty/error state, never fabricated defaults.

## User installation

From this checkout, run `./scripts/install.sh`. It builds a dedicated environment
under `${XDG_DATA_HOME:-~/.local/share}/kde-shortcut-explorer/venv`, installs a
launcher in `~/.local/bin`, and adds a desktop entry and icon. No root needed.
The desktop entry uses an absolute executable path. Re-run the script to update.

## Assign Meta+K

1. Open **System Settings → Keyboard → Shortcuts**.
2. Use **Add New → Application** (wording may vary), select **Shortcut Explorer**.
3. Add **Meta+K** as its launch shortcut and apply.
4. If Plasma reports a conflict, choose another combination or explicitly reassign
   it yourself. The app never overrides an existing binding.

Launching opens the overlay and focuses search. Type to filter; use Up/Down to
navigate, Escape to close, or switch focus to dismiss. Refresh re-reads bindings.
No autostart required. Repeated launches while an instance is open are ignored.

### Wayland placement

Qt requests centering on the pointer's screen, but KWin decides placement. For
consistent placement use **System Settings → Window Management → Window Rules**:
add a rule matching the Shortcut Explorer window (use Detect Window Properties),
set **Initial placement → Force → Centered**, and, if offered, **Screen → Apply
Initially → Active screen**. Test Meta+K from each monitor. Exact option labels
vary. Active-screen placement and focus activation need a real-session check;
application-side absolute positioning cannot guarantee them on Wayland.

## Coverage and limitations

Includes KWin, Plasma, registered application global actions, and KDE custom
application launch bindings. Does not include every application's local menu
shortcuts or shortcuts registered outside KGlobalAccel. Only assigned current
bindings are shown; alternate sequences appear separately. Non-default shortcut
contexts are not separately explored. Categories are heuristics. Changes appear
on Refresh or next launch. Errors are shown beneath the list (hover for all errors).
Use `--diagnose` when reporting problems. See [DESIGN.md](DESIGN.md) for verified APIs.

## Uninstall

Remove the Meta+K entry you created in System Settings first. Then:

```sh
base="${XDG_DATA_HOME:-$HOME/.local/share}"
rm -f "$HOME/.local/bin/kde-shortcuts"
rm -f "$base/applications/org.kde.shortcutexplorer.desktop"
rm -f "$base/icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg"
rm -rf "$base/kde-shortcut-explorer"
```

Remove any window rule you added. The utility stores no shortcut configuration.

MIT licensed.
