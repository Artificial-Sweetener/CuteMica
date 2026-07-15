from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.capabilities import WindowRegistration
from cutemica.providers.wayland_window_geometry import WaylandWindowGeometryProvider


def test_wayland_uses_stable_screen_local_geometry(qtbot: QtBot) -> None:
    screen = QGuiApplication.primaryScreen()
    assert screen is not None
    geometry = Rect(-100, 25, 1000, 800)
    binding = ScreenBinding("screen", geometry, screen.name(), geometry, 1.25)
    provider = WaylandWindowGeometryProvider((binding,))
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(320, 180)

    first = provider.snapshot(window)
    window.move(400, 300)
    second = provider.snapshot(window)

    assert provider.registration is WindowRegistration.SCREEN_LOCAL
    assert first.native_rect_px == second.native_rect_px
    assert first.native_rect_px.x == -100
    assert first.native_rect_px.y == 25
    assert first.native_rect_px.width == 400
