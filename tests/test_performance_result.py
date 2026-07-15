from cutemica.performance.result import summarize_motion_samples


def test_p95_uses_the_nearest_rank() -> None:
    result = summarize_motion_samples([float(value) for value in range(1, 21)])

    assert result.frame_count == 20
    assert result.median_ms == 10.5
    assert result.p95_ms == 19.0
    assert result.maximum_ms == 20.0
