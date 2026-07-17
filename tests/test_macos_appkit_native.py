import os
import sys

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

if sys.platform != "darwin":
    pytest.skip("Native AppKit wallpaper provider", allow_module_level=True)

from cutemica.controller import MaterialController  # noqa: E402
from cutemica.enums import ThemeMode  # noqa: E402
from cutemica.providers.macos_appkit import read_macos_desktops  # noqa: E402
from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider  # noqa: E402
from cutemica.providers.qt_screens import infer_qt_screen_bindings  # noqa: E402
from cutemica.theme import ThemeController  # noqa: E402


def test_appkit_reports_wallpaper_for_every_qt_screen(qapp: QApplication) -> None:
    bindings = infer_qt_screen_bindings(qapp.screens())

    snapshot = MacOSWallpaperProvider().discover(bindings)

    assert snapshot.per_screen
    assert len(snapshot.per_screen) == len(bindings)
    snapshot.validate()
    for item in snapshot.per_screen:
        with Image.open(item.source.path) as image:
            image.load()
            assert image.width > 0
            assert image.height > 0


def test_native_default_generates_material_through_shared_renderer(
    qapp: QApplication,
    qtbot: QtBot,
) -> None:
    if os.environ.get("CUTEMICA_MACOS_NATIVE_DEFAULT") != "1":
        pytest.skip("requires activated native macOS wallpaper mode")
    records = read_macos_desktops()
    assert records
    assert all(record.path.suffix.casefold() == ".heic" for record in records)
    bindings = infer_qt_screen_bindings(qapp.screens())
    snapshot = MacOSWallpaperProvider().discover(bindings)
    assert all(
        item.source.source_kind == "macos-native-still" for item in snapshot.per_screen
    )
    controller = MaterialController(
        snapshot,
        bindings,
        ThemeController(ThemeMode.AUTO),
    )
    errors: list[str] = []
    controller.error.connect(errors.append)

    with qtbot.waitSignal(controller.material_ready, timeout=15_000):
        controller.refresh()

    assert not errors
