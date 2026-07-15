"""Measure the cached motion paint path without creating a window."""

from __future__ import annotations

import argparse
from time import perf_counter

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap

from cutemica.geometry import FloatRect, WindowGeometry
from cutemica.performance.fixture import (
    create_motion_binding,
    create_motion_material,
)
from cutemica.performance.result import (
    MotionBenchmarkResult,
    summarize_motion_samples,
)
from cutemica.viewport import plan_material_slices
from cutemica.widgets.material_painter import paint_material_slices


def benchmark_motion_frames(frame_count: int = 600) -> MotionBenchmarkResult:
    """Render desktop-registered frames into a QImage and report timings."""

    if frame_count < 50:
        raise ValueError("Motion benchmark requires at least 50 frames")
    application = QGuiApplication.instance() or QGuiApplication([])
    material = QPixmap.fromImage(create_motion_material())
    target = QImage(980, 680, QImage.Format.Format_RGB32)
    binding = create_motion_binding()
    materials = {binding.cache_key: material}
    sizes = {binding.cache_key: (material.width(), material.height())}
    dirty_rect = QRect(0, 0, target.width(), target.height())
    samples: list[float] = []
    for frame in range(frame_count + 40):
        started = perf_counter()
        slices = plan_material_slices(
            WindowGeometry(
                FloatRect(
                    100 + frame % 256,
                    120,
                    target.width(),
                    target.height(),
                ),
                target.width(),
                target.height(),
            ),
            (binding,),
            sizes,
        )
        painter = QPainter(target)
        paint_material_slices(
            painter,
            dirty_rect,
            (32, 32, 32),
            slices,
            materials,
        )
        painter.end()
        elapsed_ms = (perf_counter() - started) * 1_000
        if frame >= 40:
            samples.append(elapsed_ms)
    del application
    return summarize_motion_samples(samples)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--p95-budget-ms", type=float, default=1.5)
    arguments = parser.parse_args()
    result = benchmark_motion_frames(arguments.frames)
    print(
        f"frames={result.frame_count} median={result.median_ms:.3f}ms "
        f"p95={result.p95_ms:.3f}ms max={result.maximum_ms:.3f}ms"
    )
    return 0 if result.p95_ms <= arguments.p95_budget_ms else 1


if __name__ == "__main__":
    raise SystemExit(main())
