import os
from pathlib import Path

from PIL import Image
from PySide6.QtGui import QPixmap
from pytestqt.qtbot import QtBot

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.recipe import MicaAltRecipe
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource


def test_controller_generates_material_off_thread(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    wallpaper_path = tmp_path / "wallpaper.png"
    Image.new("RGB", (320, 180), (30, 100, 180)).save(wallpaper_path)
    geometry = Rect(0, 0, 200, 100)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    theme = ThemeController(ThemeMode.LIGHT)
    controller = MaterialController(
        WallpaperSnapshot.single(
            "test", WallpaperSource(wallpaper_path, WallpaperPlacement.FILL)
        ),
        (binding,),
        theme,
    )

    with qtbot.waitSignal(controller.material_ready, timeout=3_000) as material:
        controller.refresh()

    assert material.args[0] == binding.cache_key
    assert isinstance(material.args[1], QPixmap)
    assert material.args[1].size().width() == round(
        geometry.width * MicaAltRecipe().texture_scale_for(binding.device_pixel_ratio)
    )
    assert material.args[2] > 0


def test_controller_regenerates_when_stable_wallpaper_path_changes(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    wallpaper_path = tmp_path / "changing.png"
    Image.new("RGB", (64, 36), (30, 100, 180)).save(wallpaper_path)
    geometry = Rect(0, 0, 64, 36)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    snapshot = WallpaperSnapshot.single(
        "test", WallpaperSource(wallpaper_path, WallpaperPlacement.FILL)
    )
    controller = MaterialController(
        snapshot,
        (binding,),
        ThemeController(ThemeMode.LIGHT),
    )
    previous = wallpaper_path.stat()
    Image.new("RGB", (64, 36), (180, 100, 30)).save(wallpaper_path)
    os.utime(
        wallpaper_path,
        ns=(previous.st_atime_ns, previous.st_mtime_ns + 1_000_000_000),
    )

    with qtbot.waitSignal(controller.wallpaper_changed, timeout=500):
        controller.set_wallpaper(snapshot)
