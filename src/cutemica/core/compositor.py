from __future__ import annotations

from collections.abc import Callable

from PIL import Image, ImageOps

from cutemica.core.center_linear import reduce_center_linear
from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding, bounding_rect

Resample = Image.Resampling.LANCZOS


def compose_wallpaper(
    wallpaper: Image.Image,
    placement: WallpaperPlacement,
    binding: ScreenBinding,
    all_bindings: tuple[ScreenBinding, ...],
    texture_scale: float,
    background_color: tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """Reconstruct the wallpaper field for one screen at material resolution."""
    target_size = _scaled_size(binding.native_geometry_px, texture_scale)
    rgb_wallpaper = wallpaper.convert("RGB")
    if placement is WallpaperPlacement.SPAN:
        return _compose_span(rgb_wallpaper, binding, all_bindings, target_size)

    if placement in {WallpaperPlacement.CENTER, WallpaperPlacement.TILE}:
        native = binding.native_geometry_px
        source_scale = min(
            target_size[0] / native.width, target_size[1] / native.height
        )
        source_size = (
            max(1, round(rgb_wallpaper.width * source_scale)),
            max(1, round(rgb_wallpaper.height * source_scale)),
        )
        rgb_wallpaper = rgb_wallpaper.resize(source_size, Resample)

    compositors: dict[
        WallpaperPlacement, Callable[[Image.Image, tuple[int, int]], Image.Image]
    ] = {
        WallpaperPlacement.FILL: _fill,
        WallpaperPlacement.FIT: lambda image, size: _fit(image, size, background_color),
        WallpaperPlacement.STRETCH: _stretch,
        WallpaperPlacement.CENTER: lambda image, size: _center(
            image, size, background_color
        ),
        WallpaperPlacement.TILE: _tile,
    }
    return compositors[placement](rgb_wallpaper, target_size)


def _compose_span(
    wallpaper: Image.Image,
    binding: ScreenBinding,
    all_bindings: tuple[ScreenBinding, ...],
    target_size: tuple[int, int],
) -> Image.Image:
    virtual = bounding_rect(tuple(item.native_geometry_px for item in all_bindings))
    native = binding.native_geometry_px
    virtual_size = (virtual.width, virtual.height)
    field = (
        wallpaper if wallpaper.size == virtual_size else _fill(wallpaper, virtual_size)
    )
    left = native.x - virtual.x
    top = native.y - virtual.y
    native_screen = field.crop((left, top, left + native.width, top + native.height))
    x_factor = native.width // target_size[0]
    y_factor = native.height // target_size[1]
    if (
        x_factor == y_factor
        and x_factor % 2 == 0
        and native.width == target_size[0] * x_factor
        and native.height == target_size[1] * y_factor
    ):
        return reduce_center_linear(native_screen, x_factor)
    return native_screen.resize(target_size, Resample)


def _scaled_size(rect: Rect, scale: float) -> tuple[int, int]:
    if not 0 < scale <= 1:
        raise ValueError("Texture scale must be greater than zero and at most one")
    return max(1, round(rect.width * scale)), max(1, round(rect.height * scale))


def _fill(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Resample, centering=(0.5, 0.5))


def _fit(
    image: Image.Image,
    size: tuple[int, int],
    background_color: tuple[int, int, int] | None = None,
) -> Image.Image:
    fitted = ImageOps.contain(image, size, method=Resample)
    canvas = Image.new("RGB", size, background_color or _edge_average(image))
    canvas.paste(fitted, _center_offset(size, fitted.size))
    return canvas


def _stretch(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return image.resize(size, Resample)


def _center(
    image: Image.Image,
    size: tuple[int, int],
    background_color: tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    canvas = Image.new("RGB", size, background_color)
    source = image.copy()
    if source.width > size[0] or source.height > size[1]:
        left = max(0, (source.width - size[0]) // 2)
        top = max(0, (source.height - size[1]) // 2)
        source = source.crop((left, top, left + size[0], top + size[1]))
    canvas.paste(source, _center_offset(size, source.size))
    return canvas


def _tile(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size)
    for y in range(0, size[1], image.height):
        for x in range(0, size[0], image.width):
            canvas.paste(image, (x, y))
    return canvas


def _center_offset(
    container: tuple[int, int], content: tuple[int, int]
) -> tuple[int, int]:
    return (container[0] - content[0]) // 2, (container[1] - content[1]) // 2


def _edge_average(image: Image.Image) -> tuple[int, int, int]:
    sample = ImageOps.fit(image, (1, 1), method=Resample).getpixel((0, 0))
    if not isinstance(sample, tuple) or len(sample) < 3:
        return 0, 0, 0
    return int(sample[0]), int(sample[1]), int(sample[2])
