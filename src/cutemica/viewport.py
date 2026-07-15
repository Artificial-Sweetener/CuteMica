"""Pure desktop-to-material slice planning for cached backdrop presentation."""

from __future__ import annotations

from dataclasses import dataclass

from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry


@dataclass(frozen=True, slots=True)
class MaterialSlice:
    screen_key: str
    target: FloatRect
    source: FloatRect


def plan_material_slices(
    window: WindowGeometry,
    bindings: tuple[ScreenBinding, ...],
    material_sizes: dict[str, tuple[int, int]],
) -> tuple[MaterialSlice, ...]:
    """Map native screen intersections into local and material coordinates."""

    window_native_px = window.native_rect_px
    x_to_local = window.local_width_dip / window_native_px.width
    y_to_local = window.local_height_dip / window_native_px.height
    slices: list[MaterialSlice] = []
    for binding in bindings:
        material_size = material_sizes.get(binding.cache_key)
        screen = binding.native_geometry_px
        intersection = _intersection(window_native_px, screen)
        if material_size is None or intersection is None:
            continue
        x_scale = material_size[0] / screen.width
        y_scale = material_size[1] / screen.height
        slices.append(
            MaterialSlice(
                screen_key=binding.cache_key,
                target=FloatRect(
                    (intersection.x - window_native_px.x) * x_to_local,
                    (intersection.y - window_native_px.y) * y_to_local,
                    intersection.width * x_to_local,
                    intersection.height * y_to_local,
                ),
                source=FloatRect(
                    (intersection.x - screen.x) * x_scale,
                    (intersection.y - screen.y) * y_scale,
                    intersection.width * x_scale,
                    intersection.height * y_scale,
                ),
            )
        )
    return tuple(slices)


def _intersection(first: FloatRect, second: Rect) -> FloatRect | None:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.right, second.right)
    bottom = min(first.bottom, second.bottom)
    if right <= left or bottom <= top:
        return None
    return FloatRect(left, top, right - left, bottom - top)
