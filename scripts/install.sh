#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base="${XDG_DATA_HOME:-$HOME/.local/share}"
venv="$base/kde-shortcut-explorer/venv"
python3 -m venv "$venv"
"$venv/bin/pip" install .
mkdir -p "$HOME/.local/bin" "$base/applications" "$base/icons/hicolor/scalable/apps"
ln -sf "$venv/bin/kde-shortcuts" "$HOME/.local/bin/kde-shortcuts"
# Absolute executable also works when ~/.local/bin is absent from Plasma's PATH.
sed "s|^Exec=.*|Exec=\"$venv/bin/kde-shortcuts\"|" data/org.kde.shortcutexplorer.desktop > "$base/applications/org.kde.shortcutexplorer.desktop"
cp data/org.kde.shortcutexplorer.svg "$base/icons/hicolor/scalable/apps/"
printf 'Installed. Assign Meta+K in System Settings → Keyboard → Shortcuts.\n'
