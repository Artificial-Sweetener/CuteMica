"""Result models and budgets for native drag validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cutemica.performance.result import MotionBenchmarkResult


@dataclass(frozen=True, slots=True)
class DragStabilityResult:
    frame_count: int
    compared_pixels: int
    mismatched_pixels: int
    fallback_pixels: int
    maximum_channel_delta: int

    @property
    def mismatch_ratio(self) -> float:
        return (
            self.mismatched_pixels / self.compared_pixels
            if self.compared_pixels
            else 0.0
        )


@dataclass(frozen=True, slots=True)
class NativeDragResult:
    platform_name: str
    registration: str
    move_events: int
    forced_presentations: int
    generation_count: int
    material_cache_stable: bool
    move_cycle: MotionBenchmarkResult
    geometry: MotionBenchmarkResult
    presentation: MotionBenchmarkResult
    paint: MotionBenchmarkResult
    stability: DragStabilityResult

    def payload(self) -> dict[str, object]:
        """Return a JSON-serializable evidence payload."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class NativeDragBudgets:
    move_cycle_p95_ms: float
    geometry_p95_ms: float
    presentation_p95_ms: float
    paint_p95_ms: float
    mismatch_ratio: float = 0.0
    maximum_channel_delta: int = 2

    def violations(self, result: NativeDragResult) -> tuple[str, ...]:
        """Describe every failed performance or stability invariant."""

        failures: list[str] = []
        _check_timing(failures, "move cycle", result.move_cycle, self.move_cycle_p95_ms)
        _check_timing(failures, "geometry", result.geometry, self.geometry_p95_ms)
        _check_timing(
            failures,
            "presentation",
            result.presentation,
            self.presentation_p95_ms,
        )
        _check_timing(failures, "paint", result.paint, self.paint_p95_ms)
        if result.generation_count:
            failures.append(
                f"movement triggered {result.generation_count} material generations"
            )
        if not result.material_cache_stable:
            failures.append("movement replaced a cached material texture")
        if result.stability.fallback_pixels:
            failures.append(
                f"rendered {result.stability.fallback_pixels} fallback pixels"
            )
        if result.stability.mismatch_ratio > self.mismatch_ratio:
            failures.append(
                "frame mismatch ratio "
                f"{result.stability.mismatch_ratio:.6f} exceeds "
                f"{self.mismatch_ratio:.6f}"
            )
        if result.stability.maximum_channel_delta > self.maximum_channel_delta:
            failures.append(
                "maximum channel delta "
                f"{result.stability.maximum_channel_delta} exceeds "
                f"{self.maximum_channel_delta}"
            )
        return tuple(failures)


def _check_timing(
    failures: list[str],
    name: str,
    result: MotionBenchmarkResult,
    budget_ms: float,
) -> None:
    if result.p95_ms > budget_ms:
        failures.append(f"{name} p95 {result.p95_ms:.3f} ms exceeds {budget_ms:.3f} ms")
