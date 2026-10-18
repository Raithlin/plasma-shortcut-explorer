# Plasma Shortcut Explorer

A small Python/Qt overlay showing **your configured KDE global shortcuts**.
Search action names, apps, categories, and key combinations. No default shortcut
list, config-file edits, X11 tools, or automatic shortcut registration.

## Requirements and compatibility

This application is for **KDE Plasma 6 on Linux**. GNOME, other desktops, and
Plasma 5 are not supported. It reads Plasma's KGlobalAccel service; installing
Qt alone does not provide the shortcut data.

| Component | Requirement |
| --- | --- |
| Desktop | Plasma 6.0 or newer is the API baseline; see tested versions below |
| Shortcut service | KDE 6 KGlobalAccel daemon (`kglobalacceld`), running in your desktop session |
| Session bus | A working user D-Bus session with `org.kde.kglobalaccel` available |
| Python | 3.11 or newer for source installs and native packages |
| Python Qt bindings | PySide6 Essentials 6.6 or newer, below 7, providing Qt Widgets and Qt Network; distro packages may split the modules differently |
| D-Bus bindings | `dbus-next` 0.2.3 or newer, below 0.3 |
| Wayland runtime | The matching Qt 6 Wayland platform plugin and its system libraries |
| Shortcut editing | Plasma System Settings with the Shortcuts module (`kcm_keys`); `kcmshell6` can also open it |

**Minimum API version is not a fully tested minimum desktop version.** The three
discovery methods are present in the
[KGlobalAccel 6.0.0 interface](https://github.com/KDE/kglobalaccel/blob/v6.0.0/src/org.kde.KGlobalAccel.xml).
Live discovery and GUI smoke checks have been performed on **Plasma 6.8,
KGlobalAccel/Frameworks 6.31, and Qt/PySide6 6.12**, on EndeavourOS with Wayland.
Older Plasma 6 releases still need live validation. X11 sessions have not been
validated; Wayland activation and monitor placement also need the manual checks
described below. A native package build passing in a container does not establish
that the desktop UI works on that distribution.

Native packaging currently targets rolling Arch/EndeavourOS, Debian 13, and
Fedora 44. These are build targets, not a claim of compatibility with every
Debian/Ubuntu or Fedora release. See [RELEASES.md](RELEASES.md) for package
validation status. Package managers install the declared runtime dependencies;
source installations also need the system Qt platform libraries. System Settings
is optional for browsing, but required for the editing handoff unless
`kcmshell6` and the Shortcuts module are available.

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

### Update checks

After the window opens, the app checks GitHub's public latest-release endpoint
asynchronously, at most once every 24 hours. Shortcut discovery and navigation
do not wait for the request. A newer stable version shows a button leading to
Settings and the release downloads. Settings shows the installed version and
provides **Check now** and an option to disable automatic checks. Preferences
and the last release result are stored using Qt's normal user settings.

Checks send no shortcut data or credentials; GitHub receives a normal HTTPS
request with the app version in its user agent. Requests have a ten-second
deadline. Failed checks leave shortcut browsing available; use Check now to
retry. Before the first release, the app reports that none is published yet.
Checks offer downloads, not in-place installation. Update native packages using
your package manager; the explorer does not replace package-managed files.

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
workflows are available in the repository. Pushing a matching `vX.Y.Z` tag
automatically tests and builds the source archive, wheel, Debian, Fedora, and
Arch packages, uploads all assets and checksums to a draft, then publishes it
without an approval step. No downloadable release has been published yet.
Native package builds and the candidate AppImage are separate
from publishing apt/dnf update repositories or submitting a recipe to AUR.

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

## Development

Install Python and the normal Qt Wayland runtime through your package manager
if absent, then:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/plasma-shortcut-explorer
.venv/bin/plasma-shortcut-explorer --diagnose
KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/test.sh -q
```

PySide6 Essentials (Qt Widgets and Qt Network) and dbus-next are the only direct Python runtime dependencies. Discovery runs in
a worker; the UI remains responsive. Diagnostics emit JSON and return nonzero
for partial or complete discovery failures. No session bus means an explanatory
empty/error state, never fabricated defaults.

The test runner creates a private D-Bus session and uses Qt offscreen. It enforces
**95% line and 95% branch coverage separately**, including the UI and lifecycle.
For a coverage report run `.venv/bin/python -m coverage html` and open
`htmlcov/index.html`. Tests require `dbus-run-session` (Arch: `dbus`; Debian/Fedora:
`dbus-daemon`). Plain pytest skips the private-bus integration test unless launched
through the test runner.

MIT licensed.
