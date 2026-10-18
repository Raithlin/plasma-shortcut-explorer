#!/bin/sh
set -eu
dnf install -y rpm-build python3-devel pyproject-rpm-macros python3-setuptools \
    python3-wheel python3-pytest python3-coverage python3-pyside6 python3-dbus-next \
    dbus-daemon qt6-qtwayland kglobalacceld
mkdir -p /tmp/rpmbuild/SOURCES
cp "$KDE_SHORTCUTS_SOURCE" /tmp/rpmbuild/SOURCES/
rpmbuild -ba --define '_topdir /tmp/rpmbuild' packaging/rpm/plasma-shortcut-explorer.spec
dnf install -y /tmp/rpmbuild/RPMS/noarch/*.rpm
sh scripts/check_installed.sh
rpm -e plasma-shortcut-explorer
test ! -e /usr/bin/plasma-shortcut-explorer
cp /tmp/rpmbuild/RPMS/noarch/*.rpm /tmp/rpmbuild/SRPMS/*.rpm /out/
