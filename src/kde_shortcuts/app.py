import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile, QStandardPaths
from .config import APP_ID
from .discovery import discover


def main():
    parser = argparse.ArgumentParser(description="Explore current KDE global shortcuts")
    parser.add_argument("--diagnose", action="store_true", help="Print discovery JSON without opening a window")
    args = parser.parse_args()
    if args.diagnose:
        result = asyncio.run(discover())
        print(json.dumps(asdict(result), indent=2))
        return int(bool(result.errors))
    from .ui import Overlay
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setDesktopFileName(APP_ID)
    app.setApplicationName("Shortcut Explorer")
    lock = QLockFile(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.RuntimeLocation) + "/kde-shortcut-explorer.lock")
    if not lock.tryLock(0):
        return 0
    window = Overlay()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
