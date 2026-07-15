import sys

import pytest

from cutemica.providers import system_wallpaper
from cutemica.providers.gnome_wallpaper import GnomeWallpaperProvider
from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider


def test_linux_selects_gnome_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")

    provider = system_wallpaper.create_system_wallpaper_provider()

    assert isinstance(provider, GnomeWallpaperProvider)


def test_linux_selects_plasma_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")

    provider = system_wallpaper.create_system_wallpaper_provider()

    assert isinstance(provider, PlasmaWallpaperProvider)
