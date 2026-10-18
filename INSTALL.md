# Installation

## Arch Linux and EndeavourOS

Until AUR publishing is available, install the native Arch package from
[GitHub Releases](https://github.com/Raithlin/plasma-shortcut-explorer/releases).
An AUR account or helper is not required. The release workflow builds the
`.pkg.tar.zst` package and tests installation and removal in an Arch container.
See [requirements and tested desktop versions](README.md#requirements-and-compatibility)
before installing. Arch validation currently targets x86-64 Plasma 6 systems.

No release has been published yet. The steps below apply once release assets
are available; the source installation below is available now.

### Install a release package

1. Download `plasma-shortcut-explorer-<version>-<pkgrel>-any.pkg.tar.zst` and
   `SHA256SUMS` from the same GitHub release into a dedicated directory.
2. In that directory, check the downloaded package:

   ```sh
   sha256sum --check --ignore-missing SHA256SUMS
   ```

   Confirm that the package filename is reported as `OK`. Other release assets
   do not need to be downloaded.
3. Bring the system up to date using Arch's normal full-upgrade procedure:

   ```sh
   sudo pacman -Syu
   ```

4. Install the downloaded package using its exact filename. For example, for
   version 0.1.0, package revision 1:

   ```sh
   sudo pacman -U ./plasma-shortcut-explorer-0.1.0-1-any.pkg.tar.zst
   ```

   Pacman resolves required dependencies from the configured repositories.
   For the settings-editor handoff, install the optional System Settings package
   if your Plasma installation does not already provide it:

   ```sh
   sudo pacman -S --needed systemsettings
   ```

Launch **Plasma Shortcut Explorer** from the application menu or run
`plasma-shortcut-explorer`. Then [assign an opening shortcut](README.md#assign-metak).
This package does not register a shortcut or add autostart entries.

Pacman's local package installation and Arch's full-upgrade guidance are
documented in the [ArchWiki](https://wiki.archlinux.org/title/Pacman) and
[system maintenance guidance](https://wiki.archlinux.org/title/System_maintenance#Partial_upgrades_are_unsupported).

### Upgrade

The app's asynchronous update check links to newer GitHub releases. Download
the new package and its `SHA256SUMS`, verify it, and repeat `pacman -U` with the
new filename. Pacman upgrades the existing installation.

This is a locally installed package, so `pacman -Syu` alone will not fetch new
app releases from GitHub. Automatic package-manager updates can be added later
through AUR or a package repository. Python upgrades on rolling Arch may also
require an updated package built for the current system Python.

### Remove

Remove any launch shortcut and window rule you created, then run:

```sh
sudo pacman -R plasma-shortcut-explorer
```

## Manual installation from source

For a per-user installation without a native package, install Git, Python 3.11+
with venv support, and the Qt Wayland system runtime, then:

```sh
git clone https://github.com/Raithlin/plasma-shortcut-explorer.git
cd plasma-shortcut-explorer
./scripts/install.sh
```

This installs the current development checkout. To use a release instead,
download and extract its `plasma_shortcut_explorer-<version>.tar.gz` source asset
and run `./scripts/install.sh` from the extracted directory.

The installer uses a dedicated virtual environment under
`${XDG_DATA_HOME:-~/.local/share}/plasma-shortcut-explorer/venv`, creates launchers
in `~/.local/bin`, and installs the desktop entry, icon, and AppStream metadata.
It downloads Python dependencies into that environment. It does not require
root or install into system Python. Ensure `~/.local/bin` is on your `PATH` to
use the terminal command.

Update by obtaining a newer checkout or release source archive and rerunning
the installer. Follow the README's [per-user removal instructions](README.md#uninstall)
to uninstall. Remove a per-user installation before switching to the native
package so its launcher and desktop entry do not shadow the packaged versions.
