"""Conversions shared by Linux desktop wallpaper providers."""

from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from cutemica.enums import WallpaperPlacement
from cutemica.providers.gsettings_client import decode_string


def path_from_uri(value: str, desktop: str) -> Path:
    """Convert a GSettings file URI into a validated path value."""

    decoded = decode_string(value)
    if not decoded:
        raise RuntimeError(f"{desktop} has no wallpaper image configured")
    parsed = urlparse(decoded)
    if parsed.scheme not in {"", "file"}:
        raise RuntimeError(f"Unsupported {desktop} wallpaper URI: {parsed.scheme}")
    path = parsed.path if parsed.scheme else decoded
    return Path(url2pathname(unquote(path)))


def path_from_filename(value: str, desktop: str) -> Path:
    """Convert a GSettings filename into a non-empty path value."""

    decoded = decode_string(value)
    if not decoded:
        raise RuntimeError(f"{desktop} has no wallpaper image configured")
    return Path(decoded)


def wallpaper_placement(value: str) -> WallpaperPlacement:
    """Translate common freedesktop wallpaper placement names."""

    return {
        "wallpaper": WallpaperPlacement.TILE,
        "centered": WallpaperPlacement.CENTER,
        "scaled": WallpaperPlacement.FIT,
        "stretched": WallpaperPlacement.STRETCH,
        "zoom": WallpaperPlacement.FILL,
        "spanned": WallpaperPlacement.SPAN,
    }.get(decode_string(value).casefold(), WallpaperPlacement.FILL)


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
