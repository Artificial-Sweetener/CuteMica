from collections import deque
from statistics import fmean


class PaintMetrics:
    def __init__(self, sample_count: int = 180) -> None:
        self._samples: deque[float] = deque(maxlen=sample_count)

    def record(self, elapsed_ms: float) -> None:
        self._samples.append(elapsed_ms)

    @property
    def sample_count(self) -> int:
        return len(self._samples)

    @property
    def average_ms(self) -> float:
        return fmean(self._samples) if self._samples else 0.0

    @property
    def maximum_ms(self) -> float:
        return max(self._samples, default=0.0)

    @property
    def latest_ms(self) -> float:
        """Return the most recently recorded paint duration."""

        return self._samples[-1] if self._samples else 0.0
