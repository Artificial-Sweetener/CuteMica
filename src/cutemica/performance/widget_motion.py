"""Measure synchronous backdrop presentation on Qt's offscreen platform."""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter

from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import FloatRect, WindowGeometry
from cutemica.performance.fixture import (
    create_motion_binding,
    create_motion_material,
)
from cutemica.performance.result import (
    MotionBenchmarkResult,
    summarize_motion_samples,
)
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource
from cutemica.widgets.backdrop import PortableMicaBackdrop


def benchmark_widget_motion_frames(
    frame_count: int = 600,
) -> MotionBenchmarkResult:
    """Measure the real QWidget hot path without creating a desktop window."""

    if frame_count < 50:
        raise ValueError("Motion benchmark requires at least 50 frames")
    application = _offscreen_application()
    binding = create_motion_binding()
    controller = MaterialController(
        WallpaperSnapshot.single(
            "benchmark", WallpaperSource(Path(__file__), WallpaperPlacement.FILL)
        ),
        (binding,),
        ThemeController(ThemeMode.LIGHT),
    )
    window = QWidget()
    window.resize(980, 680)
    backdrop = PortableMicaBackdrop(controller, window)
    backdrop.setGeometry(window.rect())
    backdrop.set_material(
        binding.cache_key,
        QPixmap.fromImage(create_motion_material()),
    )
    window.show()
    try:
        window.activateWindow()
        application.processEvents()
        if not window.isActiveWindow():
            raise RuntimeError(
                "Offscreen platform did not activate the benchmark window"
            )
        samples = _measure_presentations(backdrop, frame_count)
        if backdrop.paint_metrics.sample_count == 0:
            raise RuntimeError("Offscreen platform did not deliver backdrop paints")
    finally:
        window.close()
        application.processEvents()
    return summarize_motion_samples(samples)


def _offscreen_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    if not isinstance(application, QApplication):
        raise RuntimeError("The motion benchmark requires QApplication")
    if QGuiApplication.platformName() != "offscreen":
        raise RuntimeError("Set QT_QPA_PLATFORM=offscreen before benchmarking")
    return application


def _measure_presentations(
    backdrop: PortableMicaBackdrop,
    frame_count: int,
) -> list[float]:
    samples: list[float] = []
    for frame in range(frame_count + 40):
        started = perf_counter()
        backdrop.present(
            WindowGeometry(
                FloatRect(100 + frame % 256, 120, 980, 680),
                980,
                680,
            ),
            immediate=True,
        )
        elapsed_ms = (perf_counter() - started) * 1_000
        if frame >= 40:
            samples.append(elapsed_ms)
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--p95-budget-ms", type=float, default=1.5)
    arguments = parser.parse_args()
    result = benchmark_widget_motion_frames(arguments.frames)
    print(
        f"frames={result.frame_count} median={result.median_ms:.3f}ms "
        f"p95={result.p95_ms:.3f}ms max={result.maximum_ms:.3f}ms"
    )
    return 0 if result.p95_ms <= arguments.p95_budget_ms else 1


if __name__ == "__main__":
    raise SystemExit(main())
