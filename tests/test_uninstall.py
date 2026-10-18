"""Exercise removal in disposable homes; never touch the real installation."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/uninstall.sh"


@pytest.fixture
def installation(tmp_path):
    home = tmp_path / "home"
    data = tmp_path / "app data"
    config = tmp_path / "config"
    home.mkdir()
    appdir = data / "plasma-shortcut-explorer"
    appdir.mkdir(parents=True)
    (appdir / "venv/bin").mkdir(parents=True)
    (appdir / "venv/bin/plasma-shortcut-explorer").write_text("installed entry point")
    assets = [data / "applications/org.kde.shortcutexplorer.desktop",
              data / "icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg",
              data / "metainfo/org.kde.shortcutexplorer.metainfo.xml"]
    for path in assets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("installed asset")
    bindir = home / ".local/bin"
    bindir.mkdir(parents=True)
    launcher = bindir / "plasma-shortcut-explorer"
    launcher.symlink_to(appdir / "venv/bin/plasma-shortcut-explorer")
    preference = config / "Raithlin/PlasmaShortcutExplorer.conf"
    preference.parent.mkdir(parents=True)
    preference.write_text("[updates]\nautomatic=false\n")
    unrelated = data / "applications/other.desktop"
    unrelated.write_text("unrelated app")
    env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(data), XDG_CONFIG_HOME=str(config))
    return env, appdir, assets, launcher, preference, unrelated


def run(env, *options, script=SCRIPT):
    return subprocess.run(["sh", str(script), *options], env=env, capture_output=True, text=True)


def test_removes_installation_preserves_preferences_and_external_data(installation, tmp_path):
    env, appdir, assets, launcher, preference, unrelated = installation
    external = tmp_path / "external"
    external.mkdir()
    precious = external / "keep.txt"
    precious.write_text("keep me")
    (appdir / "external").symlink_to(external, target_is_directory=True)
    olddir = appdir.parent / "kde-shortcut-explorer"
    (olddir / "venv/bin").mkdir(parents=True)
    (olddir / "venv/bin/kde-shortcuts").write_text("legacy entry point")
    old_launcher = launcher.with_name("kde-shortcuts")
    old_launcher.symlink_to(olddir / "venv/bin/kde-shortcuts")
    process = run(env)
    assert process.returncode == 0, process.stderr
    assert not appdir.exists() and not olddir.exists()
    assert not launcher.is_symlink() and not old_launcher.is_symlink()
    assert not any(path.exists() for path in assets)
    assert preference.exists() and unrelated.exists()
    assert precious.read_text() == "keep me"
    assert "Plasma System Settings" in process.stdout
    assert run(env).returncode == 0  # Repeating removal is harmless.


def test_dry_run_and_purge(installation):
    env, appdir, assets, launcher, preference, unrelated = installation
    process = run(env, "--dry-run", "--purge")
    assert process.returncode == 0 and "Would remove" in process.stdout
    assert appdir.exists() and launcher.is_symlink() and preference.exists()
    assert all(path.exists() for path in assets)
    sibling = preference.with_name("OtherApp.conf")
    sibling.write_text("keep")
    assert run(env, "--purge").returncode == 0
    assert not preference.exists()
    assert sibling.exists() and unrelated.exists()


@pytest.mark.parametrize("symlink", [True, False])
def test_unrelated_launcher_is_not_deleted(installation, tmp_path, symlink):
    env, appdir, assets, launcher, preference, unrelated = installation
    launcher.unlink()
    if symlink:
        launcher.symlink_to(tmp_path / "another-program")
    else:
        launcher.write_text("custom wrapper")
    process = run(env)
    assert process.returncode == 0
    assert launcher.is_symlink() if symlink else launcher.read_text() == "custom wrapper"
    assert "Preserving unrelated launcher" in process.stderr


def test_help_bad_options_and_relative_paths_do_not_remove_anything(installation):
    env, appdir, assets, launcher, preference, unrelated = installation
    assert run(env, "--help").returncode == 0
    assert run(env, "--unknown").returncode == 2
    invalid = dict(env, XDG_DATA_HOME="relative/path")
    assert run(invalid).returncode == 2
    assert appdir.exists() and all(path.exists() for path in assets)


def test_app_directory_symlink_is_not_followed(installation, tmp_path):
    env, appdir, assets, launcher, preference, unrelated = installation
    shutil.rmtree(appdir)
    external = tmp_path / "other directory"
    external.mkdir()
    (external / "keep").write_text("data")
    appdir.symlink_to(external, target_is_directory=True)
    assert run(env).returncode == 0
    assert appdir.is_symlink() and (external / "keep").exists()


def test_unverified_installation_directories_are_preserved(installation):
    env, appdir, assets, launcher, preference, unrelated = installation
    (appdir / "venv/bin/plasma-shortcut-explorer").unlink()
    current_data = appdir / "my-work.txt"
    current_data.write_text("keep current")
    olddir = appdir.parent / "kde-shortcut-explorer"
    olddir.mkdir()
    legacy_data = olddir / "my-work.txt"
    legacy_data.write_text("keep legacy")
    process = run(env)
    assert process.returncode == 0
    assert current_data.read_text() == "keep current"
    assert legacy_data.read_text() == "keep legacy"
    assert process.stderr.count("Preserving unverified installation directory") == 2


def test_installer_saves_a_working_standalone_uninstaller(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    python = tools / "python3"
    # Stub venv/pip creation: this integration test never downloads or installs Python packages.
    python.write_text(f"#!{sys.executable}\n" + '''
import sys
from pathlib import Path
assert sys.argv[1:3] == ['-m', 'venv']
binpath = Path(sys.argv[3]) / 'bin'
binpath.mkdir(parents=True)
for name in ('pip', 'plasma-shortcut-explorer'):
    path = binpath / name
    path.write_text('#!/bin/sh\\nexit 0\\n')
    path.chmod(0o755)
''')
    python.chmod(0o755)
    env = dict(os.environ, HOME=str(home), PATH=str(tools) + os.pathsep + os.environ["PATH"])
    env.pop("XDG_DATA_HOME", None)
    env.pop("XDG_CONFIG_HOME", None)
    process = subprocess.run(["sh", str(ROOT / "scripts/install.sh")], env=env, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    appdir = home / ".local/share/plasma-shortcut-explorer"
    saved = appdir / "uninstall.sh"
    assert saved.is_file()
    assert run(env, script=saved).returncode == 0
    assert not appdir.exists()
    assert not (home / ".local/bin/plasma-shortcut-explorer").is_symlink()
