# Applied AI Engineering, Volume IV, Chapter 7
# Section 7.3, Profiling AI Applications
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Example: line_profiler usage (requires: pip install line-profiler)
# Decorate the function you want to profile with @profile, then run:
#   kernprof -l -v script.py

from line_profiler import LineProfiler  # type: ignore

def profile_lines(func):
    """Decorator that prints per-line timing after function completes."""
    lp = LineProfiler()
    lp_wrapper = lp(func)
    def inner(*args, **kwargs):
        result = lp_wrapper(*args, **kwargs)
        lp.print_stats()
        return result
    return inner
