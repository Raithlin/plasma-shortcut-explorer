# Design

Plasma Shortcut Explorer reads current KGlobalAccel bindings and displays them
in an on-demand Qt overlay. It leaves shortcut assignment to Plasma's editor.

## Modules

| Module | Responsibility |
| --- | --- |
| `app.py` | CLI modes, single-instance lock, and application lifecycle |
| `discovery.py` | Async D-Bus reads, timeouts, partial results, and connection cleanup |
| `model.py` | Shortcut records, key-sequence decoding, categories, and deduplication |
| `search.py` | Case-insensitive token and subsequence matching |
| `ui.py` | Overlay, category tree, search, selection details, and dismissal |
| `settings_ui.py` | Launch-shortcut settings and update controls |
| `integration.py` | Open Plasma's Shortcuts module |
| `updates.py` | Async GitHub checks, version comparison, and cached results |
| `config.py` | Window dimensions and desktop identity |

## Read current bindings

Discovery calls `org.kde.KGlobalAccel` at `/kglobalaccel` on the user session bus:

| Method | Input | Output | Result |
| --- | --- | --- | --- |
| `allMainComponents` | none | `aas` | Component identities |
| `allActionsForComponent` | `as` | `aas` | Action identities and translated labels |
| `shortcutKeys` | `as` | `a(ai)` | Assigned key sequences, including alternatives and multiple strokes |

An action identity contains the component ID, action ID, component label, and
action label. Discovery validates reply signatures and four-field identities.
It omits unassigned actions and deduplicates by component/action identity.
Actions that share a key combination remain separate entries.

The component interface also exposes context information. Its legacy integer
arrays do not fully represent multiple strokes, so discovery uses the root
`shortcutKeys` method. The root API reports the daemon's selected contexts;
the app does not enumerate other contexts independently.

The app reads neither default bindings nor `kglobalshortcutsrc`. Registered
actions may remain after their application stops, so a listed binding does not
prove that a handler is running. Application-local shortcuts and bindings
managed outside KGlobalAccel fall outside this API.

Discovery runs in a QThread. A five-second timeout bounds connection setup and
each request, while a 20-second overall deadline bounds the full scan. A failed
action or component leaves other results available and adds a diagnostic. The
overall deadline also preserves results already collected. Refresh and each
launch read the service again; the app does not persist shortcut results.

## Launch and close

Plasma launches the installed desktop entry through a user-assigned shortcut.
The app needs no tray icon or autostart process. A runtime lock prevents a second
instance from opening another overlay.

Escape and focus loss hide the window and request discovery cancellation. The
process waits for the worker to finish before quitting; an in-flight D-Bus call
may take up to its timeout. Closing also cancels an update request.

Qt requests centering on the pointer's screen. KWin controls final Wayland
placement, so users can add a [window rule](INSTALL.md#window-placement).

## Select and edit

Mouse or keyboard selection shows the action, application, category, and
assigned keys. It does not execute the action or open another window.

**Edit in Plasma…** opens `kcm_keys` using `systemsettings`, with `kcmshell6` as
a fallback. Plasma 6.8 accepts a component argument but has no individual-action
argument. Both frontends split module arguments on spaces, so component names
containing spaces open the general page. Launch failures appear inline.

Settings identifies the app's `_launch` action by its desktop ID. It does not
guess which unrelated custom command might launch the app. Plasma handles
assignments and conflicts. The desktop ID remains `org.kde.shortcutexplorer` so
existing assignments continue to work.

Qt's system palette and widget style control appearance. The app uses native
widget APIs for fonts, layout, and keycap frames. Native distro integration can
provide Breeze; the development pip environment used Fusion with a dark palette.

## Check for updates

After showing the window, `app.main` schedules a Qt Network request independently
of shortcut discovery. Automatic checks run at most once per day, including
failed attempts. Manual checks bypass that interval.

A ten-second deadline and transfer timeout bound the request. Responses have a
64 KiB limit. The checker compares stable three-part versions numerically and
constructs release links from the fixed upstream repository. It ignores remote
HTML and never installs an update. Only one request can run at a time.

QSettings stores the automatic-check preference, last attempt, and cached release
tag. The request sends the app version in its user agent, without shortcut data
or credentials. Failures leave shortcut browsing available.

## Verified interfaces

Live checks on EndeavourOS used Plasma 6.8, KGlobalAccel 6.31, and Qt/PySide6 6.12
under Wayland. An initial read returned 21 components and 168 KWin actions.
Full discovery returned 124 assigned actions with no errors in 0.172 seconds;
a later read took 0.181 seconds. These timings measure discovery, not total
Python/Qt startup. Offscreen and live Wayland UI smoke checks passed.

The installed XML files are
`/usr/share/dbus-1/interfaces/kf6_org.kde.KGlobalAccel.xml` and
`/usr/share/dbus-1/interfaces/kf6_org.kde.kglobalaccel.Component.xml`.
The discovery methods also exist in the
[KGlobalAccel 6.0.0 interface](https://github.com/KDE/kglobalaccel/blob/v6.0.0/src/org.kde.KGlobalAccel.xml).
For API details, see the [KDE interface](https://github.com/KDE/kglobalaccel/blob/master/src/org.kde.KGlobalAccel.xml)
and [KGlobalAccel API](https://api.kde.org/kglobalaccel.html).

Component selection follows KDE's Plasma 6.8 implementations in
[`kcm_keys.cpp`](https://github.com/KDE/plasma-desktop/blob/Plasma/6.8/kcms/keys/kcm_keys.cpp)
and [`main.cpp`](https://github.com/KDE/systemsettings/blob/Plasma/6.8/app/main.cpp).
The on-demand lifecycle also follows [KDE's status guidance](https://develop.kde.org/hig/status_changes/).

See [DEVELOPMENT.md](DEVELOPMENT.md) for tests and [RELEASES.md](RELEASES.md)
for package validation.
