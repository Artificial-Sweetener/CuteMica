"""One-click export policy for an interactive validation session."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths

from cutemica.diagnostics.report import build_support_report
from cutemica.diagnostics.session import ValidationSession
from cutemica.diagnostics.support_bundle import SupportBundleWriter
from cutemica.geometry import ScreenBinding
from cutemica.wallpaper import WallpaperSnapshot


class TesterReportExporter:
    """Build and save a privacy-safe tester bundle to Downloads."""

    def __init__(
        self,
        bindings: tuple[ScreenBinding, ...],
        registration: str,
    ) -> None:
        self._bindings = bindings
        self._registration = registration

    def export(
        self,
        session: ValidationSession,
        wallpaper: WallpaperSnapshot,
    ) -> Path:
        """Write the current session and return its ZIP path."""

        report = build_support_report(
            session,
            self._bindings,
            wallpaper,
            self._registration,
        )
        downloads = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        destination = Path(downloads) if downloads else Path.home() / "Downloads"
        sensitive = tuple(
            str(source.path)
            for source in (
                wallpaper.default_source,
                *(item.source for item in wallpaper.per_screen),
            )
        ) + (str(Path.home()),)
        return SupportBundleWriter().write(
            report,
            destination,
            sensitive_values=sensitive,
        )
