"""GNOME-family wallpaper metadata discovery."""

from __future__ import annotations

import ast
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.linux_session import linux_window_registration
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource

CommandRunner = Callable[[tuple[str, ...]], str]


class GnomeWallpaperProvider:
    """Read static wallpaper state from GNOME-compatible GSettings schemas."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._run = runner or _run_command
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").casefold()
        cinnamon = "cinnamon" in desktop
        self._background_schema = (
            "org.cinnamon.desktop.background"
            if cinnamon
            else "org.gnome.desktop.background"
        )
        self._interface_schema = (
            "org.cinnamon.desktop.interface"
            if cinnamon
            else "org.gnome.desktop.interface"
        )

    @property
    def name(self) -> str:
        return "gnome"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            automatic_wallpaper=True,
            wallpaper_changes=True,
            per_screen_wallpaper=False,
            window_registration=linux_window_registration(),
        )

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, _bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        dark = "dark" in self._get(self._interface_schema, "color-scheme")
        uri = self._get(self._background_schema, "picture-uri")
        if dark:
            dark_uri = self._get_optional(self._background_schema, "picture-uri-dark")
            uri = dark_uri or uri
        source = WallpaperSource(
            path=_path_from_gsettings(uri),
            placement=_placement(
                _unquote(self._get(self._background_schema, "picture-options"))
            ),
            background_color=_parse_color(
                _unquote(self._get(self._background_schema, "primary-color"))
            ),
        )
        source.validate()
        return WallpaperSnapshot(self.name, source)

    def _get(self, schema: str, key: str) -> str:
        return self._run(("gsettings", "get", schema, key)).strip()

    def _get_optional(self, schema: str, key: str) -> str | None:
        try:
            value = self._get(schema, key)
        except RuntimeError:
            return None
        return value if _unquote(value) else None


def _run_command(arguments: tuple[str, ...]) -> str:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(
            f"Could not query GNOME wallpaper setting: {error}"
        ) from error
    return completed.stdout


def _unquote(value: str) -> str:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("'\"")
    return parsed if isinstance(parsed, str) else str(parsed)


def _path_from_gsettings(value: str) -> Path:
    decoded = _unquote(value)
    parsed = urlparse(decoded)
    if parsed.scheme not in {"", "file"}:
        raise RuntimeError(f"Unsupported GNOME wallpaper URI scheme: {parsed.scheme}")
    path = parsed.path if parsed.scheme else decoded
    return Path(url2pathname(unquote(path)))


def _placement(value: str) -> WallpaperPlacement:
    return {
        "wallpaper": WallpaperPlacement.TILE,
        "centered": WallpaperPlacement.CENTER,
        "scaled": WallpaperPlacement.FIT,
        "stretched": WallpaperPlacement.STRETCH,
        "zoom": WallpaperPlacement.FILL,
        "spanned": WallpaperPlacement.SPAN,
    }.get(value.casefold(), WallpaperPlacement.FILL)


def _parse_color(value: str) -> tuple[int, int, int]:
    normalized = value.lstrip("#")
    if len(normalized) == 3:
        normalized = "".join(character * 2 for character in normalized)
    if len(normalized) != 6:
        return 0, 0, 0
    try:
        return tuple(int(normalized[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return 0, 0, 0
