#!/usr/bin/env python3
"""Download a versioned AppImage build tool and check its supplied SHA-256."""
import argparse
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("sha256")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != "https" or "/releases/download/" not in url.path or "/continuous/" in url.path:
        parser.error("Supply a versioned HTTPS release asset, not a continuous build")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.sha256):
        parser.error("Supply the independently verified SHA-256")
    digest = hashlib.sha256()
    temporary = args.output.with_suffix(".download")
    try:
        with urlopen(args.url, timeout=60) as source, temporary.open("wb") as target:
            while data := source.read(1024 * 1024):
                digest.update(data)
                target.write(data)
        if digest.hexdigest() != args.sha256.lower():
            parser.error("Downloaded asset checksum mismatch")
        temporary.replace(args.output)
        args.output.chmod(0o755)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
