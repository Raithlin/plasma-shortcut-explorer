#!/bin/sh
# Run on the oldest supported build baseline, not a rolling-release host.
set -eu
cd "$(dirname "$0")/.."
: "${APPIMAGETOOL:?Set APPIMAGETOOL to a verified appimagetool executable}"
: "${APPIMAGE_RUNTIME:?Set APPIMAGE_RUNTIME to a verified type2 runtime file}"
python="${KDE_SHORTCUTS_PYTHON:-python3}"
version=$("$python" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
arch=$(uname -m)
mkdir -p build
appdir=$(mktemp -d "$PWD/build/AppDir.XXXXXX")
# PyInstaller handles Qt's platform and Wayland dependency hooks. Keep a directory
# bundle, so the AppImage doesn't unpack a second one-file archive on every launch.
"$python" -m PyInstaller --noconfirm --clean --onedir --name plasma-shortcut-explorer \
    --paths src --distpath build/frozen --workpath build/pyinstaller \
    --specpath build packaging/appimage/entry.py
mkdir -p "$appdir/usr/share/metainfo" "$appdir/usr/lib" "$appdir/usr/share/licenses/plasma-shortcut-explorer"
cp -a build/frozen/plasma-shortcut-explorer "$appdir/usr/lib/"
cp packaging/appimage/AppRun "$appdir/"
cp data/org.kde.shortcutexplorer.desktop "$appdir/"
cp data/org.kde.shortcutexplorer.svg "$appdir/"
cp LICENSE "$appdir/usr/share/licenses/plasma-shortcut-explorer/"
cp data/org.kde.shortcutexplorer.metainfo.xml "$appdir/usr/share/metainfo/"
# Ship the complete wheel notices, including Qt/PySide6 licensing material.
"$python" - "$appdir/usr/share/licenses/plasma-shortcut-explorer" <<'PY'
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys
for name in ("PySide6-Essentials", "shiboken6", "dbus-next", "pyinstaller"):
    dist = distribution(name)
    for file in dist.files or ():
        if any(word in str(file).lower() for word in ("license", "copying", "notice")):
            origin = Path(dist.locate_file(file))
            if origin.is_file():
                target = Path(sys.argv[1]) / name / file
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, target)
PY
if ! find "$appdir/usr/lib" -name 'libqwayland*.so' -print -quit | grep -q .; then
    printf 'Qt Wayland platform plugins were not bundled. Refusing to build.\n' >&2
    exit 1
fi
mkdir -p dist
ARCH="$arch" APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" \
    --runtime-file "$APPIMAGE_RUNTIME" "$appdir" \
    "dist/Plasma_Shortcut_Explorer-$version-$arch.AppImage"
