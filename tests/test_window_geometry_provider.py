import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.qt_window_geometry import QtWindowGeometryProvider
from cutemica.providers.window_geometry import create_window_geometry_provider


def test_offscreen_platform_selects_the_portable_geometry_adapter(
    qtbot: QtBot,
) -> None:
    if QGuiApplication.platformName() != "offscreen":
        pytest.skip("Geometry selection test requires Qt's offscreen platform")
    screen = QGuiApplication.primaryScreen()
    assert screen is not None
    geometry = screen.geometry()
    rect = Rect(
        geometry.x(),
        geometry.y(),
        geometry.width(),
        geometry.height(),
    )
    binding = ScreenBinding("offscreen", rect, screen.name(), rect, 1.0)

    provider = create_window_geometry_provider((binding,))
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(320, 180)
    snapshot = provider.snapshot(window)

    assert isinstance(provider, QtWindowGeometryProvider)
    assert snapshot.local_width_dip == 320
    assert snapshot.local_height_dip == 180
