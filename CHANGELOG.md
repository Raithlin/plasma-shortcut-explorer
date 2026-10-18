# Changelog

## Unreleased

- Add a per-user uninstaller with dry-run and preference-purge options; save a
  standalone copy during installation.
- Remove the `kde-shortcuts` command alias; use `plasma-shortcut-explorer`.
- Guide users to choose a memorable launch shortcut; Meta+K is only a suggestion.
- Check for newer stable GitHub releases asynchronously, with daily automatic
  checks, a Settings opt-out, manual checks, and release download links.
- Publish tagged releases automatically after tests, coverage, and native
  package builds pass; upload every asset before making the release public.
- Add Settings with the current opening shortcut, a handoff to Plasma’s native
  shortcut editor, Ctrl+comma, --settings, and a desktop Settings action.
- Follow Qt’s system appearance without custom palettes or a theme selector.

- Name the app Plasma Shortcut Explorer and use Raithlin/plasma-shortcut-explorer
  for the intended repository. Retain the desktop ID.

- Read current global shortcuts from KDE's KGlobalAccel service.
- Search categorized actions and key combinations in a Qt overlay.
- Add deterministic lifecycle, UI, failure-path, and private D-Bus integration tests.
- Enforce at least 95% line and 95% branch coverage independently.
- Add native package recipes and a draft release pipeline.
- Preserve existing bindings and the development application identity.
