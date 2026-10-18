#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Always create the private bus here; inherited flags and bus addresses are untrusted.
exec dbus-run-session -- sh -eu -c '
    unset KDE_SHORTCUTS_TEST_BUS KDE_SHORTCUTS_ISOLATED_BUS
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
    python="${KDE_SHORTCUTS_PYTHON:-python3}"
    "$python" -m coverage run -m pytest "$@"
    "$python" -m coverage report
    "$python" -m coverage json -o coverage.json
    "$python" scripts/check_coverage.py coverage.json
' sh "$@"
