"""Open KDE's verified shortcut KCM; never write global bindings ourselves."""
from shutil import which
from PySide6.QtCore import QProcess


def open_shortcut_settings(component=None):
    executable = which("systemsettings") or which("kcmshell6")
    if not executable:
        raise OSError("Plasma System Settings was not found. Install System Settings to configure the launch shortcut.")
    args = ["kcm_keys"]
    # Both KDE frontends split --args on spaces, without shell quoting.
    # Such component names must be located manually in the full editor.
    if component and " " not in component:
        args.extend(["--args", component])
    started, _pid = QProcess.startDetached(executable, args)
    if not started:
        raise OSError("Could not open Plasma's Shortcuts page. Open System Settings → Keyboard → Shortcuts manually.")
