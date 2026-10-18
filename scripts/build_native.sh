#!/bin/sh
# All package-manager changes happen inside disposable rootless containers.
set -eu
cd "$(dirname "$0")/.."
case "${1:-}" in
    arch) image=docker.io/library/archlinux:base ;;
    deb) image=docker.io/library/debian:13 ;;
    rpm) image=registry.fedoraproject.org/fedora:44 ;;
    *) printf 'Usage: %s arch|deb|rpm\n' "$0" >&2; exit 2 ;;
esac
python="${KDE_SHORTCUTS_PYTHON:-python3}"
version=$("$python" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
archive="plasma_shortcut_explorer-$version.tar.gz"
test -f "dist/$archive" || { printf 'Build the source distribution first.\n' >&2; exit 1; }
mkdir -p "dist/native/$1"
"${KDE_SHORTCUTS_CONTAINER_ENGINE:-podman}" run --rm \
    --security-opt label=disable \
    -v "$PWD/dist/$archive:/sources/$archive:ro" \
    -v "$PWD/dist/native/$1:/out:rw" \
    -e "KDE_SHORTCUTS_SOURCE=/sources/$archive" \
    -e "KDE_SHORTCUTS_PACKAGE_TARGET=$1" \
    "$image" sh -eu -c '
        mkdir -p /work
        tar -xf "$KDE_SHORTCUTS_SOURCE" -C /work
        cd /work/plasma_shortcut_explorer-*
        exec sh "packaging/containers/$KDE_SHORTCUTS_PACKAGE_TARGET.sh"
    '
