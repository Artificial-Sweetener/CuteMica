"""Locate the Qt D-Bus command across distribution-specific Qt layouts."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_DIRECT_NAMES = ("qdbus6", "qdbus", "qdbus-qt5")
_QTPATHS_NAMES = ("qtpaths6", "qtpaths-qt6", "qtpaths")


def qt_dbus_executable() -> str:
    """Return the installed Qt D-Bus command or raise an actionable error."""
    for name in _DIRECT_NAMES:
        if executable := shutil.which(name):
            return executable
    for name in _QTPATHS_NAMES:
        qtpaths = shutil.which(name)
        if qtpaths is None:
            continue
        candidate = _query_qt_binary_directory(qtpaths) / "qdbus"
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError("Plasma wallpaper discovery requires qdbus")


def _query_qt_binary_directory(qtpaths: str) -> Path:
    try:
        completed = subprocess.run(
            (qtpaths, "--query", "QT_INSTALL_BINS"),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"Could not query Qt's binary directory: {error}") from error
    return Path(completed.stdout.strip())
