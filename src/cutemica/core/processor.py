import numpy as np
from PIL import Image

from cutemica.core.blur_plan import BlurBackend, resolve_blur_plan
from cutemica.core.float_blur import gaussian_blur_pixels
from cutemica.core.mica_blend import blend_mica_pixels
from cutemica.core.speed_blur import speed_blur_pixels
from cutemica.recipe import ResolvedMicaAltStyle


def process_mica_alt(
    wallpaper_field: Image.Image,
    style: ResolvedMicaAltStyle,
    texture_pixels_per_dip: float,
) -> Image.Image:
    """Apply the bounded, cacheable Mica Alt material recipe."""
    blur_plan = resolve_blur_plan(style, texture_pixels_per_dip)
    pixels = np.asarray(wallpaper_field.convert("RGB"), dtype=np.float32)
    blurred = (
        speed_blur_pixels(pixels)
        if blur_plan.backend is BlurBackend.SPEED
        else gaussian_blur_pixels(wallpaper_field, blur_plan.radius_pixels)
    )
    return Image.fromarray(blend_mica_pixels(blurred, style), mode="RGB")
