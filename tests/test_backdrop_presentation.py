"""Verify active and inactive portable material presentation policy."""

from PySide6.QtGui import QPixmap
from pytestqt.qtbot import QtBot

from cutemica.widgets.backdrop import material_presentation_enabled


def test_active_window_with_material_presents_wallpaper_texture(
    qtbot: QtBot,
) -> None:
    del qtbot
    material = QPixmap(1, 1)

    assert material_presentation_enabled(True, material)


def test_inactive_window_uses_the_fallback_even_when_material_is_ready(
    qtbot: QtBot,
) -> None:
    del qtbot
    material = QPixmap(1, 1)

    assert not material_presentation_enabled(False, material)


def test_active_window_uses_fallback_until_material_is_ready() -> None:
    assert not material_presentation_enabled(True, None)
