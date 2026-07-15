"""Windows-compatible center-linear reduction for wallpaper surfaces."""

from __future__ import annotations

import numpy as np
from PIL import Image


def reduce_center_linear(image: Image.Image, factor: int) -> Image.Image:
    """Reduce an integer-scaled image using CuteMica's center sample footprint."""

    if factor < 2 or factor % 2 != 0:
        raise ValueError("Center-linear reduction requires an even factor")
    if image.width % factor or image.height % factor:
        raise ValueError("Image dimensions must be divisible by the reduction factor")

    pixels = np.asarray(image.convert("RGB"), dtype=np.uint16)
    first = factor // 2 - 1
    second = factor // 2
    samples = (
        pixels[first::factor, first::factor]
        + pixels[first::factor, second::factor]
        + pixels[second::factor, first::factor]
        + pixels[second::factor, second::factor]
    )
    reduced = ((samples + 1) // 4).astype(np.uint8)
    return Image.fromarray(reduced, mode="RGB")
