"""Select the host adapter that snapshots a window's native client geometry."""

from __future__ import annotations

import sys
from typing import Protocol

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from cutemica.geometry import ScreenBinding, WindowGeometry
from cutemica.providers.capabilities import WindowRegistration


class WindowGeometryProvider(Protocol):
    @property
    def registration(self) -> WindowRegistration:
        """Describe the coordinate contract used by snapshots."""

    def snapshot(self, window: QWidget) -> WindowGeometry:
        """Return one internally consistent native/local geometry snapshot."""


def create_window_geometry_provider(
    bindings: tuple[ScreenBinding, ...],
) -> WindowGeometryProvider:
    """Create the native adapter available on the current host."""

    if sys.platform == "win32" and QGuiApplication.platformName() == "windows":
        from cutemica.providers.windows_window_geometry import (
            WindowsWindowGeometryProvider,
        )

        return WindowsWindowGeometryProvider()

    if QGuiApplication.platformName().casefold().startswith("wayland"):
        from cutemica.providers.wayland_window_geometry import (
            WaylandWindowGeometryProvider,
        )

        return WaylandWindowGeometryProvider(bindings)

    from cutemica.providers.qt_window_geometry import QtWindowGeometryProvider

    return QtWindowGeometryProvider(bindings)
