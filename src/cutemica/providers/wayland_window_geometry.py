"""Honest screen-local fallback for standard Wayland clients."""

from PySide6.QtWidgets import QWidget

from cutemica.geometry import FloatRect, ScreenBinding, WindowGeometry
from cutemica.providers.capabilities import WindowRegistration


class WaylandWindowGeometryProvider:
    """Anchor material to the current screen without inventing global position."""

    def __init__(self, bindings: tuple[ScreenBinding, ...]) -> None:
        if not bindings:
            raise ValueError("Wayland geometry requires at least one screen binding")
        self._bindings = bindings

    @property
    def registration(self) -> WindowRegistration:
        return WindowRegistration.SCREEN_LOCAL

    def snapshot(self, window: QWidget) -> WindowGeometry:
        """Return a stable screen-local rectangle for the current surface."""

        screen_name = window.screen().name()
        binding = next(
            (item for item in self._bindings if item.qt_screen_name == screen_name),
            self._bindings[0],
        )
        scale = binding.device_pixel_ratio
        native = binding.native_geometry_px
        return WindowGeometry(
            FloatRect(
                native.x,
                native.y,
                window.width() * scale,
                window.height() * scale,
            ),
            window.width(),
            window.height(),
        )
