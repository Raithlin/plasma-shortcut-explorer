#!/usr/bin/env python3
"""Stage a PKGBUILD with the actual source checksum; never use SKIP for releases."""
import argparse
import hashlib
from pathlib import Path
import shlex
import shutil
import tomllib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dist/arch"))
    parser.add_argument("--project-url", default=None)
    parser.add_argument("--source-url", help="Public source URL for an AUR recipe; omit for a local build")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    project_url = args.project_url if args.project_url is not None else project["urls"]["Homepage"]
    if args.archive.name != f"plasma_shortcut_explorer-{version}.tar.gz":
        parser.error("Archive filename must match the version in pyproject.toml")
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.archive.name
    if args.source_url:
        source += "::" + args.source_url
    replacements = {"VERSION": version, "URL": shlex.quote(project_url),
                    "SOURCE": shlex.quote(source),
                    "SHA256": hashlib.sha256(args.archive.read_bytes()).hexdigest()}
    template = (root / "packaging/arch/PKGBUILD.in").read_text()
    for key, value in replacements.items():
        template = template.replace(f"@{key}@", value)
    (args.output / "PKGBUILD").write_text(template)
    shutil.copy2(args.archive, args.output / args.archive.name)
    print(args.output / "PKGBUILD")


if __name__ == "__main__":
    main()
