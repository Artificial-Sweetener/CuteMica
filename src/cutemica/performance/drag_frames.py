"""Pixel-level continuity analysis for captured native drag frames."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PySide6.QtGui import QImage

from cutemica.geometry import WindowGeometry
from cutemica.performance.drag_result import DragStabilityResult
from cutemica.providers.capabilities import WindowRegistration

RgbFrame = NDArray[np.uint8]


@dataclass(frozen=True, slots=True)
class CapturedDragFrame:
    geometry: WindowGeometry
    pixels: RgbFrame


def captured_frame(geometry: WindowGeometry, image: QImage) -> CapturedDragFrame:
    """Copy a Qt image into an RGB array independent of its row stride."""

    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    rows = np.frombuffer(converted.constBits(), dtype=np.uint8).reshape(
        converted.height(), converted.bytesPerLine()
    )
    pixels = rows[:, : converted.width() * 4].reshape(
        converted.height(), converted.width(), 4
    )
    return CapturedDragFrame(geometry, pixels[:, :, :3].copy())


def analyze_drag_frames(
    frames: tuple[CapturedDragFrame, ...],
    registration: WindowRegistration,
    fallback_color: tuple[int, int, int],
    *,
    channel_tolerance: int = 2,
) -> DragStabilityResult:
    """Measure fallback exposure and translation continuity across a trajectory."""

    if len(frames) < 2:
        raise ValueError("Drag stability requires at least two captured frames")
    fallback = np.array(fallback_color, dtype=np.uint8)
    fallback_pixels = sum(
        int(np.count_nonzero(np.all(frame.pixels == fallback, axis=2)))
        for frame in frames
    )
    compared_pixels = 0
    mismatched_pixels = 0
    maximum_delta = 0
    for previous, current in zip(frames, frames[1:], strict=False):
        previous_overlap, current_overlap = _overlap(previous, current, registration)
        differences = np.abs(
            previous_overlap.astype(np.int16) - current_overlap.astype(np.int16)
        )
        pixel_deltas = differences.max(axis=2)
        compared_pixels += pixel_deltas.size
        mismatched_pixels += int(np.count_nonzero(pixel_deltas > channel_tolerance))
        maximum_delta = max(maximum_delta, int(pixel_deltas.max(initial=0)))
    return DragStabilityResult(
        frame_count=len(frames),
        compared_pixels=compared_pixels,
        mismatched_pixels=mismatched_pixels,
        fallback_pixels=fallback_pixels,
        maximum_channel_delta=maximum_delta,
    )


def _overlap(
    previous: CapturedDragFrame,
    current: CapturedDragFrame,
    registration: WindowRegistration,
) -> tuple[RgbFrame, RgbFrame]:
    if previous.pixels.shape != current.pixels.shape:
        raise RuntimeError("Native drag changed the captured frame dimensions")
    if registration is WindowRegistration.SCREEN_LOCAL:
        return previous.pixels, current.pixels
    previous_native = previous.geometry.native_rect_px
    current_native = current.geometry.native_rect_px
    height, width, _channels = current.pixels.shape
    shift_x = _pixel_shift(
        current_native.x - previous_native.x,
        current_native.width,
        width,
    )
    shift_y = _pixel_shift(
        current_native.y - previous_native.y,
        current_native.height,
        height,
    )
    if abs(shift_x) >= width or abs(shift_y) >= height:
        raise RuntimeError("Native drag frames do not overlap")
    previous_y, current_y = _axis_overlap(height, shift_y)
    previous_x, current_x = _axis_overlap(width, shift_x)
    return (
        previous.pixels[previous_y, previous_x],
        current.pixels[current_y, current_x],
    )


def _pixel_shift(native_delta: float, native_extent: float, pixels: int) -> int:
    exact = native_delta * pixels / native_extent
    rounded = round(exact)
    if abs(exact - rounded) > 0.05:
        raise RuntimeError(f"Native drag produced a fractional capture shift: {exact}")
    return rounded


def _axis_overlap(length: int, shift: int) -> tuple[slice, slice]:
    if shift >= 0:
        return slice(shift, length), slice(0, length - shift)
    return slice(0, length + shift), slice(-shift, length)
