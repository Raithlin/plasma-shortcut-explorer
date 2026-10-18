#!/usr/bin/env python3
"""Fill real project metadata in a disposable release checkout."""
import argparse
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-url", required=True)
    args = parser.parse_args()
    url = urlsplit(args.project_url)
    if url.scheme != "https" or not url.netloc or url.query or url.fragment:
        parser.error("Use the real HTTPS project URL, without a query or fragment")
    root = Path(__file__).resolve().parent.parent
    path = root / "data/org.kde.shortcutexplorer.metainfo.xml"
    tree = ET.parse(path)
    component = tree.getroot()
    homepage = component.find("url[@type='homepage']")
    if homepage is None:
        homepage = ET.SubElement(component, "url", type="homepage")
    homepage.text = args.project_url
    developer = component.find("developer")
    developer.set("id", "io.github." + url.path.strip("/").split("/")[0].lower()
                  if url.netloc == "github.com" else ".".join(reversed(url.netloc.split("."))))
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
