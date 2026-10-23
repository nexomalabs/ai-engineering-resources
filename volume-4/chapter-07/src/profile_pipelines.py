"""Steps 2 and 4: profile the slow and the fast pipeline with cProfile and compare.

uv run python solution/profile_pipelines.py
"""

import cProfile
import io
import pstats
import time

import pipeline_fast
import pipeline_slow
from documents import DOCUMENTS

WATCH = {
    "_ask": "model calls",
    "round_trip_through_disk": "file write and read",
    "build_report": "report building",
}


def profile(label: str, fn) -> tuple[float, dict[str, float], str]:
    profiler = cProfile.Profile()
    t0 = time.perf_counter()
    profiler.enable()
    report = fn(DOCUMENTS)
    profiler.disable()
    wall = time.perf_counter() - t0

    stats = pstats.Stats(profiler)
    # Cumulative time for the functions we care about, whichever module defines them.
    found = {}
    for (filename, _, name), (_, _, _, cumulative, _) in stats.stats.items():
        if name in WATCH and "pipeline" in filename:
            found[name] = found.get(name, 0.0) + cumulative

    text = io.StringIO()
    pstats.Stats(profiler, stream=text).sort_stats("cumulative").print_stats(8)
    print(f"\n=== {label}: {wall:.2f} s wall time ===")
    for name, what in WATCH.items():
        seconds = found.get(name, 0.0)
        print(f"  {what:<20} {seconds:8.3f} s cumulative ({100 * seconds / wall:5.1f}% of wall)")
    return wall, found, report


if __name__ == "__main__":
    slow_wall, slow_found, slow_report = profile(
        "Before: sequential, via disk", pipeline_slow.process_all_documents
    )
    fast_wall, fast_found, fast_report = profile(
        "After: concurrent, in memory", pipeline_fast.process_all_documents
    )

    print("\n=== Improvement ===")
    print(
        f"Wall time: {slow_wall:.2f} s -> {fast_wall:.2f} s ({100 * (1 - fast_wall / slow_wall):.0f}% less)"
    )
    print(f"Same report: {slow_report == fast_report}")
    print(
        "\ncProfile counts the time a coroutine spends running, not the time it spends waiting "
        "in await,\nso the async pipeline's model calls look almost free. The waiting is still "
        "there, overlapped.\nCompare wall times, not the profile's totals, across sync and async code."
    )
