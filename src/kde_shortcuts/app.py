import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile, QStandardPaths
from .config import APP_ID
from .discovery import discover


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explore current KDE global shortcuts")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--settings", action="store_true", help="Open app settings")
    mode.add_argument("--diagnose", action="store_true", help="Print discovery JSON without opening a window")
    args = parser.parse_args(argv)
    if args.diagnose:
        result = asyncio.run(discover())
        print(json.dumps(asdict(result), indent=2))
        return int(bool(result.errors))
    from .ui import Overlay
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setDesktopFileName(APP_ID)
    app.setApplicationName("Plasma Shortcut Explorer")
    lock = QLockFile(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.RuntimeLocation) + "/kde-shortcut-explorer.lock")
    if not lock.tryLock(0):
        return 0
    window = Overlay()
    if args.settings:
        window.show_settings()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
