# Installation

Use a native package from [GitHub Releases](https://github.com/Raithlin/plasma-shortcut-explorer/releases),
or [install from source](#install-from-source). See the
[requirements](README.md#requirements) for supported dependencies.

## Verify a download

Download the package for your distribution and `SHA256SUMS` from the same
release. Put both files in a separate directory, then run:

```sh
sha256sum --check --ignore-missing SHA256SUMS
```

The package filename should appear with `OK`. You do not need to download the
other release assets.

The package commands below use version 0.1.2. Substitute the exact
filename you downloaded.

## Arch Linux

Download the `.pkg.tar.zst` package. You do not need an AUR account or helper.
Keep Arch up to date before installing:

```sh
sudo pacman -Syu
```

Pacman upgrades installed system packages. Then install the download:

```sh
sudo pacman -U ./plasma-shortcut-explorer-0.1.2-1-any.pkg.tar.zst
```

Pacman installs the app and resolves its dependencies. If Plasma's shortcut
editor is missing, install the optional System Settings package:

```sh
sudo pacman -S --needed systemsettings
```

This adds the editor used by the app's settings buttons. Arch package checks
currently target x86-64 Plasma 6 systems. See the ArchWiki for
[local package installation](https://wiki.archlinux.org/title/Pacman) and
[full system upgrades](https://wiki.archlinux.org/title/System_maintenance#Partial_upgrades_are_unsupported).

## Debian 13

Download the `.deb` package and install it:

```sh
sudo apt install ./plasma-shortcut-explorer_0.1.2-1_all.deb
```

Apt installs the app and resolves its dependencies from your configured repositories.

## Fedora 44

Download the `.rpm` package and install it:

```sh
sudo dnf install ./plasma-shortcut-explorer-0.1.2-1.fc44.noarch.rpm
```

Dnf installs the app and resolves its dependencies from your configured repositories.

## Install from source

Install Git, Python 3.11+ with venv support, and the Qt Wayland system runtime.
Then run, without sudo:

```sh
git clone https://github.com/Raithlin/plasma-shortcut-explorer.git
cd plasma-shortcut-explorer
./scripts/install.sh
```

The installer downloads Python dependencies into a dedicated virtual environment
and adds a launcher, desktop entry, icon, and AppStream metadata for your user.
It installs the current development checkout. To install a release, extract its
`plasma_shortcut_explorer-<version>.tar.gz` asset and run `./scripts/install.sh`
from that directory instead.

The environment lives under
`${XDG_DATA_HOME:-~/.local/share}/plasma-shortcut-explorer/venv`.
Add `~/.local/bin` to your `PATH` to use the terminal command. The application
menu entry works independently of that setting.

Remove a per-user installation before switching to a native package so its
launcher and desktop entry do not shadow the package's versions.

## Open the app

Choose **Plasma Shortcut Explorer** from the application menu or run
`plasma-shortcut-explorer`. The overlay opens with search focused.
[Assign a shortcut you will remember](README.md#assign-a-shortcut) to open it
from the keyboard.

### Window placement

On Wayland, open **System Settings → Window Management → Window Rules** and
use **Detect Window Properties** to match the explorer. Set
**Initial placement → Force → Centered** and, if available,
**Screen → Apply Initially → Active screen**. Labels vary between Plasma versions.
Test your launch shortcut from each monitor; KWin decides the final placement.

## Upgrade

The app's update check links to newer GitHub releases. Download and verify the
new package, then repeat the install command with its filename. The package
manager upgrades the existing installation.

GitHub downloads do not add an apt, dnf, or pacman update repository. System
upgrades alone will not fetch new app releases. On rolling Arch, a Python
upgrade may also require a package built for the new Python version.

For a source installation, get a newer checkout or source archive and rerun
`./scripts/install.sh`. The installer updates the per-user environment.

## Uninstall a per-user installation

From the checkout or extracted archive, run without sudo:

```sh
./scripts/uninstall.sh
```

The script removes the app environment, desktop assets, and launcher symlinks.
The installer also saves a standalone copy. If you deleted the checkout, run:

```sh
sh "${XDG_DATA_HOME:-$HOME/.local/share}/plasma-shortcut-explorer/uninstall.sh"
```

This performs the same removal. Use `--dry-run` to list what it would remove,
or `--purge` to also remove update preferences and cached release information.
Both scripts respect your XDG data location; the uninstaller also respects the
XDG config location. It leaves unrelated launchers and shared Python/Qt packages
in place.
If the uninstaller cannot verify an app directory by its installed entry point,
it reports and preserves that directory for manual inspection.

## Uninstall a native package

Use the manager that installed the app:

```sh
sudo pacman -R plasma-shortcut-explorer       # Arch
sudo apt remove plasma-shortcut-explorer    # Debian
sudo dnf remove plasma-shortcut-explorer    # Fedora
```

The selected manager removes the package. After either a per-user or native
uninstall, remove your launch shortcut and any window rule in Plasma System Settings.
