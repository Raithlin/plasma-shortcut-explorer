# Plasma Shortcut Explorer design

## Phase 1: verified feasibility (2026-10-18)

This machine runs EndeavourOS, KDE on Wayland (`XDG_CURRENT_DESKTOP=KDE`,
`WAYLAND_DISPLAY=wayland-1`). Installed packages: plasma-workspace 6.8.0-1,
kwin 6.8.0-1, kglobalaccel 6.31.0-1. PySide6 was initially absent.

Read-only live `busctl --user introspect org.kde.kglobalaccel /kglobalaccel`
confirmed `org.kde.KGlobalAccel` methods:

| Method | Input | Output | Purpose |
|---|---|---|---|
| allMainComponents | none | aas | Component identities |
| allActionsForComponent | as | aas | Action identities and translated labels |
| shortcutKeys | as | a(ai) | Current alternatives, each containing sequence strokes |
| allComponents | none | ao | Component object paths |

`allMainComponents` returned 21 components, including kwin, kmix, plasmashell,
1Password, Dolphin, Konsole, and Floorp. `allActionsForComponent` returned 168
KWin actions. Action identities are [component ID, action ID, component label,
action label]. These are actual local observations, not assumptions from Plasma 5.

Installed XML sources:
`/usr/share/dbus-1/interfaces/kf6_org.kde.KGlobalAccel.xml` and
`/usr/share/dbus-1/interfaces/kf6_org.kde.kglobalaccel.Component.xml`.
The latter exposes context enumeration and shortcut info. Its legacy integer
arrays do not fully represent multi-stroke sequences, so use root `shortcutKeys`.
No `defaultShortcut*` calls are used. Unassigned actions are omitted.

Upstream references: [KDE interface](https://github.com/KDE/kglobalaccel/blob/master/src/org.kde.KGlobalAccel.xml),
[KGlobalAccel API](https://api.kde.org/kglobalaccel.html).

## Scope and limitations

The daemon exposes registered global actions, including KWin and application global
shortcuts and custom launchers registered with KDE. It cannot enumerate arbitrary
in-application menu shortcuts or shortcuts privately handled by another service.
Inactive/stale registered application actions may be present. This is a reference
to configured bindings, not proof that each action currently has a running handler.
Non-default shortcut contexts are not independently enumerated in the MVP; the
root API reports the daemon's selected action contexts. No config-file fallback:
partial errors are visible, and diagnostics include every failed call.

`kglobalshortcutsrc` is KDE's persistent configuration, but direct parsing loses
runtime state and sequence semantics. It is deliberately not read or written.

## Activation and placement

Qt QShortcut is window-local and cannot register a global launch key on Wayland. Use Plasma's
System Settings to assign the installed desktop application. Plasma launches it
on demand, supplies its ordinary activation mechanism, and warns about conflicts.
No autostart or daemon is necessary. This follows the [KDE status guidance](https://develop.kde.org/hig/status_changes/), which discourages unnecessary persistent tray icons. The application does not call mutating
KGlobalAccel methods or request an automatic binding.

Wayland compositors control top-level window positions. The UI requests centering
on the pointer screen with Qt, but KWin may ignore that request. A user-configured
KWin rule is the practical supported placement mechanism (README). Strict active
screen centering is therefore not guaranteed by the Python-only MVP. Focus and
activation must be validated on the actual compositor after assigning the shortcut.

## Architecture and plan

- `discovery.py`: dbus-next asynchronous low-level calls, five-second per-call timeout,
  partial failure diagnostics, bus cleanup. No introspection-dependent generated types.
- `model.py`: immutable records, Qt key sequence decoding, identity deduplication,
  deterministic component/action categorization. Shared combinations remain separate actions.
- `search.py`: case-insensitive token/subsequence matching across all displayed fields.
- `ui.py`: native Qt Widgets palette, category tree, keycap labels, instant search,
  arrows, Escape, focus-loss dismissal. A QThread keeps discovery off the GUI thread.
- `app.py`: command-line diagnostics and on-demand application lifecycle.
- `config.py`: UI dimensions and desktop identity.

Phase 2 implements read-only discovery and the searchable overlay. Phase 3 adds
navigation, packaging, automated tests, and setup guidance. Categories are heuristics
based on component IDs and action IDs, not translated labels. Discovery refreshes
on launch and on Refresh; there is no stale persisted cache. Closing cancels further enumeration; an in-flight D-Bus call may delay process
termination by its five-second timeout, protecting the worker thread.

Risks: API availability varies across Frameworks versions; errors must stay visible.
Sequential D-Bus calls trade simplicity for startup latency on very large registries.
Theme integration uses Qt's available platform theme; pip wheels may need local
Qt platform dependencies. A Qt runtime lock prevents simultaneous overlay instances. Package versions have bounded compatibility ranges, not a locked binary
environment; use the tested requirements snapshot for exact development versions.

## Validation results

- Seven automated tests passed on Python 3.14.4, PySide6 Essentials 6.12.0,
  dbus-next 0.2.3, and pytest 9.1.1.
- Full Python discovery against the live session returned **124 assigned actions
  in 0.172 seconds**, with zero discovery errors. No bindings were modified.
- Offscreen UI smoke check passed: render, search/no-match, keycaps, error state,
  and close. Keycap row height was corrected after inspecting the rendered image.
- The same UI smoke check passed using the real Qt Wayland backend in this session.
- A sandbox-blocked session bus produced an explicit diagnostic, with no crash or defaults.
- Installer shell syntax and desktop-entry validation passed; distributable wheel built.

Still manual: user-assigned shortcut launch, conflict resolution in System Settings,
focus-loss behavior during normal desktop use, and multi-monitor KWin rule placement.
The 0.172-second figure measures discovery, not total Python/Qt cold-start latency.

## Testing and release hardening

Discovery now validates D-Bus reply signatures and four-field identities, preserves
other results after malformed actions, and gives explicit connection/request timeout
errors. The session bus connection itself is bounded as well as method calls.
Shutdown connects worker completion before checking its running state, avoiding
losing the quit event if the worker finishes during dismissal.

The default test entry point is now `scripts/test.sh`, which creates a private
session bus and runs the headless Qt interaction suite, lifecycle tests, discovery
failure tests, and a real wire-format integration service. It enforces at least
95% line and 95% branch coverage independently without application exclusions.
This supersedes the initial seven-test validation snapshot above.

Native packaging and candidate AppImage tooling are documented in RELEASES.md.
Desktop assets are now part of the wheel as well as the source distribution.
No shortcuts, user KDE configuration, or application identity are changed by this
work. The org.kde development identity is retained for existing installations;
choose an owned public namespace and plan migration before the first public release.

## Settings and native appearance

The app now has a Settings page (button, Ctrl+comma, --settings, desktop action).
It displays a discovered `_launch` binding only when its component matches this
application's preserved desktop ID. It never guesses from an unrelated custom
command registration. The configuration button opens `systemsettings kcm_keys`,
with `kcmshell6 kcm_keys` as fallback. The command is verified in the locally
installed kcm_keys.desktop entry. Assignment and conflict resolution remain in
Plasma's native editor; no additional global shortcut registration is introduced.

Appearance belongs to the desktop. No app-specific theme preference, palette,
stylesheet, or forced widget style is used. Font/layout adjustments and keycap
frames use Qt widget APIs, preserving live palette changes. Tests cover both
light and dark palette changes on the same running widget tree. On this machine,
a read-only check of the real Wayland application reported Qt 6.12, Fusion style,
and a dark palette (window #202326, foreground #fcfcfc). Native distro integration
can provide Breeze; pip/AppImage Qt packaging must be checked separately.

See RELEASES.md for KDE's Python distribution guidance and our packaging choice.

## Selection and editing

Mouse and keyboard selection show action, application, category, assigned keys,
and guidance for finding the action in Plasma. Selection never executes actions
or opens external windows. An explicit Edit in Plasma button opens kcm_keys
with the component as --args. Plasma 6.8's KCM accepts a component identifier,
not an action identifier. System Settings splits module arguments on spaces, so
components containing spaces open the general page instead. Errors stay inline.

Verified against KDE's Plasma/6.8 sources:
- https://github.com/KDE/plasma-desktop/blob/Plasma/6.8/kcms/keys/kcm_keys.cpp
- https://github.com/KDE/systemsettings/blob/Plasma/6.8/app/main.cpp

## Asynchronous update discovery

Qt Network owns the HTTPS request; no blocking urllib call or network worker
thread is used. app.main schedules the check after showing the window, separately
from KGlobalAccel discovery. A ten-second total deadline and transfer timeout
bound requests. Responses are limited to 64 KiB; stable three-part version tags
are compared numerically. Release links are constructed from the fixed upstream
repository, never from remote HTML. A pending request cannot be duplicated and
is cancelled when the overlay closes. QSettings stores the automatic-check
preference, last attempt, and cached release tag. Tests use isolated settings
and controlled replies, without contacting GitHub or the real desktop service.
