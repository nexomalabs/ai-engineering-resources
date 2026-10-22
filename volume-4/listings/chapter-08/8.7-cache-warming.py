# Applied AI Engineering, Volume IV, Chapter 8
# Section 8.7, Cache Warming
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import math
import random
import time

def should_early_refresh(expiry: float, delta: float, beta: float = 1.0) -> bool:
    """
    Probabilistic early expiration (XFetch; Vattani et al., 2015).
    expiry: when the entry expires, on the time.monotonic() clock.
    delta:  how long the last recomputation of the entry took, in seconds.
    beta:   eagerness; above 1.0 refreshes earlier, below 1.0 later.
    Returns True when this request should recompute the entry now.
    """
    now = time.monotonic()
    # -log(U) is exponentially distributed: the chance of an early refresh rises
    # sharply as expiry approaches, so only a few requests recompute at once.
    return now - delta * beta * math.log(1.0 - random.random()) >= expiry
