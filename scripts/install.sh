#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
base="${XDG_DATA_HOME:-$HOME/.local/share}"
venv="$base/plasma-shortcut-explorer/venv"
python3 -m venv "$venv"
"$venv/bin/pip" install .
mkdir -p "$HOME/.local/bin" "$base/applications" "$base/icons/hicolor/scalable/apps" "$base/metainfo"
ln -sf "$venv/bin/plasma-shortcut-explorer" "$HOME/.local/bin/plasma-shortcut-explorer"
ln -sf "$venv/bin/kde-shortcuts" "$HOME/.local/bin/kde-shortcuts"
# Absolute executable also works when ~/.local/bin is absent from Plasma's PATH.
sed "s|^Exec=plasma-shortcut-explorer|Exec=\"$venv/bin/plasma-shortcut-explorer\"|" data/org.kde.shortcutexplorer.desktop > "$base/applications/org.kde.shortcutexplorer.desktop"
cp data/org.kde.shortcutexplorer.svg "$base/icons/hicolor/scalable/apps/"
cp data/org.kde.shortcutexplorer.metainfo.xml "$base/metainfo/"
printf 'Installed. Assign Meta+K in System Settings → Keyboard → Shortcuts.\n'
