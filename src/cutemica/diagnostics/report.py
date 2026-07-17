"""Host and material metadata for a privacy-safe tester report."""

from __future__ import annotations

import platform
from datetime import UTC, datetime

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import qVersion
from PySide6.QtGui import QGuiApplication

from cutemica import __version__
from cutemica.diagnostics.session import ValidationSession
from cutemica.geometry import ScreenBinding
from cutemica.wallpaper import WallpaperSnapshot


def build_support_report(
    session: ValidationSession,
    bindings: tuple[ScreenBinding, ...],
    wallpaper: WallpaperSnapshot,
    registration: str,
) -> dict[str, object]:
    """Build diagnostics without wallpaper pixels, names, or source paths."""

    return {
        "schema_version": 1,
        "product": "CuteMica",
        "product_version": __version__,
        "exported_at_utc": datetime.now(UTC).isoformat(),
        "runtime": {
            "operating_system": platform.platform(),
            "macos_version": platform.mac_ver()[0],
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "qt": qVersion(),
            "pyside": pyside_version,
            "qt_platform": QGuiApplication.platformName(),
        },
        "display_topology": [_binding_payload(binding) for binding in bindings],
        "window_registration": registration,
        "wallpaper": _wallpaper_payload(wallpaper),
        "session": session.payload(),
    }


def _binding_payload(binding: ScreenBinding) -> dict[str, object]:
    native = binding.native_geometry_px
    qt = binding.qt_geometry_dip
    return {
        "screen_name": binding.qt_screen_name,
        "native_geometry_px": [native.x, native.y, native.width, native.height],
        "qt_geometry_dip": [qt.x, qt.y, qt.width, qt.height],
        "device_pixel_ratio": binding.device_pixel_ratio,
    }


def _wallpaper_payload(wallpaper: WallpaperSnapshot) -> dict[str, object]:
    sources = [wallpaper.default_source]
    sources.extend(item.source for item in wallpaper.per_screen)
    unique_sources = {
        (source.path.suffix.casefold(), source.placement.value, source.source_kind)
        for source in sources
    }
    source_paths = {source.path.resolve() for source in sources}
    return {
        "provider": wallpaper.provider_name,
        "per_screen_assignments": len(wallpaper.per_screen),
        "source_count": len(source_paths),
        "sources": [
            {
                "file_type": suffix or "unknown",
                "placement": placement,
                "source_kind": source_kind,
            }
            for suffix, placement, source_kind in sorted(unique_sources)
        ],
        "privacy": "Wallpaper pixels, filenames, and paths are not collected.",
    }
