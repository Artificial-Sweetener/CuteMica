"""Float-preserving, mirrored Gaussian approximation for material textures."""

from __future__ import annotations

from math import floor, sqrt
from typing import Literal, cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image

FloatPixels = NDArray[np.float32]

_PASSES = 3


def gaussian_blur_pixels(image: Image.Image, radius: float) -> FloatPixels:
    """Blur RGB pixels without quantizing between the separable box passes."""

    pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
    if radius <= 0:
        return pixels

    box_radius = _gaussian_box_radius(radius)
    for _ in range(_PASSES):
        pixels = _box_blur_axis(pixels, box_radius, axis=1)
    for _ in range(_PASSES):
        pixels = _box_blur_axis(pixels, box_radius, axis=0)
    return pixels


def gaussian_blur_support_pixels(radius: float) -> int:
    """Return the source-pixel support required by all box passes."""

    if radius <= 0:
        return 0
    return _PASSES * (int(_gaussian_box_radius(radius)) + 1)


def _gaussian_box_radius(radius: float) -> float:
    variance = radius * radius / _PASSES
    box_length = sqrt(12.0 * variance + 1.0)
    integer_radius = floor((box_length - 1.0) / 2.0)
    numerator = (2 * integer_radius + 1) * (
        integer_radius * (integer_radius + 1) - 3.0 * variance
    )
    denominator = 6.0 * (variance - (integer_radius + 1) ** 2)
    return integer_radius + numerator / denominator


def _box_blur_axis(
    pixels: FloatPixels,
    radius: float,
    axis: Literal[0, 1],
) -> FloatPixels:
    working = np.swapaxes(pixels, 0, 1) if axis == 0 else pixels
    height, width, channels = working.shape
    integer_radius = int(radius)
    fractional_radius = np.float32(radius - integer_radius)
    normalization = np.float32(2.0 * radius + 1.0)
    padded = np.pad(
        working,
        ((0, 0), (integer_radius + 1, integer_radius + 1), (0, 0)),
        mode="symmetric",
    )
    cumulative = np.concatenate(
        (
            np.zeros((height, 1, channels), dtype=np.float32),
            np.cumsum(padded, axis=1, dtype=np.float32),
        ),
        axis=1,
    )
    far_offset = 2 * integer_radius + 2
    interior = (
        cumulative[:, far_offset : far_offset + width] - cumulative[:, 1 : width + 1]
    )
    endpoints = padded[:, :width] + padded[:, far_offset : far_offset + width]
    blurred = (interior + fractional_radius * endpoints) / normalization
    result = np.swapaxes(blurred, 0, 1) if axis == 0 else blurred
    return cast(FloatPixels, result)
