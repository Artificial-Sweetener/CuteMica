from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import Self


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def union(self, other: Self) -> Self:
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        return type(self)(x, y, right - x, bottom - y)


@dataclass(frozen=True, slots=True)
class FloatRect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class WindowGeometry:
    native_rect_px: FloatRect
    local_width_dip: int
    local_height_dip: int


def bounding_rect(rectangles: tuple[Rect, ...]) -> Rect:
    if not rectangles:
        raise ValueError("At least one rectangle is required")
    return reduce(Rect.union, rectangles)


@dataclass(frozen=True, slots=True)
class ScreenBinding:
    provider_screen_id: str
    native_geometry_px: Rect
    qt_screen_name: str
    qt_geometry_dip: Rect
    device_pixel_ratio: float

    @property
    def cache_key(self) -> str:
        geometry = self.native_geometry_px
        return (
            f"{self.provider_screen_id}:"
            f"{geometry.x},{geometry.y},{geometry.width},{geometry.height}:"
            f"{self.device_pixel_ratio:.3f}"
        )

    def texture_pixels_per_dip(self, physical_texture_scale: float) -> float:
        """Convert a physical-resolution fraction to texture pixels per Qt DIP."""

        return physical_texture_scale * self.device_pixel_ratio
