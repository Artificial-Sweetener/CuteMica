from time import perf_counter, process_time

from cutemica.performance.timing_clock import BenchmarkClock, timing_function


def test_timing_clock_selects_wall_and_process_domains() -> None:
    assert timing_function(BenchmarkClock.WALL) is perf_counter
    assert timing_function(BenchmarkClock.PROCESS) is process_time
