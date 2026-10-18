# Development guidance

Keep discovery read-only. Never use defaultShortcut/defaultShortcutKeys as live bindings,
and never modify KDE shortcut files or register bindings without explicit user permission.
Use the installed KDE 6 D-Bus XML and live introspection to verify API changes.
Keep normalization, categorization, search, UI, and lifecycle separate.
Run `KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/test.sh -q` for the complete suite.
Keep line and branch coverage at or above 95% independently; do not exclude application code.
The test KGlobalAccel service must only run on the explicitly isolated private bus.
Native package builds run inside disposable containers, never via pacman/apt/dnf on the host.
Read RELEASES.md before changing package recipes or release workflows.
Real Wayland activation and placement require a Plasma session; record limitations honestly.
Do not add X11 tools or silently fall back to a static shortcut list.
