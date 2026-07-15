import numpy as np
from PIL import Image

from cutemica.core.float_blur import gaussian_blur_pixels


def test_blur_preserves_fractional_values_until_material_blending() -> None:
    source = Image.new("RGB", (9, 1), "black")
    source.putpixel((4, 0), (255, 255, 255))

    blurred = gaussian_blur_pixels(source, radius=2.0)

    assert blurred.dtype == np.float32
    assert np.any(blurred != np.rint(blurred))


def test_mirrored_blur_keeps_a_constant_field_constant() -> None:
    source = Image.new("RGB", (7, 5), (23, 47, 89))

    blurred = gaussian_blur_pixels(source, radius=12.0)

    assert np.allclose(blurred, (23, 47, 89), atol=0.001)
