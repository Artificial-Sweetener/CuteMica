"""Non-separable luminosity and color layers used by Mica."""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import NDArray

from cutemica.core.float_blur import FloatPixels
from cutemica.recipe import ResolvedMicaAltStyle

BytePixels = NDArray[np.uint8]
Luminosity = float | NDArray[np.float32]
_LUMINOSITY_WEIGHTS = np.asarray((0.3, 0.59, 0.11), dtype=np.float32)


def blend_mica_pixels(
    blurred_pixels: FloatPixels,
    style: ResolvedMicaAltStyle,
) -> BytePixels:
    """Apply Mica's luminosity layer followed by its color layer."""

    backdrop = blurred_pixels / np.float32(255.0)
    material = np.asarray(style.material_color, dtype=np.float32) / np.float32(255.0)
    luminosity_color = _set_luminosity(backdrop, _luminosity(material))
    luminous = _interpolate(backdrop, luminosity_color, style.luminosity_opacity)
    material_field = np.broadcast_to(material, luminous.shape)
    tint_color = _set_luminosity(material_field, _luminosity(luminous))
    blended = _interpolate(luminous, tint_color, style.tint_opacity)
    result = np.rint(np.clip(blended * np.float32(255.0), 0.0, 255.0)).astype(np.uint8)
    return cast(BytePixels, result)


def _set_luminosity(color: FloatPixels, target: Luminosity) -> FloatPixels:
    target_field = np.broadcast_to(target, color.shape[:2]).astype(
        np.float32, copy=False
    )
    adjusted = color + (target_field - _luminosity(color))[:, :, None]
    return _clip_color(adjusted)


def _clip_color(color: FloatPixels) -> FloatPixels:
    luminosity = _luminosity(color)
    clipped = color

    minimum = clipped.min(axis=2)
    below_zero = minimum < 0.0
    if np.any(below_zero):
        scale = np.ones_like(minimum)
        scale[below_zero] = luminosity[below_zero] / (
            luminosity[below_zero] - minimum[below_zero]
        )
        clipped = (
            luminosity[:, :, None]
            + (clipped - luminosity[:, :, None]) * scale[:, :, None]
        )

    maximum = clipped.max(axis=2)
    above_one = maximum > 1.0
    if np.any(above_one):
        scale = np.ones_like(maximum)
        scale[above_one] = (1.0 - luminosity[above_one]) / (
            maximum[above_one] - luminosity[above_one]
        )
        clipped = (
            luminosity[:, :, None]
            + (clipped - luminosity[:, :, None]) * scale[:, :, None]
        )
    return clipped


def _luminosity(color: FloatPixels) -> NDArray[np.float32]:
    return color @ _LUMINOSITY_WEIGHTS


def _interpolate(
    background: FloatPixels,
    foreground: FloatPixels,
    opacity: float,
) -> FloatPixels:
    foreground_opacity = np.float32(opacity)
    background_opacity = np.float32(1.0 - opacity)
    return cast(
        FloatPixels,
        background * background_opacity + foreground * foreground_opacity,
    )
