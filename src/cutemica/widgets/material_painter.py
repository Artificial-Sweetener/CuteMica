"""Rasterize planned CuteMica slices into an active Qt painter."""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QColor, QPainter, QPixmap

from cutemica.geometry import FloatRect
from cutemica.viewport import MaterialSlice


def paint_material_slices(
    painter: QPainter,
    dirty_rect: QRect,
    fallback_color: tuple[int, int, int],
    slices: tuple[MaterialSlice, ...],
    materials: dict[str, QPixmap],
) -> None:
    """Paint an opaque fallback and smoothly sampled available materials."""

    dirty_area = dirty_rect.width() * dirty_rect.height()
    if _covered_area(dirty_rect, slices) + 1e-6 < dirty_area:
        painter.fillRect(dirty_rect, QColor(*fallback_color))
    if not slices:
        return
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for material_slice in slices:
        painter.drawPixmap(
            _to_qrectf(material_slice.target),
            materials[material_slice.screen_key],
            _to_qrectf(material_slice.source),
        )


def _to_qrectf(rectangle: FloatRect) -> QRectF:
    return QRectF(
        rectangle.x,
        rectangle.y,
        rectangle.width,
        rectangle.height,
    )


def _covered_area(
    dirty_rect: QRect,
    slices: tuple[MaterialSlice, ...],
) -> float:
    area = 0.0
    for material_slice in slices:
        target = material_slice.target
        left = max(dirty_rect.x(), target.x)
        top = max(dirty_rect.y(), target.y)
        right = min(dirty_rect.x() + dirty_rect.width(), target.right)
        bottom = min(dirty_rect.y() + dirty_rect.height(), target.bottom)
        if right > left and bottom > top:
            area += (right - left) * (bottom - top)
    return area
