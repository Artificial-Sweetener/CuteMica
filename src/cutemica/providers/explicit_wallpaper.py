"""Provider for application-supplied wallpaper images."""

from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import (
    ProviderCapabilities,
    WindowRegistration,
)
from cutemica.wallpaper import WallpaperSnapshot, wallpaper_from_path


class ExplicitWallpaperProvider:
    """Publish the same explicit wallpaper to every display."""

    def __init__(
        self,
        path: Path,
        placement: WallpaperPlacement = WallpaperPlacement.SPAN,
    ) -> None:
        self._path = path
        self._placement = placement

    @property
    def name(self) -> str:
        return "explicit"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            automatic_wallpaper=False,
            wallpaper_changes=False,
            per_screen_wallpaper=False,
            window_registration=WindowRegistration.GLOBAL,
        )

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, _bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        return wallpaper_from_path(self._path, self._placement)
