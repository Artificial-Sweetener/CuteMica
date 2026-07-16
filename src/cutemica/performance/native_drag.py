"""Measure native CuteMica drag latency and rendered-frame continuity."""

from __future__ import annotations

import argparse
import json
import sys

from PySide6.QtCore import QPoint
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from cutemica.performance.drag_fixture import (
    create_drag_materials,
    performance_positions,
    split_drag_bindings,
    stability_positions,
)
from cutemica.performance.drag_frames import (
    CapturedDragFrame,
    analyze_drag_frames,
    captured_frame,
)
from cutemica.performance.drag_result import (
    NativeDragBudgets,
    NativeDragResult,
)
from cutemica.performance.drag_window import NativeDragProbeWindow
from cutemica.performance.result import summarize_motion_samples
from cutemica.providers.qt_screens import infer_qt_screen_bindings
from cutemica.providers.window_geometry import create_window_geometry_provider

_MARKER = "CUTEMICA_NATIVE_DRAG_OK"
_WINDOW_SIZE = (240, 140)


def benchmark_native_drag(
    frame_count: int = 600,
    stability_frame_count: int = 96,
) -> NativeDragResult:
    """Run native move events, immediate paints, and pixel continuity checks."""

    if frame_count < 50:
        raise ValueError("Native drag benchmark requires at least 50 frames")
    if stability_frame_count < 8:
        raise ValueError("Native drag stability requires at least 8 frames")
    application = _native_application()
    actual_bindings = infer_qt_screen_bindings(application.screens())
    if not actual_bindings:
        raise RuntimeError("Native drag benchmark requires a Qt screen")
    primary = actual_bindings[0]
    bindings = split_drag_bindings(primary)
    provider = create_window_geometry_provider(bindings)
    window = NativeDragProbeWindow(
        application,
        bindings,
        provider,
        create_drag_materials(bindings),
        _WINDOW_SIZE,
    )
    stability_path = stability_positions(primary, *_WINDOW_SIZE, stability_frame_count)
    window.start(stability_path[0])
    try:
        window.begin_recording()
        _warm_up(window)
        window.clear_timings()
        captured = _capture_stability(window, stability_path)
        window.clear_timings()
        for position in performance_positions(primary, *_WINDOW_SIZE, frame_count):
            window.step(position)
        samples = window.samples
        stability = analyze_drag_frames(
            captured,
            provider.registration,
            window.fallback_color,
        )
        return NativeDragResult(
            platform_name=QGuiApplication.platformName(),
            registration=provider.registration.value,
            move_events=window.move_events,
            forced_presentations=window.forced_presentations,
            generation_count=window.generation_count,
            move_cycle=summarize_motion_samples(list(window.move_cycles_ms)),
            geometry=summarize_motion_samples(
                [sample.geometry_ms for sample in samples]
            ),
            presentation=summarize_motion_samples(
                [sample.presentation_ms for sample in samples]
            ),
            paint=summarize_motion_samples([sample.paint_ms for sample in samples]),
            stability=stability,
        )
    finally:
        window.finish()


def _native_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv[:1])
    if not isinstance(application, QApplication):
        raise RuntimeError("Native drag benchmark requires QApplication")
    platform = QGuiApplication.platformName().casefold()
    if platform in {"offscreen", "minimal", "vnc"}:
        raise RuntimeError(f"Native drag benchmark rejects Qt platform {platform!r}")
    return application


def _warm_up(window: NativeDragProbeWindow) -> None:
    origin = window.pos()
    for frame in range(24):
        window.step(QPoint(origin.x() + frame % 8, origin.y()))


def _capture_stability(
    window: NativeDragProbeWindow,
    positions: tuple[QPoint, ...],
) -> tuple[CapturedDragFrame, ...]:
    frames: list[CapturedDragFrame] = []
    for position in positions:
        sample = window.step(position)
        frames.append(captured_frame(sample.geometry, window.capture()))
    return tuple(frames)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--stability-frames", type=int, default=96)
    parser.add_argument("--move-p95-budget-ms", type=float, default=10.0)
    parser.add_argument("--geometry-p95-budget-ms", type=float, default=2.0)
    parser.add_argument("--presentation-p95-budget-ms", type=float, default=5.0)
    parser.add_argument("--paint-p95-budget-ms", type=float, default=5.0)
    parser.add_argument("--mismatch-ratio", type=float, default=0.0)
    parser.add_argument("--maximum-channel-delta", type=int, default=2)
    arguments = parser.parse_args()
    result = benchmark_native_drag(arguments.frames, arguments.stability_frames)
    budgets = NativeDragBudgets(
        move_cycle_p95_ms=arguments.move_p95_budget_ms,
        geometry_p95_ms=arguments.geometry_p95_budget_ms,
        presentation_p95_ms=arguments.presentation_p95_budget_ms,
        paint_p95_ms=arguments.paint_p95_budget_ms,
        mismatch_ratio=arguments.mismatch_ratio,
        maximum_channel_delta=arguments.maximum_channel_delta,
    )
    violations = budgets.violations(result)
    print(json.dumps(result.payload(), sort_keys=True))
    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1
    print(_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
