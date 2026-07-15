import numpy as np

from cutemica.core.speed_blur import speed_blur_pixels


def test_speed_blur_preserves_shape_type_and_constant_color() -> None:
    pixels = np.full((180, 240, 3), (20, 80, 160), dtype=np.float32)

    blurred = speed_blur_pixels(pixels)

    assert blurred.shape == pixels.shape
    assert blurred.dtype == np.float32
    np.testing.assert_allclose(blurred[90, 120], pixels[90, 120], atol=0.02)
