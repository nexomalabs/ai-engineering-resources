# Batching simulation — Volume IV, Chapter 6 lab, Step 7 (reference solution)
#
# The customs pipeline from the chapter's opening story: an open model on two GPUs, an
# afternoon rush of documents whose answers vary a great deal in length. Each GPU decodes
# one token for every request in its batch per step. The two schedulers differ only in
# when a request may join a batch:
#   fixed batches        a batch starts when the GPU is idle and runs until its longest
#                        request finishes; finished slots sit empty until then
#   continuous batching  a slot freed by a finished request is refilled at the next step
#
#   python solution/batching_sim.py

import random
from dataclasses import dataclass, field

STEP_SECONDS = 0.02  # one decoding step for the whole batch
SLOTS_PER_GPU = 8  # requests a GPU decodes together
# Output lengths, in tokens, of the customs answers: most short, a few very long.
LENGTHS = [60, 80, 100, 120, 150, 200, 260, 400, 700, 1100]


@dataclass
class Request:
    arrival: float
    tokens: int
    remaining: int = 0
    finished: float | None = None

    def __post_init__(self):
        self.remaining = self.tokens


@dataclass
class GPU:
    queue: list = field(default_factory=list)
    batch: list = field(default_factory=list)


def make_arrivals(rate_per_second: float, minutes: float, seed: int = 7) -> list[Request]:
    rng = random.Random(seed)
    t, arrivals = 0.0, []
    while t < minutes * 60:
        t += rng.expovariate(rate_per_second)
        arrivals.append(Request(arrival=t, tokens=rng.choice(LENGTHS)))
    return arrivals


def admit(gpu: GPU, continuous: bool) -> None:
    """Move queued requests into the batch, as the scheduler allows."""
    if continuous or not gpu.batch:
        while gpu.queue and len(gpu.batch) < SLOTS_PER_GPU:
            gpu.batch.append(gpu.queue.pop(0))


def simulate(
    arrivals: list[Request], gpus: int = 2, continuous: bool = True, until: float | None = None
) -> dict:
    """
    Run the schedule until `until` seconds (default: the end of the rush) and report what
    the customers saw, and how much of the GPUs' capacity was used.
    """
    requests = [Request(r.arrival, r.tokens) for r in arrivals]
    pending = list(requests)
    servers = [GPU() for _ in range(gpus)]
    longest_queue, now, steps, busy_slots = 0, 0.0, 0, 0
    end = until if until is not None else (arrivals[-1].arrival if arrivals else 0.0)
    while now <= end:
        while pending and pending[0].arrival <= now:
            min(servers, key=lambda g: len(g.queue) + len(g.batch)).queue.append(pending.pop(0))
        for gpu in servers:
            admit(gpu, continuous)
            busy_slots += len(gpu.batch)
            for request in gpu.batch:
                request.remaining -= 1
                if request.remaining == 0:
                    request.finished = now + STEP_SECONDS
            gpu.batch = [r for r in gpu.batch if r.remaining > 0]
        longest_queue = max(longest_queue, sum(len(g.queue) for g in servers))
        now += STEP_SECONDS
        steps += 1

    done = sorted(r.finished - r.arrival for r in requests if r.finished is not None)
    return {
        "arrived": len(requests),
        "completed": len(done),
        "p50_s": done[len(done) // 2] if done else 0.0,
        "p95_s": done[int(len(done) * 0.95)] if done else 0.0,
        "longest_queue": longest_queue,
        "waiting_at_end": sum(len(g.queue) for g in servers),
        "slot_utilization": busy_slots / (steps * gpus * SLOTS_PER_GPU) if steps else 0.0,
    }


def main() -> None:
    rate, minutes = 2.0, 30
    arrivals = make_arrivals(rate, minutes)
    print(
        f"Afternoon rush: {minutes} minutes at {rate} documents a second "
        f"({len(arrivals)} documents), 2 GPUs with {SLOTS_PER_GPU} slots each\n"
    )
    print(
        f"{'scheduler':<20} {'completed':>9} {'p50':>8} {'p95':>8} {'longest queue':>14} "
        f"{'slots busy':>11}"
    )
    for name, continuous in (("fixed batches", False), ("continuous batching", True)):
        r = simulate(arrivals, gpus=2, continuous=continuous)
        print(
            f"{name:<20} {r['completed']:>9} {r['p50_s']:>7.1f}s {r['p95_s']:>7.1f}s "
            f"{r['longest_queue']:>14} {r['slot_utilization']:>11.0%}"
        )


if __name__ == "__main__":
    main()
