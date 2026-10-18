# Changelog

## Unreleased

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
