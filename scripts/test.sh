#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Never export a test KGlobalAccel service on the user's actual session bus.
if [ "${KDE_SHORTCUTS_ISOLATED_BUS:-}" != 1 ]; then
    exec dbus-run-session -- env KDE_SHORTCUTS_ISOLATED_BUS=1 "$0" "$@"
fi
export KDE_SHORTCUTS_TEST_BUS="$DBUS_SESSION_BUS_ADDRESS"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
python="${KDE_SHORTCUTS_PYTHON:-python3}"
"$python" -m coverage run -m pytest "$@"
"$python" -m coverage report
"$python" -m coverage json -o coverage.json
"$python" scripts/check_coverage.py coverage.json
