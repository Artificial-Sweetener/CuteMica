"""Native-screen fixture and deterministic materials for drag validation."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen, QPixmap

from cutemica.geometry import Rect, ScreenBinding
from cutemica.recipe import MicaAltRecipe


def split_drag_bindings(primary: ScreenBinding) -> tuple[ScreenBinding, ScreenBinding]:
    """Split one real display into two deterministic material regions."""

    native = primary.native_geometry_px
    left_width = native.width // 2
    right_width = native.width - left_width
    return (
        _drag_binding(
            primary, "left", Rect(native.x, native.y, left_width, native.height)
        ),
        _drag_binding(
            primary,
            "right",
            Rect(native.x + left_width, native.y, right_width, native.height),
        ),
    )


def create_drag_materials(
    bindings: tuple[ScreenBinding, ...],
) -> dict[str, QPixmap]:
    """Create richly patterned textures at the production texture scale."""

    recipe = MicaAltRecipe()
    return {
        binding.cache_key: QPixmap.fromImage(
            _material_image(
                binding,
                recipe.texture_scale_for(binding.device_pixel_ratio),
                index,
            )
        )
        for index, binding in enumerate(bindings)
    }


def stability_positions(
    primary: ScreenBinding,
    window_width: int,
    window_height: int,
    frame_count: int,
) -> tuple[QPoint, ...]:
    """Return one-DIP steps that carry the window through the synthetic seam."""

    screen = primary.qt_geometry_dip
    center = screen.x + screen.width // 2
    start_x = center - window_width // 2 - frame_count // 2
    start_x = max(screen.x + 8, start_x)
    start_x = min(start_x, screen.right - window_width - frame_count - 8)
    y = screen.y + max(8, (screen.height - window_height) // 2)
    return tuple(QPoint(start_x + frame, y) for frame in range(frame_count))


def performance_positions(
    primary: ScreenBinding,
    window_width: int,
    window_height: int,
    frame_count: int,
) -> tuple[QPoint, ...]:
    """Return a repeatable bidirectional native-window movement trajectory."""

    screen = primary.qt_geometry_dip
    margin = 12
    available = max(2, screen.width - window_width - margin * 2)
    travel = min(384, available)
    start_x = screen.x + margin + max(0, (available - travel) // 2)
    y = screen.y + max(margin, (screen.height - window_height) // 2)
    cycle = max(2, travel * 2)
    points: list[QPoint] = []
    for frame in range(frame_count):
        phase = frame % cycle
        offset = phase if phase <= travel else cycle - phase
        points.append(QPoint(start_x + offset, y))
    return tuple(points)


def _drag_binding(
    primary: ScreenBinding,
    identifier: str,
    native: Rect,
) -> ScreenBinding:
    return ScreenBinding(
        provider_screen_id=f"drag-{identifier}",
        native_geometry_px=native,
        qt_screen_name=primary.qt_screen_name,
        qt_geometry_dip=primary.qt_geometry_dip,
        device_pixel_ratio=primary.device_pixel_ratio,
    )


def _material_image(
    binding: ScreenBinding,
    texture_scale: float,
    variant: int,
) -> QImage:
    native = binding.native_geometry_px
    width = max(1, round(native.width * texture_scale))
    height = max(1, round(native.height * texture_scale))
    image = QImage(width, height, QImage.Format.Format_RGB32)
    palettes = (
        (QColor(42, 71, 154), QColor(191, 73, 126)),
        (QColor(29, 142, 121), QColor(203, 128, 47)),
    )
    start, end = palettes[variant % len(palettes)]
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0.0, start)
    gradient.setColorAt(1.0, end)
    painter = QPainter(image)
    painter.fillRect(image.rect(), gradient)
    painter.setPen(QPen(QColor(238, 214, 91), 1, Qt.PenStyle.SolidLine))
    for x in range(7 + variant * 5, width, 29):
        painter.drawLine(x, 0, x, height)
    painter.setPen(QPen(QColor(73, 210, 225), 1, Qt.PenStyle.SolidLine))
    for y in range(11 + variant * 3, height, 23):
        painter.drawLine(0, y, width, y)
    painter.end()
    return image
