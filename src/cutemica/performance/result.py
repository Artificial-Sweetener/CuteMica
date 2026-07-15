"""Timing result model for CuteMica motion benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import median


@dataclass(frozen=True, slots=True)
class MotionBenchmarkResult:
    frame_count: int
    median_ms: float
    p95_ms: float
    maximum_ms: float


def summarize_motion_samples(samples: list[float]) -> MotionBenchmarkResult:
    """Summarize a non-empty sequence with a nearest-rank p95."""

    if not samples:
        raise ValueError("At least one motion timing sample is required")
    ordered = sorted(samples)
    return MotionBenchmarkResult(
        frame_count=len(ordered),
        median_ms=median(ordered),
        p95_ms=ordered[ceil(len(ordered) * 0.95) - 1],
        maximum_ms=ordered[-1],
    )
