"""MATE wallpaper metadata discovery."""

from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.gsettings_client import CommandRunner, GSettingsClient
from cutemica.providers.linux_session import linux_window_registration
from cutemica.providers.wallpaper_values import (
    path_from_filename,
    rgb_color,
    wallpaper_placement,
)
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource

_BACKGROUND_SCHEMA = "org.mate.background"


class MateWallpaperProvider:
    """Read MATE's single-desktop static wallpaper configuration."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._settings = GSettingsClient(runner)

    @property
    def name(self) -> str:
        return "mate"

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
        source = WallpaperSource(
            path=path_from_filename(
                self._settings.get(_BACKGROUND_SCHEMA, "picture-filename"),
                "MATE",
            ),
            placement=wallpaper_placement(
                self._settings.get(_BACKGROUND_SCHEMA, "picture-options")
            ),
            background_color=rgb_color(
                self._settings.get(_BACKGROUND_SCHEMA, "primary-color")
            ),
        )
        source.validate()
        return WallpaperSnapshot(self.name, source)
