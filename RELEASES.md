# Release engineering

## Status

The application remains a development build, version 0.1.0. The public upstream
repository is https://github.com/Raithlin/plasma-shortcut-explorer. No public
release has been created. Native package recipes use system Python and distro
Qt bindings, rather than pip at install time. The final application namespace, screenshots, and signing keys must
be settled before publishing a release. The current desktop ID is intentionally preserved
to avoid breaking an existing user-assigned shortcut.

## Quality gates

Run `KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/test.sh -q`. This creates an
isolated D-Bus session and runs all tests with Qt's offscreen backend. It enforces
95% line and 95% branch coverage independently, across all application modules.
No application code is excluded. The integration test exports a mock KGlobalAccel
only on the private bus; it never registers shortcuts with the desktop.

Real Plasma Wayland remains a separate manual release gate: launch via the
assigned shortcut, verify Escape, focus loss, refresh after a changed binding,
monitor placement, and system light/dark themes. Automated coverage does not
prove compositor behavior or package portability.

## Build sources

```sh
.venv/bin/pip install build
.venv/bin/python -m build
```

Both the sdist and wheel include the desktop entry, icon, and AppStream metadata.
The sdist also includes tests and packaging recipes. Build native packages from
the same sdist, not from a wheel copied out of a developer virtual environment.
Before a public build, fill the real homepage with
`python scripts/configure_release.py --project-url https://github.com/Raithlin/plasma-shortcut-explorer`
and validate with `appstreamcli validate --no-net data/*.metainfo.xml`.
This is the public upstream location.

## Native builds and installation checks

With rootless Podman installed, after building the sdist:

```sh
scripts/build_native.sh arch
scripts/build_native.sh deb
scripts/build_native.sh rpm
```

Use `KDE_SHORTCUTS_CONTAINER_ENGINE=docker` if using Docker. Each command creates
a disposable container, installs its own build dependencies, runs tests, builds
and installs the package, checks its assets and missing-session diagnostics,
then removes it and checks that the executable is gone. It does not install
packages on the host. Output is under `dist/native/{arch,deb,rpm}`.
Image tags move; record the resolved image digests and build logs for a release.
GitHub Actions are pinned to immutable commit IDs, with their major versions in comments.
These recipes alone do not establish bit-for-bit reproducibility.

Targets: current Arch, Debian 13, and Fedora 44 on x86_64. Native packages are
architecture-independent Python code, but dependencies must be available on each
architecture. Ubuntu is not yet a validated target; build on the actual target
release rather than assuming Debian binaries work there. Python 3.11+, PySide6
6.6+, and a Plasma 6 session providing `allMainComponents`,
`allActionsForComponent`, and `shortcutKeys` are required. All three methods were also verified in the [KGlobalAccel 6.0.0 interface XML](https://github.com/KDE/kglobalaccel/blob/v6.0.0/src/org.kde.KGlobalAccel.xml). The live service is verified on Frameworks 6.31; older target desktop versions still require live testing.

The Arch PKGBUILD is generated using the source archive's actual SHA-256. For AUR
publication regenerate it with a real `--project-url` and `--source-url`, then
run `makepkg --printsrcinfo`. Never publish a checksum of `SKIP`.

```sh
python scripts/prepare_arch.py dist/plasma_shortcut_explorer-0.1.0.tar.gz \
  --project-url https://github.com/Raithlin/plasma-shortcut-explorer \
  --source-url https://github.com/Raithlin/plasma-shortcut-explorer/releases/download/v0.1.0/plasma_shortcut_explorer-0.1.0.tar.gz
```

For direct installation use `sudo pacman -U FILE.pkg.tar.zst`,
`sudo apt install ./FILE.deb`, or `sudo dnf install ./FILE.rpm`.
Use the same manager to remove `plasma-shortcut-explorer`. Packages never configure
Meta+K, install autostart entries, or alter KDE shortcut files.

## AppImage

Build on Ubuntu 24.04 (glibc 2.39 baseline), not the rolling-release Arch host.
The AppImage bundles Python/Qt, but still needs a host KDE Plasma 6 session.
Install `requirements-dev.txt` and `requirements-appimage.txt` in a build venv,
then install this project. Supply verified, versioned appimagetool and type2
runtime files; the script deliberately does not download mutable `continuous`
assets or fetch a runtime implicitly.

```sh
APPIMAGETOOL=/absolute/path/to/appimagetool \
APPIMAGE_RUNTIME=/absolute/path/to/runtime-x86_64 \
KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/build_appimage.sh
```

The builder uses a PyInstaller directory bundle, checks for Wayland plugins,
copies dependency license notices, and produces `dist/Plasma_Shortcut_Explorer-*.AppImage`.
Before distributing, audit bundled license/source obligations, run
`--appimage-extract-and-run --diagnose` outside KDE (expected exit 1 with JSON),
and run GUI checks on all target desktops. Merely finding a Wayland plugin does
not prove that all its shared-library dependencies resolve on another distro.

AppImage validation and publication are separate from native packaging. The
build helper is provided, but no AppImage is release-qualified until those
cross-distro checks and the bundle license review pass.

## Publication

Use version tags matching pyproject.toml, RPM Version, Debian changelog, and
AppStream metadata. CI gates tests and creates artifacts. Release workflows
prepare a **draft**, requiring human review before publication. They do not
create apt/dnf repositories or submit to AUR.

A GitHub release holding .deb/.rpm files provides downloads, not automatic
package-manager updates. For updates, provision a signed apt repository (or an
Ubuntu PPA), an RPM repository/COPR, and/or maintain the AUR recipe. Keep signing
keys out of the repository and use protected CI environments. Publish checksums
and signatures with the artifacts; checksums alone do not authenticate them.

References: [Arch Python packaging](https://wiki.archlinux.org/title/Python_package_guidelines),
[Debian pybuild](https://wiki.debian.org/Python/Pybuild),
[Fedora Python macros](https://fedoraproject.org/wiki/Changes/DeprecateSetuppyMacros),
[AppImage packaging](https://docs.appimage.org/packaging-guide/).

## Checks completed in the development environment

The automated suite currently passes 53 tests with 99.75% line coverage and
98.89% branch coverage. All application modules are included; the only uncovered
application path is the module's `__main__` wrapper. The wire-format integration
test passes on a private D-Bus session. A fresh read of the real Plasma service
returned 124 assigned actions, zero errors, in 0.181 seconds.

Native container validation completed successfully:

| Target | Tests | Lines | Branches | Install/assets/diagnostics/removal |
| --- | --- | --- | --- | --- |
| Current Arch | 39 passed | 99.62% | 98.57% | Passed |
| Debian 13 | 39 passed | 99.25% | 98.78% | Passed |
| Fedora 44 | 39 passed | 99.62% | 98.57% | Passed |

The first Fedora install check caught an automatically generated PyPI Essentials
requirement that the distro could not satisfy. The recipe now filters that
requirement, explicitly depends on Fedora's python3-pyside6, and passed a fresh
build and installation check. These are development package candidates, not
published releases. Rebuild all artifacts together from the chosen immutable tag
before publishing; local validation builds were iterative.
The three GitHub workflows pass actionlint. AppImage tooling is a candidate build
path, not a claim of a validated portable release. AppStream homepage metadata uses the intended repository URL and passes offline
validation. CI also derives the URL from its actual repository.

## KDE Python distribution guidance (checked 2026-10-18)

KDE's [Python packaging tutorial](https://develop.kde.org/docs/getting-started/python/python-package/)
uses pyproject.toml, setuptools, an entry point, desktop metadata, an icon, and
AppStream metadata. A single source file or frozen executable is not required.
Our package layout follows this approach; internal modules can remain separate
regardless of the installation format.

KDE's [Python Flatpak tutorial](https://develop.kde.org/docs/getting-started/python/python-flatpak/)
uses the KDE runtime and a PySide BaseApp (or PyQt BaseApp). The example's runtime
version is illustrative, not a version pin to copy into a new release.
Flatpak is a documented cross-distribution route, not the only allowed format.
Kajongg, a KDE Python application, also documents
[installation through distro packages](https://docs.kde.org/stable_kf6/en/kajongg/kajongg/kajongg.pdf).
KDE's build infrastructure also supports
[Craft-based AppImage jobs](https://blogs.kde.org/2024/01/30/farewell-binary-factory-add-craft-jobs-your-apps-kdes-gitlab-now/).

For this host-integrated utility, we recommend native packages first. A Flatpak
would need explicitly scoped KGlobalAccel D-Bus permission and a tested host
settings-editor handoff. Its default sandbox does not allow arbitrary host
processes or services; the current QProcess invocation is not a Flatpak solution.
See [Flatpak permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html#d-bus-access).
There is no tested Flatpak manifest in this repository. AppImage remains an
optional candidate format, not a KDE requirement.

KDE's [Flatpak integration guidance](https://develop.kde.org/docs/packaging/flatpak/integration/#theming)
also says to follow the system theme rather than hardcode an application theme.
The settings page therefore has no appearance selector or persisted color settings.

The native validation table above records the earlier prototype revision. The
public package rename and Settings changes require fresh native builds before
release; do not publish those older development artifacts under the new name.
