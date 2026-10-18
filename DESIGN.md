# KDE Plasma Shortcut Explorer design

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

Qt QShortcut is window-local and cannot register Meta+K on Wayland. Use Plasma's
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

Still manual: user-assigned Meta+K launch, conflict resolution in System Settings,
focus-loss behavior during normal desktop use, and multi-monitor KWin rule placement.
The 0.172-second figure measures discovery, not total Python/Qt cold-start latency.
