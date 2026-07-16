import sys

import pytest
from PySide6.QtGui import QGuiApplication

if sys.platform != "win32":
    pytest.skip("Native Windows wallpaper provider", allow_module_level=True)

from cutemica.providers.qt_screens import infer_qt_screen_bindings  # noqa: E402
from cutemica.providers.windows_wallpaper import (  # noqa: E402
    WindowsWallpaperProvider,
)


def test_windows_api_reports_wallpaper_for_every_qt_screen() -> None:
    bindings = infer_qt_screen_bindings(QGuiApplication.screens())

    snapshot = WindowsWallpaperProvider().discover(bindings)

    assert snapshot.per_screen
    assert len(snapshot.per_screen) == len(bindings)
    snapshot.validate()
