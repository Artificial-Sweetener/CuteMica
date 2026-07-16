import numpy as np
import pytest
from PySide6.QtGui import QImage

from cutemica.geometry import FloatRect, WindowGeometry
from cutemica.performance.drag_frames import (
    CapturedDragFrame,
    analyze_drag_frames,
    captured_frame,
)
from cutemica.providers.capabilities import WindowRegistration


def test_global_drag_accepts_exact_registered_translation() -> None:
    field = np.arange(24 * 8 * 3, dtype=np.uint8).reshape(8, 24, 3)
    previous = _frame(10, field[:, :16])
    current = _frame(11, field[:, 1:17])

    result = analyze_drag_frames(
        (previous, current),
        WindowRegistration.GLOBAL,
        (1, 2, 3),
    )

    assert result.mismatched_pixels == 0
    assert result.maximum_channel_delta == 0


def test_screen_local_drag_requires_an_unchanged_material() -> None:
    pixels = np.full((8, 16, 3), (40, 80, 120), dtype=np.uint8)

    result = analyze_drag_frames(
        (_frame(0, pixels), _frame(0, pixels.copy())),
        WindowRegistration.SCREEN_LOCAL,
        (32, 32, 32),
    )

    assert result.mismatched_pixels == 0
    assert result.fallback_pixels == 0


def test_drag_analysis_reports_fallback_and_changed_pixels() -> None:
    previous = np.full((4, 8, 3), (40, 80, 120), dtype=np.uint8)
    current = previous.copy()
    current[1, 2] = (32, 32, 32)

    result = analyze_drag_frames(
        (_frame(0, previous), _frame(0, current)),
        WindowRegistration.SCREEN_LOCAL,
        (32, 32, 32),
    )

    assert result.mismatched_pixels == 1
    assert result.fallback_pixels == 1
    assert result.maximum_channel_delta == 88


def test_global_drag_rejects_fractional_capture_registration() -> None:
    pixels = np.zeros((8, 16, 3), dtype=np.uint8)
    previous = _frame(0, pixels)
    current = CapturedDragFrame(
        WindowGeometry(FloatRect(0.5, 0, 16, 8), 16, 8),
        pixels,
    )

    with pytest.raises(RuntimeError, match="fractional capture shift"):
        analyze_drag_frames(
            (previous, current),
            WindowRegistration.GLOBAL,
            (32, 32, 32),
        )


def test_qimage_capture_copies_rgb_pixels() -> None:
    image = QImage(3, 2, QImage.Format.Format_RGB32)
    image.fill(0xFF123456)

    frame = captured_frame(
        WindowGeometry(FloatRect(0, 0, 3, 2), 3, 2),
        image,
    )

    assert frame.pixels.shape == (2, 3, 3)
    assert frame.pixels[0, 0].tolist() == [18, 52, 86]


def _frame(
    native_x: float, pixels: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]
) -> CapturedDragFrame:
    height, width, _channels = pixels.shape
    return CapturedDragFrame(
        WindowGeometry(FloatRect(native_x, 0, width, height), width, height),
        pixels,
    )
