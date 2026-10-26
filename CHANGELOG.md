# Changelog

## Unreleased

- Add keybind, keybindings, and hotkeys to application launcher search keywords.
- Add a window resize handle and adapt the results columns to the available space.
- Compact the selected-action hint and show configured totals when filtering shortcuts.

## 0.1.1 (2026-10-18)

- Bound shortcut discovery to 20 seconds and retain results collected before the deadline.
- Run the mock KGlobalAccel service only on a private D-Bus daemon, including when
  its integration test is invoked directly.
- Preserve current and legacy installation directories when their entry point is
  missing or the directory cannot be verified.
- Normalize the release metadata filename before generating checksums.

## 0.1.0 (2026-10-18)

- Read assigned global shortcuts from KDE's KGlobalAccel service.
- Search actions and key combinations in a categorized Qt overlay.
- Show details for the selected action and open its component in Plasma's editor.
- Add launch-shortcut settings through the Settings page, `Ctrl+,`, `--settings`,
  and a desktop action.
- Follow Qt's system appearance.
- Check asynchronously for stable GitHub releases. Add daily caching, manual
  checks, an opt-out, and release download links.
- Add a per-user installer and uninstaller with dry-run and preference-purge options.
- Name the app Plasma Shortcut Explorer and retain its desktop ID.
- Remove the `kde-shortcuts` alias; use `plasma-shortcut-explorer`.
- Let users choose a memorable launch shortcut, with Meta+K as one suggestion.
- Add native package recipes and automatic tagged-release publication.
- Test discovery, UI behavior, lifecycle, updates, uninstalling, and release failures.
- Require 95% line and 95% branch coverage across all application modules.
