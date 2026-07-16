import sys

import pytest
from PySide6.QtWidgets import QApplication

if sys.platform != "darwin":
    pytest.skip("Native AppKit wallpaper provider", allow_module_level=True)

from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider  # noqa: E402
from cutemica.providers.qt_screens import infer_qt_screen_bindings  # noqa: E402


def test_appkit_reports_wallpaper_for_every_qt_screen(qapp: QApplication) -> None:
    bindings = infer_qt_screen_bindings(qapp.screens())

    snapshot = MacOSWallpaperProvider().discover(bindings)

    assert snapshot.per_screen
    assert len(snapshot.per_screen) == len(bindings)
    snapshot.validate()
