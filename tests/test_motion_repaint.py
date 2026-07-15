from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource
from cutemica.widgets.backdrop import PortableMicaBackdrop


def test_motion_position_uses_immediate_repaint_without_showing_window(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "wallpaper.png"
    Image.new("RGB", (32, 18), (20, 40, 80)).save(wallpaper)
    geometry = Rect(0, 0, 100, 100)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    controller = MaterialController(
        WallpaperSnapshot.single(
            "test", WallpaperSource(wallpaper, WallpaperPlacement.FILL)
        ),
        (binding,),
        ThemeController(ThemeMode.LIGHT),
    )
    parent = QWidget()
    qtbot.addWidget(parent)
    backdrop = PortableMicaBackdrop(controller, parent)
    calls = {"repaint": 0, "update": 0}
    generations: list[int] = []
    controller.generation_started.connect(generations.append)

    monkeypatch.setattr(
        backdrop,
        "repaint",
        lambda: calls.__setitem__("repaint", calls["repaint"] + 1),
    )
    monkeypatch.setattr(
        backdrop,
        "update",
        lambda: calls.__setitem__("update", calls["update"] + 1),
    )

    backdrop.present(
        WindowGeometry(FloatRect(20, 30, 100, 100), 100, 100),
        immediate=True,
    )
    backdrop.present(
        WindowGeometry(FloatRect(21, 30, 100, 100), 100, 100),
        immediate=False,
    )

    assert calls == {"repaint": 1, "update": 1}
    assert generations == []
