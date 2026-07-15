"""Prepare a bounded, neighbor-aware wallpaper field for material blur."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from cutemica.core.blur_plan import BlurPlan
from cutemica.core.compositor import compose_wallpaper
from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding


@dataclass(frozen=True, slots=True)
class PreparedMaterialField:
    image: Image.Image
    material_box: tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class FieldPadding:
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def is_empty(self) -> bool:
        return not any((self.left, self.top, self.right, self.bottom))


def prepare_material_field(
    wallpaper: Image.Image,
    placement: WallpaperPlacement,
    binding: ScreenBinding,
    all_bindings: tuple[ScreenBinding, ...],
    texture_scale: float,
    blur_plan: BlurPlan,
    background_color: tuple[int, int, int] = (0, 0, 0),
    neighbor_halo: bool = True,
) -> PreparedMaterialField:
    """Pad one screen and replace only halo regions occupied by neighbors."""

    material = compose_wallpaper(
        wallpaper,
        placement,
        binding,
        all_bindings,
        texture_scale,
        background_color,
    )
    padding = (
        _neighbor_padding(
            binding,
            all_bindings,
            texture_scale,
            blur_plan.support_pixels,
        )
        if neighbor_halo
        else FieldPadding()
    )
    if padding.is_empty:
        return PreparedMaterialField(material, (0, 0, *material.size))

    pixels = np.asarray(material.convert("RGB"), dtype=np.uint8)
    padded = np.pad(
        pixels,
        (
            (padding.top, padding.bottom),
            (padding.left, padding.right),
            (0, 0),
        ),
        mode=blur_plan.padding_mode,
    )
    field = Image.fromarray(padded)
    for neighbor in all_bindings:
        if neighbor == binding:
            continue
        _paste_neighbor(
            field,
            wallpaper,
            placement,
            binding,
            neighbor,
            all_bindings,
            texture_scale,
            padding,
            background_color,
        )
    box = (
        padding.left,
        padding.top,
        padding.left + material.width,
        padding.top + material.height,
    )
    return PreparedMaterialField(field, box)


def _paste_neighbor(
    field: Image.Image,
    wallpaper: Image.Image,
    placement: WallpaperPlacement,
    binding: ScreenBinding,
    neighbor: ScreenBinding,
    all_bindings: tuple[ScreenBinding, ...],
    texture_scale: float,
    padding: FieldPadding,
    background_color: tuple[int, int, int],
) -> None:
    native = binding.native_geometry_px
    intersection = _intersection(
        native.x - padding.left / texture_scale,
        native.y - padding.top / texture_scale,
        native.right + padding.right / texture_scale,
        native.bottom + padding.bottom / texture_scale,
        neighbor.native_geometry_px,
    )
    if intersection is None:
        return
    neighbor_image = compose_wallpaper(
        wallpaper,
        placement,
        neighbor,
        all_bindings,
        texture_scale,
        background_color,
    )
    neighbor_native = neighbor.native_geometry_px
    source_box = _scaled_box(intersection, neighbor_native, texture_scale)
    patch = neighbor_image.crop(source_box)
    destination_x = round(padding.left + (intersection[0] - native.x) * texture_scale)
    destination_y = round(padding.top + (intersection[1] - native.y) * texture_scale)
    field.paste(patch, (destination_x, destination_y))


def _neighbor_padding(
    binding: ScreenBinding,
    all_bindings: tuple[ScreenBinding, ...],
    texture_scale: float,
    support: int,
) -> FieldPadding:
    if support == 0:
        return FieldPadding()
    native = binding.native_geometry_px
    physical_support = support / texture_scale
    left = top = right = bottom = 0
    for neighbor in all_bindings:
        if neighbor == binding:
            continue
        intersection = _intersection(
            native.x - physical_support,
            native.y - physical_support,
            native.right + physical_support,
            native.bottom + physical_support,
            neighbor.native_geometry_px,
        )
        if intersection is None:
            continue
        left = support if intersection[0] < native.x else left
        top = support if intersection[1] < native.y else top
        right = support if intersection[2] > native.right else right
        bottom = support if intersection[3] > native.bottom else bottom
    return FieldPadding(left, top, right, bottom)


def _scaled_box(
    region: tuple[float, float, float, float],
    origin: Rect,
    scale: float,
) -> tuple[int, int, int, int]:
    return (
        round((region[0] - origin.x) * scale),
        round((region[1] - origin.y) * scale),
        round((region[2] - origin.x) * scale),
        round((region[3] - origin.y) * scale),
    )


def _intersection(
    left: float,
    top: float,
    right: float,
    bottom: float,
    rectangle: Rect,
) -> tuple[float, float, float, float] | None:
    intersection = (
        max(left, rectangle.x),
        max(top, rectangle.y),
        min(right, rectangle.right),
        min(bottom, rectangle.bottom),
    )
    if intersection[2] <= intersection[0] or intersection[3] <= intersection[1]:
        return None
    return intersection
