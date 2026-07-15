"""Select the platform wallpaper provider without coupling it to the core."""

from __future__ import annotations

import os
import sys

from cutemica.providers.wallpaper_provider import WallpaperProvider


def create_system_wallpaper_provider() -> WallpaperProvider:
    """Create the most specific automatic provider available on this host."""

    if sys.platform == "win32":
        from cutemica.providers.windows_wallpaper import WindowsWallpaperProvider

        return WindowsWallpaperProvider()
    if sys.platform == "darwin":
        from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider

        return MacOSWallpaperProvider()
    if sys.platform.startswith("linux"):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").casefold()
        if "gnome" in desktop or "unity" in desktop or "cinnamon" in desktop:
            from cutemica.providers.gnome_wallpaper import GnomeWallpaperProvider

            return GnomeWallpaperProvider()
        if "kde" in desktop or "plasma" in desktop:
            from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider

            return PlasmaWallpaperProvider()
        if "mate" in desktop:
            from cutemica.providers.mate_wallpaper import MateWallpaperProvider

            return MateWallpaperProvider()
        if "xfce" in desktop:
            from cutemica.providers.xfce_wallpaper import XfceWallpaperProvider

            return XfceWallpaperProvider()
        if "lxqt" in desktop:
            from cutemica.providers.lxqt_wallpaper import LxqtWallpaperProvider

            return LxqtWallpaperProvider()
        raise RuntimeError(
            "Automatic wallpaper discovery supports GNOME-family, KDE Plasma, "
            "MATE, XFCE, and LXQt desktops; launch with --wallpaper on this Linux "
            "desktop"
        )
    raise RuntimeError(
        "Automatic wallpaper discovery is not available on this platform; "
        "launch with --wallpaper"
    )
