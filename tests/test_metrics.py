from cutemica.metrics import PaintMetrics


def test_paint_metrics_retain_a_bounded_sample_window() -> None:
    metrics = PaintMetrics(sample_count=3)

    for value in range(10):
        metrics.record(float(value))

    assert metrics.sample_count == 3
    assert metrics.average_ms == 8.0
    assert metrics.maximum_ms == 9.0
    assert metrics.latest_ms == 9.0
