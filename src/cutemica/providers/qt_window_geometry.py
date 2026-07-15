"""Portable Qt fallback for hosts with continuous global DIP geometry."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget

from cutemica.geometry import FloatRect, ScreenBinding, WindowGeometry
from cutemica.providers.capabilities import WindowRegistration


class QtWindowGeometryProvider:
    def __init__(self, bindings: tuple[ScreenBinding, ...]) -> None:
        self._bindings = bindings

    @property
    def registration(self) -> WindowRegistration:
        return WindowRegistration.GLOBAL

    def snapshot(self, window: QWidget) -> WindowGeometry:
        """Map Qt global DIPs through the window's current screen binding."""

        origin = window.mapToGlobal(QPoint(0, 0))
        screen_name = window.screen().name()
        anchor = next(
            (
                binding
                for binding in self._bindings
                if binding.qt_screen_name == screen_name
            ),
            self._bindings[0],
        )
        qt_screen = anchor.qt_geometry_dip
        native_screen = anchor.native_geometry_px
        scale = anchor.device_pixel_ratio
        return WindowGeometry(
            FloatRect(
                native_screen.x + (origin.x() - qt_screen.x) * scale,
                native_screen.y + (origin.y() - qt_screen.y) * scale,
                window.width() * scale,
                window.height() * scale,
            ),
            window.width(),
            window.height(),
        )
