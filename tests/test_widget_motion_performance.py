import os

import pytest

from cutemica.performance.widget_motion import benchmark_widget_motion_frames


@pytest.mark.skipif(
    os.environ.get("QT_QPA_PLATFORM") != "offscreen",
    reason="Widget performance tests are restricted to Qt's offscreen platform",
)
def test_offscreen_widget_motion_stays_inside_frame_budget() -> None:
    result = benchmark_widget_motion_frames(240)

    assert result.p95_ms <= 10.0
    assert result.maximum_ms <= 20.0
