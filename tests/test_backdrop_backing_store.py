from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource
from cutemica.widgets.backdrop import PortableMicaBackdrop


def test_backdrop_declares_opaque_non_erasing_backing_store_behavior(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "wallpaper.png"
    Image.new("RGB", (16, 9)).save(wallpaper)
    geometry = Rect(0, 0, 100, 100)
    controller = MaterialController(
        WallpaperSnapshot.single(
            "test", WallpaperSource(wallpaper, WallpaperPlacement.FILL)
        ),
        (ScreenBinding("screen", geometry, "screen", geometry, 1.0),),
        ThemeController(ThemeMode.LIGHT),
    )
    parent = QWidget()
    qtbot.addWidget(parent)
    backdrop = PortableMicaBackdrop(controller, parent)

    assert backdrop.testAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
    assert backdrop.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    assert not backdrop.autoFillBackground()
