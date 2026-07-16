"""Select clocks for portable performance measurements."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from time import perf_counter, process_time

type TimingFunction = Callable[[], float]


class BenchmarkClock(StrEnum):
    """Clock domains supported by native performance probes."""

    WALL = "wall"
    PROCESS = "process"


def timing_function(clock: BenchmarkClock) -> TimingFunction:
    """Return the monotonic timer for a benchmark clock domain."""

    if clock is BenchmarkClock.PROCESS:
        return process_time
    return perf_counter
