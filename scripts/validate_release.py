#!/usr/bin/env python3
"""Check version and desktop identity consistency before producing release assets."""
import argparse
from pathlib import Path
import re
import tomllib
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    package = (root / "src/kde_shortcuts/__init__.py").read_text()
    if re.search(r'^__version__ = "([^"]+)"', package, re.M)[1] != version:
        parser.error("Application version disagrees with pyproject.toml")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        parser.error("Use a three-part release version")
    if args.tag and args.tag != f"v{version}":
        parser.error(f"Tag must be v{version}")
    rpm = (root / "packaging/rpm/plasma-shortcut-explorer.spec").read_text()
    if re.search(r"^Version:\s+(\S+)", rpm, re.M)[1] != version:
        parser.error("RPM version disagrees with pyproject.toml")
    changelog = (root / "packaging/debian/changelog").read_text()
    if not changelog.startswith(f"plasma-shortcut-explorer ({version}-1)"):
        parser.error("Debian changelog version disagrees with pyproject.toml")
    metadata = ET.parse(root / "data/org.kde.shortcutexplorer.metainfo.xml").getroot()
    if metadata.find("releases/release").get("version") != version:
        parser.error("AppStream version disagrees with pyproject.toml")
    config = (root / "src/kde_shortcuts/config.py").read_text()
    identity = re.search(r'APP_ID = "([^"]+)"', config)[1]
    if metadata.findtext("id") != identity:
        parser.error("AppStream identity disagrees with config.py")
    if metadata.find("launchable").text != f"{identity}.desktop":
        parser.error("AppStream desktop ID disagrees with application ID")
    desktop = (root / f"data/{identity}.desktop").read_text()
    if f"Icon={identity}\n" not in desktop or not (root / f"data/{identity}.svg").is_file():
        parser.error("Desktop icon and identity disagree")
    print(f"Release metadata is consistent: v{version} ({identity})")


if __name__ == "__main__":
    main()
