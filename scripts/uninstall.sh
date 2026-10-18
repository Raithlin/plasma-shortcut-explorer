#!/bin/sh
# Remove only the per-user installation; native packages belong to their manager.
set -eu
dry_run=false
purge=false
for option in "$@"; do
    case "$option" in
        --dry-run) dry_run=true ;;
        --purge) purge=true ;;
        -h|--help)
            printf 'Usage: %s [--dry-run] [--purge]\n' "$0"
            printf 'Remove the per-user app. --purge also removes update preferences.\n'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$option" >&2; exit 2 ;;
    esac
done

base="${XDG_DATA_HOME:-$HOME/.local/share}"
config="${XDG_CONFIG_HOME:-$HOME/.config}"
for location in "$HOME" "$base" "$config"; do
    case "$location" in
        /*) ;;
        *) printf 'HOME and XDG paths must be absolute: %s\n' "$location" >&2; exit 2 ;;
    esac
done
appdir="$base/plasma-shortcut-explorer"
old_appdir="$base/kde-shortcut-explorer"

remove_file() {
    if [ -e "$1" ] || [ -L "$1" ]; then
        if "$dry_run"; then
            printf 'Would remove: %s\n' "$1"
        else
            rm -f -- "$1"
        fi
    fi
}

for launcher in "$HOME/.local/bin/plasma-shortcut-explorer" "$HOME/.local/bin/kde-shortcuts"; do
    if [ -L "$launcher" ]; then
        case "$(readlink "$launcher")" in
            "$appdir/venv/bin/plasma-shortcut-explorer"|"$appdir/venv/bin/kde-shortcuts"|\
            "$old_appdir/venv/bin/plasma-shortcut-explorer"|"$old_appdir/venv/bin/kde-shortcuts") remove_file "$launcher" ;;
            *) printf 'Preserving unrelated launcher: %s\n' "$launcher" >&2 ;;
        esac
    elif [ -e "$launcher" ]; then
        printf 'Preserving unrelated launcher: %s\n' "$launcher" >&2
    fi
done
remove_file "$base/applications/org.kde.shortcutexplorer.desktop"
remove_file "$base/icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg"
remove_file "$base/metainfo/org.kde.shortcutexplorer.metainfo.xml"
if "$purge"; then
    remove_file "$config/Raithlin/PlasmaShortcutExplorer.conf"
fi
for directory in "$appdir" "$old_appdir"; do
    if [ -e "$directory" ] || [ -L "$directory" ]; then
        if "$dry_run"; then
            printf 'Would remove: %s\n' "$directory"
        else
            rm -rf -- "$directory"
        fi
    fi
done
if ! "$dry_run"; then
    printf 'Per-user installation removed. Remove any launch shortcut or window rule in Plasma System Settings.\n'
fi
