import sys

import pytest
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

if sys.platform != "win32":
    pytest.skip("Win32 geometry adapter test", allow_module_level=True)

from cutemica.geometry import FloatRect, Rect, ScreenBinding  # noqa: E402
from cutemica.providers import windows_window_geometry  # noqa: E402
from cutemica.providers.windows_window_geometry import (  # noqa: E402
    WindowsWindowGeometryProvider,
)
from cutemica.viewport import plan_material_slices  # noqa: E402


def test_native_snapshot_ignores_qt_geometry_during_dpi_handoff(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native_client = Rect(-220, 271, 1350, 900)
    monkeypatch.setattr(
        windows_window_geometry,
        "read_client_rect_px",
        lambda _window_handle: native_client,
    )
    window = QWidget()
    qtbot.addWidget(window)
    provider = WindowsWindowGeometryProvider()
    window.resize(900, 600)

    transitional = provider.snapshot(window)
    window.resize(1350, 900)
    remapped = provider.snapshot(window)

    assert transitional.native_rect_px == FloatRect(-220, 271, 1350, 900)
    assert transitional.local_width_dip == 900
    assert remapped.native_rect_px == transitional.native_rect_px
    assert remapped.local_width_dip == 1350


def test_dpi_handoff_changes_targets_without_jumping_material_sources(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native_client = Rect(-220, 271, 1350, 900)
    monkeypatch.setattr(
        windows_window_geometry,
        "read_client_rect_px",
        lambda _window_handle: native_client,
    )
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
    materials = {
        portrait.cache_key: (1280, 1440),
        primary.cache_key: (860, 360),
    }
    window = QWidget()
    qtbot.addWidget(window)
    provider = WindowsWindowGeometryProvider()
    window.resize(900, 600)
    transitional = plan_material_slices(
        provider.snapshot(window),
        (portrait, primary),
        materials,
    )
    window.resize(1350, 900)
    remapped = plan_material_slices(
        provider.snapshot(window),
        (portrait, primary),
        materials,
    )

    assert [item.source for item in transitional] == [item.source for item in remapped]
    assert sum(item.target.width for item in transitional) == pytest.approx(900)
    assert sum(item.target.width for item in remapped) == pytest.approx(1350)
