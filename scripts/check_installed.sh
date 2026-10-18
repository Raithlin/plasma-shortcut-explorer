#!/bin/sh
# Called inside a package-test container, with no KDE session service running.
set -eu
test -x /usr/bin/plasma-shortcut-explorer
test ! -e /usr/bin/kde-shortcuts
test -f /usr/share/applications/org.kde.shortcutexplorer.desktop
test -f /usr/share/icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg
test -f /usr/share/metainfo/org.kde.shortcutexplorer.metainfo.xml
set +e
plasma-shortcut-explorer --diagnose > /tmp/plasma-shortcut-explorer-package-diagnostics.json
status=$?
set -e
test "$status" -eq 1
python3 - <<'PY'
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QNetworkAccessManager
with open('/tmp/plasma-shortcut-explorer-package-diagnostics.json') as stream:
    result = json.load(stream)
assert not result['rows'] and result['errors'], result
PY
