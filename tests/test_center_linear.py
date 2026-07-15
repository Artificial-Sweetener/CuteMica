import numpy as np
from PIL import Image

from cutemica.core.center_linear import reduce_center_linear


def test_center_linear_reduction_uses_the_central_two_by_two_samples() -> None:
    pixels = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)

    reduced = np.asarray(reduce_center_linear(Image.fromarray(pixels), 4))
    expected = (
        pixels[1::4, 1::4].astype(np.uint16)
        + pixels[1::4, 2::4]
        + pixels[2::4, 1::4]
        + pixels[2::4, 2::4]
        + 1
    ) // 4

    np.testing.assert_array_equal(reduced, expected.astype(np.uint8))
