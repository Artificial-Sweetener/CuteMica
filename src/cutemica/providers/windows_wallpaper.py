from __future__ import annotations

import winreg
from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import (
    ProviderCapabilities,
    WindowRegistration,
)
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource

DESKTOP_KEY = r"Control Panel\Desktop"


class WindowsWallpaperProvider:
    """Read Windows wallpaper metadata from the user desktop settings."""

    @property
    def name(self) -> str:
        return "windows"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(True, True, False, WindowRegistration.GLOBAL)

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, _bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        return discover_windows_wallpaper()


def discover_windows_wallpaper() -> WallpaperSnapshot:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DESKTOP_KEY) as key:
        wallpaper_value, _ = winreg.QueryValueEx(key, "WallPaper")
        style_value, _ = winreg.QueryValueEx(key, "WallpaperStyle")
        tile_value, _ = winreg.QueryValueEx(key, "TileWallpaper")

    path = Path(str(wallpaper_value))
    if not path.is_file():
        transcoded = (
            Path.home() / "AppData/Local/Microsoft/Windows/Themes/TranscodedWallpaper"
        )
        path = transcoded if transcoded.is_file() else path
    return WallpaperSnapshot(
        provider_name="windows",
        default_source=WallpaperSource(
            path=path,
            placement=_placement(str(style_value), str(tile_value)),
        ),
    )


def _placement(style: str, tiled: str) -> WallpaperPlacement:
    if tiled == "1":
        return WallpaperPlacement.TILE
    return {
        "22": WallpaperPlacement.SPAN,
        "10": WallpaperPlacement.FILL,
        "6": WallpaperPlacement.FIT,
        "2": WallpaperPlacement.STRETCH,
        "0": WallpaperPlacement.CENTER,
    }.get(style, WallpaperPlacement.FILL)
