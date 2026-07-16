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
    *,
    paint_bounds: QRect | None = None,
) -> None:
    """Paint an opaque fallback and smoothly sampled available materials."""

    bounds = paint_bounds or dirty_rect
    dirty_area = dirty_rect.width() * dirty_rect.height()
    if _covered_area(dirty_rect, slices) + 1e-6 < dirty_area:
        painter.fillRect(dirty_rect, QColor(*fallback_color))
    if not slices:
        return
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for material_slice in slices:
        target, source = _sampling_rectangles(
            material_slice,
            materials[material_slice.screen_key],
            bounds,
        )
        painter.drawPixmap(
            target,
            materials[material_slice.screen_key],
            source,
        )


def _sampling_rectangles(
    material_slice: MaterialSlice,
    material: QPixmap,
    bounds: QRect,
) -> tuple[QRectF, QRectF]:
    """Expose one source pixel beyond window edges for stable bilinear sampling."""

    target = material_slice.target
    source = material_slice.source
    x_scale = source.width / target.width
    y_scale = source.height / target.height
    left = _edge_margin(target.x, bounds.x(), source.x)
    top = _edge_margin(target.y, bounds.y(), source.y)
    right = _edge_margin(
        target.right,
        bounds.x() + bounds.width(),
        material.width() - source.right,
    )
    bottom = _edge_margin(
        target.bottom,
        bounds.y() + bounds.height(),
        material.height() - source.bottom,
    )
    return (
        QRectF(
            target.x - left / x_scale,
            target.y - top / y_scale,
            target.width + (left + right) / x_scale,
            target.height + (top + bottom) / y_scale,
        ),
        QRectF(
            source.x - left,
            source.y - top,
            source.width + left + right,
            source.height + top + bottom,
        ),
    )


def _edge_margin(target_edge: float, bound_edge: int, available: float) -> float:
    if abs(target_edge - bound_edge) > 1e-6:
        return 0.0
    return min(1.0, max(0.0, available))


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
