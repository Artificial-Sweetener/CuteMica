from cutemica.performance.drag_result import (
    DragStabilityResult,
    NativeDragBudgets,
    NativeDragResult,
)
from cutemica.performance.result import MotionBenchmarkResult


def test_native_drag_budgets_accept_a_stable_fast_result() -> None:
    result = _result()
    budgets = NativeDragBudgets(1.0, 1.0, 1.0, 1.0)

    assert budgets.violations(result) == ()
    assert result.payload()["platform_name"] == "test"


def test_native_drag_budgets_report_each_invariant() -> None:
    result = NativeDragResult(
        platform_name="test",
        registration="global",
        timing_clock="wall",
        move_events=1,
        forced_presentations=0,
        generation_count=1,
        material_cache_stable=False,
        move_cycle=_timing(2.0),
        geometry=_timing(2.0),
        presentation=_timing(2.0),
        paint=_timing(2.0),
        stability=DragStabilityResult(2, 100, 2, 1, 8),
    )

    violations = NativeDragBudgets(1.0, 1.0, 1.0, 1.0).violations(result)

    assert len(violations) == 9
    assert any("material generations" in item for item in violations)
    assert any("fallback pixels" in item for item in violations)
    assert any("cached material" in item for item in violations)


def _result() -> NativeDragResult:
    timing = _timing(0.5)
    return NativeDragResult(
        platform_name="test",
        registration="global",
        timing_clock="wall",
        move_events=100,
        forced_presentations=0,
        generation_count=0,
        material_cache_stable=True,
        move_cycle=timing,
        geometry=timing,
        presentation=timing,
        paint=timing,
        stability=DragStabilityResult(10, 1_000, 0, 0, 0),
    )


def _timing(p95_ms: float) -> MotionBenchmarkResult:
    return MotionBenchmarkResult(100, p95_ms, p95_ms, p95_ms)
