# Release engineering

Version 0.1.2 improves launcher search and the shortcut window layout. GitHub
Releases hosts the source archive, wheel, and native packages. AUR publishing
and AppImage qualification remain pending.

## Prepare a version

Keep the version consistent in:

- `pyproject.toml` and `src/kde_shortcuts/__init__.py`
- `packaging/rpm/plasma-shortcut-explorer.spec`
- `packaging/debian/changelog`
- `data/org.kde.shortcutexplorer.metainfo.xml`

Update `CHANGELOG.md`, then validate the intended tag. For version 0.1.2:

```sh
python scripts/validate_release.py --tag v0.1.2
```

The script reports consistent metadata or exits with an error. It also checks
the desktop ID and icon. Keep `org.kde.shortcutexplorer` stable to preserve
existing shortcut assignments.

Run the [test suite and real-desktop checks](DEVELOPMENT.md#run-the-tests)
before tagging. Tests require at least 95% line and 95% branch coverage.
Check keyboard launch, Escape, focus loss, refresh, themes, and monitor placement
in Plasma as well.

## Publish automatically

Push a `vX.Y.Z` tag that matches the version metadata to trigger
`.github/workflows/release.yml`. The workflow:

1. Validates the tag and runs tests and coverage checks.
2. Builds the source archive and wheel.
3. Builds, installs, checks, and removes the Arch, Debian, and Fedora packages
   in disposable containers.
4. Checks that every package format is present and generates `SHA256SUMS`.
5. Uploads all assets to a temporary draft, then publishes it as the latest
   GitHub release without an approval step.

A failed upload leaves a draft. Rerun **Publish release** with the existing tag
to resume. The workflow refuses to replace an already-public release.

Ordinary pushes and pull requests run tests and source builds. To test native
packages without publishing, run **Tests and packages** manually with
`packages` enabled. AppImage uses its own manual workflow.

GitHub downloads are the current distribution channel for Debian, Fedora, and
Arch. They do not add package-manager update repositories or publish to AUR.
[INSTALL.md](INSTALL.md) explains installation and manual upgrades.

## Build source archives locally

In the development environment, run:

```sh
.venv/bin/pip install build
.venv/bin/python -m build
```

The build writes a `.tar.gz` source archive and `.whl` under `dist/`. Both contain
the desktop entry, icon, and AppStream metadata. The source archive also includes
tests, documentation, and package recipes. Build native packages from this archive.

CI derives the homepage from its GitHub repository. If building for a different
upstream location, set it before building:

```sh
python scripts/configure_release.py --project-url https://github.com/Raithlin/plasma-shortcut-explorer
appstreamcli validate --no-net data/org.kde.shortcutexplorer.metainfo.xml
```

The helper updates the release URLs; AppStream reports any metadata errors.

## Build native packages locally

Install rootless Podman and build the source archive first. Run:

```sh
scripts/build_native.sh arch
scripts/build_native.sh deb
scripts/build_native.sh rpm
```

Each command runs its package manager inside a disposable container. It tests
and installs the package, checks launchers, desktop assets, imports, and
missing-session diagnostics, then removes it. Outputs appear under
`dist/native/{arch,deb,rpm}`. Host packages stay unchanged.

Set `KDE_SHORTCUTS_CONTAINER_ENGINE=docker` to use Docker. Targets are rolling
Arch, Debian 13, and Fedora 44 on x86-64. Recipes produce architecture-independent
Python packages, but dependencies and desktop behavior still need validation on
other targets. Do not assume Debian packages support Ubuntu.

Record resolved container image digests and build logs for each release. Image
tags move; the recipes do not promise bit-for-bit reproducibility. GitHub Actions
use pinned commit IDs.

## Prepare an AUR submission

Follow the [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines).
Create an [AUR account](https://aur.archlinux.org/register), register a dedicated
public SSH key, and check for an existing official or AUR package before submitting.
The account and automation key setup are still pending for this project.

Generate the recipe from the published source asset:

```sh
python scripts/prepare_arch.py dist/plasma_shortcut_explorer-0.1.2.tar.gz \
  --project-url https://github.com/Raithlin/plasma-shortcut-explorer \
  --source-url https://github.com/Raithlin/plasma-shortcut-explorer/releases/download/v0.1.2/plasma_shortcut_explorer-0.1.2.tar.gz
```

The helper writes `dist/arch/PKGBUILD` with the source URL and actual SHA-256,
then copies the archive alongside it. In a validated Arch packaging environment,
run from the recipe directory:

```sh
makepkg --printsrcinfo > .SRCINFO
```

This generates the metadata AUR uses to display the package. Regenerate it after
changing recipe metadata. Use a separate AUR Git checkout on its required
`master` branch; the upstream GitHub branch remains `main`.

Commit the PKGBUILD, `.SRCINFO`, required helpers, and packaging-source license.
Keep the maintainer comment and MIT license. Leave source archives and built
packages out of the AUR repository. Validate the initial submission before
enabling automatic updates.

## Build a candidate AppImage

Build on Ubuntu 24.04 with its glibc 2.39 baseline. Install
`requirements-dev.txt`, `requirements-appimage.txt`, and the project in a build
venv. Supply versioned appimagetool and type2-runtime files with independently
verified checksums, then run:

```sh
APPIMAGETOOL=/absolute/path/to/appimagetool \
APPIMAGE_RUNTIME=/absolute/path/to/runtime-x86_64 \
KDE_SHORTCUTS_PYTHON=.venv/bin/python scripts/build_appimage.sh
```

The script writes `dist/Plasma_Shortcut_Explorer-*.AppImage`. It bundles a
PyInstaller directory build, checks for Wayland plugins, and copies dependency
license notices. The manual **Build candidate AppImage** workflow accepts the
tool/runtime URLs and checksums as inputs.

Before publishing an AppImage, review bundled license and source obligations,
check shared-library dependencies on target distributions, and test the GUI in
Plasma. Outside KDE, `--appimage-extract-and-run --diagnose` should return 1 with
JSON errors. The current helper does not establish portability; AppImage remains
outside automatic release publication.

## Validation record

For v0.1.2, the local suite passed 93 tests with 99.64% line and 98.44% branch coverage.
Release metadata, AppStream, and desktop-entry validation passed, and source
archive and wheel builds succeeded. The UI smoke check passed in a live Plasma
Wayland session, covering rendering, search, errors, and shutdown. Interactive
resize-handle dragging, keyboard launch, themes, and multi-monitor placement
remain manual checks.

For v0.1.1, the local suite passed 90 tests with 99.63% line and 98.33% branch coverage.
The uncovered paths are the `__main__` wrapper and a defensive oversized-response
check. Private-bus integration, offscreen UI smoke checks, wheel builds, desktop
metadata validation, and actionlint passed.

The v0.1.0 release workflow passed native package tests and installation/removal
checks on Arch, Debian 13, and Fedora 44. All published assets match their
SHA-256 checksums. Release metadata uses a non-hidden filename so GitHub does
not rename it during upload.

Earlier prototype package checks passed on these targets:

| Target | Tests | Line coverage | Branch coverage | Install/check/remove |
| --- | --- | --- | --- | --- |
| Arch | 39 | 99.62% | 98.57% | Passed |
| Debian 13 | 39 | 99.25% | 98.78% | Passed |
| Fedora 44 | 39 | 99.62% | 98.57% | Passed |

Those builds predate the public rename, settings, and updater. Rebuild from the
final tag before publishing. The Fedora check caught an unwanted generated PyPI
Essentials dependency; the recipe now filters it and requires distro PySide6.

## Packaging references

KDE's [Python packaging tutorial](https://develop.kde.org/docs/getting-started/python/python-package/)
uses modular Python sources, `pyproject.toml`, an entry point, and desktop assets.
The project follows that layout. Native packages use distro Python and Qt;
they do not run pip during installation.

KDE also documents [Python Flatpak packaging](https://develop.kde.org/docs/getting-started/python/python-flatpak/)
and [Craft AppImage builds](https://blogs.kde.org/2024/01/30/farewell-binary-factory-add-craft-jobs-your-apps-kdes-gitlab-now/).
A Flatpak would need scoped KGlobalAccel D-Bus access and a tested way to open
host settings. The current QProcess handoff does not work through Flatpak's
default sandbox. See [Flatpak permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html#d-bus-access).
There is no tested Flatpak manifest here.

For native recipes, see [Arch Python packaging](https://wiki.archlinux.org/title/Python_package_guidelines),
[Debian pybuild](https://wiki.debian.org/Python/Pybuild), and
[Fedora Python macros](https://fedoraproject.org/wiki/Changes/DeprecateSetuppyMacros).
For bundled builds, see the [AppImage packaging guide](https://docs.appimage.org/packaging-guide/).

Future apt or RPM update repositories need hosting and signing setup. COPR or
an Ubuntu PPA are possible distribution-specific routes; they are not part of
the current workflow. Keep signing keys in CI secrets and publish signatures
when signing is configured. Checksums alone do not authenticate a download.
