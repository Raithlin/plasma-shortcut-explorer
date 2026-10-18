# Changelog

## Unreleased

- Add Settings with the current opening shortcut, a handoff to Plasma’s native
  shortcut editor, Ctrl+comma, --settings, and a desktop Settings action.
- Follow Qt’s system appearance without custom palettes or a theme selector.

- Name the app Plasma Shortcut Explorer and use Raithlin/plasma-shortcut-explorer
  for the intended repository. Retain the desktop ID and legacy command alias.

- Read current global shortcuts from KDE's KGlobalAccel service.
- Search categorized actions and key combinations in a Qt overlay.
- Add deterministic lifecycle, UI, failure-path, and private D-Bus integration tests.
- Enforce at least 95% line and 95% branch coverage independently.
- Add native package recipes and a draft release pipeline.
- Preserve existing bindings and the development application identity.
