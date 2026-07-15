from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.providers.gnome_wallpaper import GnomeWallpaperProvider


def test_gnome_uses_dark_wallpaper_and_reconstructs_placement(
    tmp_path: Path,
) -> None:
    light = tmp_path / "light wallpaper.png"
    dark = tmp_path / "dark wallpaper.png"
    Image.new("RGB", (8, 8)).save(light)
    Image.new("RGB", (8, 8)).save(dark)
    values = {
        ("org.gnome.desktop.interface", "color-scheme"): "'prefer-dark'",
        ("org.gnome.desktop.background", "picture-uri"): light.as_uri(),
        ("org.gnome.desktop.background", "picture-uri-dark"): dark.as_uri(),
        ("org.gnome.desktop.background", "picture-options"): "'scaled'",
        ("org.gnome.desktop.background", "primary-color"): "'#123abc'",
    }

    def run(arguments: tuple[str, ...]) -> str:
        return values[(arguments[2], arguments[3])]

    snapshot = GnomeWallpaperProvider(run).discover(())

    assert snapshot.default_source.path == dark
    assert snapshot.default_source.placement is WallpaperPlacement.FIT
    assert snapshot.default_source.background_color == (0x12, 0x3A, 0xBC)


def test_gnome_falls_back_when_dark_specific_key_is_unavailable(
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "wallpaper.png"
    Image.new("RGB", (8, 8)).save(wallpaper)

    def run(arguments: tuple[str, ...]) -> str:
        key = arguments[3]
        if key == "picture-uri-dark":
            raise RuntimeError("missing key")
        return {
            "color-scheme": "'prefer-dark'",
            "picture-uri": wallpaper.as_uri(),
            "picture-options": "'zoom'",
            "primary-color": "'#000000'",
        }[key]

    snapshot = GnomeWallpaperProvider(run).discover(())

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.FILL


def test_cinnamon_does_not_require_gnome_color_scheme(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "cinnamon.png"
    Image.new("RGB", (8, 8)).save(wallpaper)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")

    def run(arguments: tuple[str, ...]) -> str:
        schema, key = arguments[2], arguments[3]
        if schema == "org.cinnamon.desktop.interface":
            raise RuntimeError("No such key color-scheme")
        return {
            "picture-uri": wallpaper.as_uri(),
            "picture-options": "'spanned'",
            "primary-color": "'#123abc'",
        }[key]

    snapshot = GnomeWallpaperProvider(run).discover(())

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.SPAN


def test_gnome_rejects_an_empty_wallpaper_uri() -> None:
    def run(arguments: tuple[str, ...]) -> str:
        key = arguments[3]
        return {
            "color-scheme": "'default'",
            "picture-uri": "''",
            "picture-options": "'zoom'",
            "primary-color": "'#000000'",
        }[key]

    with pytest.raises(RuntimeError, match="no wallpaper image"):
        GnomeWallpaperProvider(run).discover(())
