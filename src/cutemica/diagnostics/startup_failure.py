"""Create a useful report when the tester cannot reach the main window."""

from __future__ import annotations

import platform
import re
import traceback
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from cutemica.diagnostics.support_bundle import SupportBundleWriter


def write_startup_failure(error: Exception) -> Path:
    """Write a redacted startup report to the tester's Downloads folder."""

    downloads = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DownloadLocation
    )
    destination = Path(downloads) if downloads else Path.home() / "Downloads"
    report: dict[str, object] = {
        "schema_version": 1,
        "product": "CuteMica",
        "phase": "startup",
        "runtime": {
            "operating_system": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "error": {
            "type": type(error).__name__,
            "message": redact_startup_text(str(error)),
            "traceback": redact_startup_text(traceback.format_exc()),
        },
    }
    return SupportBundleWriter().write(
        report,
        destination,
        sensitive_values=(str(Path.home()),),
    )


def redact_startup_text(value: str) -> str:
    """Remove a home-relative filename from startup diagnostics."""

    redacted_home = value.replace(str(Path.home()), "<home>")
    return re.sub(r"<home>[/\\][^\n\r\"']+", "<redacted-path>", redacted_home)
