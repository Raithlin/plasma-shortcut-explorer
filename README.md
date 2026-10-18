# Plasma Shortcut Explorer

A small Python/Qt overlay showing **your configured KDE global shortcuts**.
Search action names, apps, categories, and key combinations. No default shortcut
list, config-file edits, X11 tools, or automatic shortcut registration.

## Development

A Plasma 6 session and a running user session bus are required for live results.
Native packaging targets current Arch/EndeavourOS, Debian 13, and Fedora 44;
see [RELEASES.md](RELEASES.md) for validation status. Install Python and the normal Qt Wayland runtime through your package
manager if absent. Then:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/plasma-shortcut-explorer
.venv/bin/plasma-shortcut-explorer --diagnose
KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/test.sh -q
```

PySide6 Essentials (Qt Widgets) and dbus-next are the only direct Python runtime dependencies. Discovery runs in
a worker; the UI remains responsive. Diagnostics emit JSON and return nonzero
for partial or complete discovery failures. No session bus means an explanatory
empty/error state, never fabricated defaults.

The test runner creates a private D-Bus session and uses Qt offscreen. It enforces
**95% line and 95% branch coverage separately**, including the UI and lifecycle.
For a coverage report run `.venv/bin/python -m coverage html` and open
`htmlcov/index.html`. Tests require `dbus-run-session` (Arch: `dbus`; Debian/Fedora:
`dbus-daemon`). Plain pytest skips the private-bus integration test unless launched
through the test runner.

## User installation

From this checkout, run `./scripts/install.sh`. It builds a dedicated environment
under `${XDG_DATA_HOME:-~/.local/share}/plasma-shortcut-explorer/venv`, installs a
launcher in `~/.local/bin`, and adds a desktop entry and icon. No root needed.
The desktop entry uses an absolute executable path. Re-run the script to update.

The primary command is `plasma-shortcut-explorer`; `kde-shortcuts` remains a
compatibility alias. The desktop ID stays `org.kde.shortcutexplorer`, so existing
Plasma shortcut assignments continue to refer to the same application. If you
installed the prototype under `~/.local/share/kde-shortcut-explorer`, that old
environment is not removed automatically by the renamed installer.

## Assign Meta+K

1. Open **System Settings → Keyboard → Shortcuts**.
2. Use **Add New → Application** (wording may vary), select **Plasma Shortcut Explorer**.
3. Add **Meta+K** as its launch shortcut and apply.
4. If Plasma reports a conflict, choose another combination or explicitly reassign
   it yourself. The app never overrides an existing binding.

Launching opens the overlay and focuses search. Type to filter; use Up/Down to
navigate, Escape to close, or switch focus to dismiss. Refresh re-reads bindings.
No autostart required. Repeated launches while an instance is open are ignored.

## Settings and appearance

Open **Settings**, press **Ctrl+,**, use the desktop entry's Settings action, or run
`plasma-shortcut-explorer --settings`. The page shows the opening shortcut found
for this application and opens Plasma's native Shortcuts editor to change it.
Plasma handles assignment and conflicts; the explorer does not write bindings.
Existing custom command shortcuts may not be identifiable as this app's launcher.
Reopen or refresh the explorer after changing a binding in Plasma.

The app follows Qt's system palette and widget style. It has no theme selector,
custom color palette, or forced Breeze/Fusion style. Colors and style are managed
in Plasma's System Settings. Native distro packages use the distro Qt integration;
bundled Python/Qt builds may use Fusion while still picking up system light/dark
colors. This was observed in the development Wayland environment. Changing the
system theme should update the app without restarting it.

The explorer is a reference, not a command launcher. Selecting a listed action
never executes it. Clicking a row or navigating with arrow keys shows its details.
**Edit in Plasma…** opens the owning component in Plasma’s Shortcuts editor; find
the named action there. KDE does not expose individual action selection. Component
names containing spaces open the full Shortcuts page instead.

### Wayland placement

Qt requests centering on the pointer's screen, but KWin decides placement. For
consistent placement use **System Settings → Window Management → Window Rules**:
add a rule matching the Plasma Shortcut Explorer window (use Detect Window Properties),
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

## Releases and packaging

[RELEASES.md](RELEASES.md) describes native package builds, the candidate AppImage
builder, release checks, and what remains before public distribution. The GitHub
workflows are prepared locally; nothing has been published.

## Uninstall

Remove the Meta+K entry you created in System Settings first. Then:

```sh
base="${XDG_DATA_HOME:-$HOME/.local/share}"
rm -f "$HOME/.local/bin/plasma-shortcut-explorer"
rm -f "$HOME/.local/bin/kde-shortcuts"
rm -f "$base/applications/org.kde.shortcutexplorer.desktop"
rm -f "$base/icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg"
rm -f "$base/metainfo/org.kde.shortcutexplorer.metainfo.xml"
rm -rf "$base/plasma-shortcut-explorer"
```

Remove any window rule you added. The utility stores no shortcut configuration.

MIT licensed.
