"""Narrow AppKit boundary for native macOS wallpaper still images."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, cast


def write_macos_url_as_png(source_url: str, destination: Path) -> bool:
    """Decode an AppKit-supported URL and atomically write a PNG still."""

    appkit: Any = import_module("AppKit")
    foundation: Any = import_module("Foundation")
    url: Any = foundation.NSURL.URLWithString_(source_url)
    if url is None:
        return False
    image: Any = appkit.NSImage.alloc().initWithContentsOfURL_(url)
    if image is None:
        return False
    tiff_data: Any = image.TIFFRepresentation()
    if tiff_data is None:
        return False
    representation: Any = appkit.NSBitmapImageRep.imageRepWithData_(tiff_data)
    if representation is None:
        return False
    png_data: Any = representation.representationUsingType_properties_(
        appkit.NSBitmapImageFileTypePNG,
        {},
    )
    if png_data is None:
        return False
    return bool(png_data.writeToFile_atomically_(str(destination), True))


def read_system_wallpaper_url() -> str | None:
    """Read WallpaperAgent's current system wallpaper URL preference."""

    foundation: Any = import_module("Foundation")
    defaults: Any = foundation.NSUserDefaults.standardUserDefaults()
    domain = cast(
        dict[str, Any] | None,
        defaults.persistentDomainForName_("com.apple.wallpaper"),
    )
    if domain is None:
        return None
    value = domain.get("SystemWallpaperURL")
    return value if isinstance(value, str) else None
