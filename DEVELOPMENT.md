# Development

Use this guide to run the app from source, inspect shortcut discovery, and test
changes. For a user installation, follow [INSTALL.md](INSTALL.md).

## Set up the environment

Install Python 3.11+ and the Qt Wayland runtime through your package manager.
From the project root, run:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install --no-deps -e .
```

The virtual environment contains the app and its test dependencies. The runtime
Python dependencies are PySide6 Essentials and `dbus-next`.

## Run the app

In a Plasma 6 session, run:

```sh
.venv/bin/plasma-shortcut-explorer
```

The overlay opens with search focused. The VS Code launch configuration runs
the same Python module from the workspace environment.

## Inspect shortcut discovery

Run diagnostics without opening the overlay:

```sh
.venv/bin/plasma-shortcut-explorer --diagnose
```

The command prints JSON with `rows` and `errors`. It returns 0 when discovery
completes without errors and 1 for partial or complete failure. It requires a
live KGlobalAccel service for real results.

## Run the tests

Install `dbus-run-session` through `dbus` on Arch or `dbus-daemon` on
Debian/Fedora. Then run:

```sh
KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/test.sh -q
```

The runner starts a private D-Bus session, runs pytest with Qt's offscreen
backend, and reports coverage. Both line and branch coverage must reach 95%.
All application modules count toward those thresholds. Plain pytest skips the
private-bus integration test.

To inspect coverage in a browser, run:

```sh
.venv/bin/python -m coverage html
```

Open `htmlcov/index.html` for the report. The test runner also writes
`coverage.json`.

Tests cover discovery failures, key sequences, search, UI interaction, lifecycle,
update checks, release publication order, and uninstall behavior. Update tests
use controlled replies; uninstall tests use temporary homes. The mock
KGlobalAccel service runs only on the private test bus.

## Check the real desktop

Automated tests do not cover KWin's activation and placement decisions. In a
Plasma session, check launching from a user-assigned shortcut, Escape,
focus-loss dismissal, refresh after changing a binding, light/dark appearance,
and placement on each monitor.

The standalone smoke check exercises rendering, search, errors, and shutdown:

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python tests/smoke_ui.py
```

It exits successfully and saves `/tmp/plasma-shortcut-explorer-smoke.png`.
Set `QT_QPA_PLATFORM=wayland` to run it against a live Wayland session.

## Change the code

Read [AGENTS.md](AGENTS.md) for repository guidance and [DESIGN.md](DESIGN.md)
for the architecture. Keep shortcut discovery read-only and show failures
instead of substituting default bindings. Never run the mock service on the
user's desktop bus.

Use disposable containers for native package builds. [RELEASES.md](RELEASES.md)
explains the build scripts, version checks, and automatic release workflow.
