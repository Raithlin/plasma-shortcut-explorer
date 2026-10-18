# Development guidance

Keep discovery read-only. Never use defaultShortcut/defaultShortcutKeys as live bindings,
and never modify KDE shortcut files or register bindings without explicit user permission.
Use the installed KDE 6 D-Bus XML and live introspection to verify API changes.
Keep normalization, categorization, search, UI, and lifecycle separate.
Run `.venv/bin/pytest` and `QT_QPA_PLATFORM=offscreen .venv/bin/python` for UI checks.
Real Wayland activation and placement require a Plasma session; record limitations honestly.
Do not add X11 tools or silently fall back to a static shortcut list.
