from cutemica.metrics import PaintMetrics


def test_paint_metrics_discards_old_samples_at_its_fixed_bound() -> None:
    metrics = PaintMetrics(sample_count=3)

    metrics.record(100.0)
    metrics.record(1.0)
    metrics.record(2.0)
    metrics.record(3.0)

    assert metrics.sample_count == 3
    assert metrics.average_ms == 2.0
    assert metrics.maximum_ms == 3.0
