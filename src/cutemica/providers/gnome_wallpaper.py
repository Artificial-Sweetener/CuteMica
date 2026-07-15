"""GNOME-family wallpaper metadata discovery."""

from __future__ import annotations

import os

from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.gsettings_client import CommandRunner, GSettingsClient
from cutemica.providers.linux_session import linux_window_registration
from cutemica.providers.wallpaper_values import (
    path_from_uri,
    rgb_color,
    wallpaper_placement,
)
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource


class GnomeWallpaperProvider:
    """Read static wallpaper state from GNOME-compatible GSettings schemas."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._settings = GSettingsClient(runner)
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
        color_scheme = self._settings.get_optional(
            self._interface_schema, "color-scheme"
        )
        dark = color_scheme is not None and "dark" in color_scheme
        uri = self._settings.get(self._background_schema, "picture-uri")
        if dark:
            dark_uri = self._settings.get_optional(
                self._background_schema, "picture-uri-dark"
            )
            uri = dark_uri or uri
        source = WallpaperSource(
            path=path_from_uri(uri, "GNOME-family desktop"),
            placement=wallpaper_placement(
                self._settings.get(self._background_schema, "picture-options")
            ),
            background_color=rgb_color(
                self._settings.get(self._background_schema, "primary-color")
            ),
        )
        source.validate()
        return WallpaperSnapshot(self.name, source)
