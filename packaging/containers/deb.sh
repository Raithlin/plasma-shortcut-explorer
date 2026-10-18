#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
cp -a packaging/debian debian
apt-get update
apt-get install -y --no-install-recommends build-essential devscripts equivs
apt-get build-dep -y --no-install-recommends .
dpkg-buildpackage -us -uc -b
apt-get install -y --no-install-recommends ../plasma-shortcut-explorer_*.deb
sh scripts/check_installed.sh
dpkg -r plasma-shortcut-explorer
test ! -e /usr/bin/plasma-shortcut-explorer
cp ../*.deb ../*.changes ../*.buildinfo /out/
