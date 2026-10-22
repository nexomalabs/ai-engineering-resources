# Applied AI Engineering, Volume IV, Chapter 7
# Section 7.3, Profiling AI Applications
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Example: cProfile usage on an AI pipeline function
import cProfile
import pstats
import io

def profile_function(func, *args, **kwargs):
    """Run func under cProfile and print the top 20 time-consuming calls."""
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()

    stream = io.StringIO()
    stats = pstats.Stats(pr, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    print(stream.getvalue())
    return result
