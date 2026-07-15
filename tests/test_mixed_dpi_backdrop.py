import os
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource
from cutemica.widgets.backdrop import PortableMicaBackdrop


@pytest.mark.skipif(
    os.environ.get("QT_QPA_PLATFORM") != "offscreen",
    reason="Backdrop rendering is restricted to Qt's offscreen platform",
)
def test_real_backdrop_covers_mixed_dpi_monitor_boundary(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "wallpaper.png"
    Image.new("RGB", (16, 9)).save(wallpaper)
    portrait = ScreenBinding(
        "portrait",
        Rect(-2560, -242, 2560, 2880),
        "portrait",
        Rect(-2560, -242, 1707, 1920),
        1.5,
    )
    primary = ScreenBinding(
        "primary",
        Rect(0, 0, 3440, 1440),
        "primary",
        Rect(0, 0, 3440, 1440),
        1.0,
    )
    controller = MaterialController(
        WallpaperSnapshot.single(
            "test", WallpaperSource(wallpaper, WallpaperPlacement.FILL)
        ),
        (portrait, primary),
        ThemeController(ThemeMode.DARK),
    )
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(600, 400)
    backdrop = PortableMicaBackdrop(controller, window)
    backdrop.setGeometry(window.rect())
    portrait_material = QPixmap(128, 144)
    primary_material = QPixmap(86, 36)
    portrait_material.fill(QColor(200, 20, 30))
    primary_material.fill(QColor(30, 40, 210))
    backdrop.set_material(portrait.cache_key, portrait_material)
    backdrop.set_material(primary.cache_key, primary_material)
    window.show()
    window.activateWindow()
    QApplication.processEvents()

    native_rect = FloatRect(-300, 100, 900, 600)
    backdrop.present(WindowGeometry(native_rect, 600, 400), immediate=True)
    rendered = backdrop.grab().toImage()

    fallback = QColor(*controller.fallback_color)
    assert rendered.pixelColor(100, 200) == QColor(200, 20, 30)
    assert rendered.pixelColor(400, 200) == QColor(30, 40, 210)
    assert all(rendered.pixelColor(x, 200) != fallback for x in range(rendered.width()))

    window.resize(900, 600)
    backdrop.setGeometry(window.rect())
    backdrop.present(WindowGeometry(native_rect, 900, 600), immediate=True)
    switched_render = backdrop.grab().toImage()

    assert switched_render.pixelColor(150, 300) == QColor(200, 20, 30)
    assert switched_render.pixelColor(500, 300) == QColor(30, 40, 210)
    assert all(
        switched_render.pixelColor(x, 300) != fallback
        for x in range(switched_render.width())
    )
