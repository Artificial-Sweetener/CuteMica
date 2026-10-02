"""Conversions shared by Linux desktop wallpaper providers."""

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from cutemica.enums import WallpaperPlacement
from cutemica.providers.gsettings_client import decode_string


def path_from_uri(value: str, desktop: str) -> Path:
    """Preserve a literal filename or decode a local file URI exactly once."""

    if not value:
        raise RuntimeError(f"{desktop} has no wallpaper image configured")
    if Path(value).is_absolute():
        return Path(value)
    parsed = urlparse(value)
    if parsed.scheme not in {"", "file"}:
        raise RuntimeError(f"Unsupported {desktop} wallpaper URI: {parsed.scheme}")
    if parsed.scheme == "file":
        if parsed.netloc.casefold() not in {"", "localhost"}:
            raise RuntimeError(f"{desktop} wallpaper URI refers to a remote host")
        return Path(url2pathname(parsed.path))
    return Path(value)


def path_from_filename(value: str, desktop: str) -> Path:
    """Convert a GSettings filename into a non-empty path value."""

    decoded = decode_string(value)
    if not decoded:
        raise RuntimeError(f"{desktop} has no wallpaper image configured")
    return Path(decoded)


def wallpaper_placement(value: str) -> WallpaperPlacement:
    """Translate common freedesktop wallpaper placement names."""

    placement = decode_string(value).casefold()
    if placement == "none":
        raise RuntimeError("Desktop is configured to display a color without an image")
    return {
        "wallpaper": WallpaperPlacement.TILE,
        "centered": WallpaperPlacement.CENTER,
        "scaled": WallpaperPlacement.FIT,
        "stretched": WallpaperPlacement.STRETCH,
        "zoom": WallpaperPlacement.FILL,
        "spanned": WallpaperPlacement.SPAN,
    }.get(placement, WallpaperPlacement.FILL)


def rgb_color(value: str) -> tuple[int, int, int]:
    """Parse a GSettings hexadecimal color with a safe black fallback."""

    normalized = decode_string(value).lstrip("#")
    if len(normalized) == 3:
        normalized = "".join(character * 2 for character in normalized)
    if len(normalized) != 6:
        return 0, 0, 0
    try:
        components = tuple(
            int(normalized[index : index + 2], 16) for index in (0, 2, 4)
        )
    except ValueError:
        return 0, 0, 0
    return components  # type: ignore[return-value]
