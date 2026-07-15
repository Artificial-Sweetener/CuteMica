import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cutemica.providers.capabilities import WindowRegistration
from cutemica.providers.qt_screens import infer_qt_screen_bindings
from cutemica.providers.window_geometry import create_window_geometry_provider


def test_native_window_geometry_smoke(qtbot: QtBot) -> None:
    platform = QGuiApplication.platformName().casefold()
    if platform not in {"xcb", "cocoa", "windows"}:
        pytest.skip("Native Qt platform smoke")
    bindings = infer_qt_screen_bindings(QGuiApplication.screens())
    provider = create_window_geometry_provider(bindings)
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(320, 180)
    window.show()
    qtbot.waitExposed(window)
    window.move(20, 20)
    snapshot = provider.snapshot(window)

    assert provider.registration is WindowRegistration.GLOBAL
    assert snapshot.local_width_dip == 320
    assert snapshot.local_height_dip == 180
