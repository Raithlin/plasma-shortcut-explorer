#!/bin/sh
set -eu
pacman -Syu --noconfirm --needed base-devel python-build python-installer \
    python-setuptools python-wheel python-pytest python-coverage python-dbus-next \
    pyside6 qt6-wayland kglobalacceld
useradd -m builder
python scripts/prepare_arch.py "$KDE_SHORTCUTS_SOURCE" --output /build
chown -R builder:builder /build
runuser -u builder -- sh -eu -c 'cd /build; makepkg --noconfirm; makepkg --printsrcinfo > .SRCINFO'
pacman -U --noconfirm /build/*.pkg.tar.zst
sh scripts/check_installed.sh
pacman -R --noconfirm plasma-shortcut-explorer
test ! -e /usr/bin/plasma-shortcut-explorer
cp /build/*.pkg.tar.zst /build/PKGBUILD /build/.SRCINFO /out/
