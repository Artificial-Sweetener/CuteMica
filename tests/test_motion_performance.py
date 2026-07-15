from cutemica.performance.motion import benchmark_motion_frames


def test_offscreen_motion_path_stays_inside_frame_budget() -> None:
    result = benchmark_motion_frames(240)

    assert result.p95_ms <= 1.5
    assert result.maximum_ms <= 6.94
