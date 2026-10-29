"""Step 3: the autoscaling signal from the chapter's opening story.

On the Monday before Christmas, traffic to Wren reached several times its usual level and
the autoscaler, which added an instance when CPU passed 70%, did nothing. Wren's instances
sat at about 20% CPU, because almost all of each request was spent waiting for the model
provider, while the requests in flight climbed until the connection pools ran out and
customers saw timeouts. Lucía switched the scaling signal to requests in flight and queue
depth, and set requests that met the provider's token-rate limit to wait in the queue
instead of failing.

This simulates the day second by second, three ways: A scales on CPU; B scales on requests
in flight and queue depth; C is B with rate-limited requests waiting in the queue. The
traffic is random from a fixed seed, and every figure is illustrative.

    python src/scaling_signal.py
"""

import math
import random
from collections import deque
from dataclasses import dataclass, field

POOL = 50  # provider connections per instance
LATENCY = 4  # seconds per request, almost all of it waiting for the provider
CPU_PER_REQUEST = 0.016  # CPU seconds per request: parsing, prompt building, streaming
TIMEOUT = 30  # seconds a request can wait in the queue before the customer sees a timeout
BOOT = 90  # seconds for a new instance to start taking traffic
MIN_INSTANCES, MAX_INSTANCES = 2, 20
CPU_THRESHOLD = 0.70  # policy A: add an instance above 70% CPU
TARGET_UTILIZATION = 0.70  # policies B and C: of each instance's connection pool
TOKENS_PER_REQUEST = 2_000
TOKENS_PER_MINUTE = 6_000_000  # the provider's token-rate limit for the account
RATE_LIMIT = TOKENS_PER_MINUTE // 60 // TOKENS_PER_REQUEST  # requests it accepts a second
START_HOUR = 7
# Requests per second at the start of each hour from 07:00. A usual day peaks near 10.
HOURLY_RATE = [8, 15, 28, 40, 42, 38, 40, 45, 44, 36, 25, 15]


@dataclass
class Result:
    arrived: int = 0
    answered: int = 0
    timed_out: int = 0
    rate_limited: int = 0  # requests that failed on the provider's rate limit
    peak_instances: int = MIN_INSTANCES
    max_cpu: float = 0.0
    waits: dict[int, int] = field(default_factory=dict)  # seconds waited: requests
    hourly: list[tuple[int, float, int, int, float, int, int]] = field(default_factory=list)

    def waited(self) -> int:
        """Requests answered after waiting a second or more in the queue."""
        return sum(n for wait, n in self.waits.items() if wait >= 1)

    def longest_wait(self) -> int:
        return max(self.waits, default=0)


def rate(second: int) -> float:
    """Requests per second, rising and falling smoothly between the hourly figures."""
    hour, into = divmod(second, 3600)
    after = HOURLY_RATE[min(hour + 1, len(HOURLY_RATE) - 1)]
    return HOURLY_RATE[hour] + (after - HOURLY_RATE[hour]) * into / 3600


def desired_by_cpu(cpu: float, instances: int) -> int:
    """Policy A: one more instance whenever average CPU is above the threshold."""
    return instances + 1 if cpu > CPU_THRESHOLD else instances


def desired_by_load(in_flight: int, queued: int) -> int:
    """Policies B and C: enough instances to hold everything in flight and queued."""
    return math.ceil((in_flight + queued) / (POOL * TARGET_UTILIZATION))


def take(queue: deque, n: int) -> list[tuple[int, int]]:
    """Remove the n oldest requests: (second they arrived, how many) groups."""
    taken = []
    while n:
        arrived, count = queue[0]
        k = min(n, count)
        taken.append((arrived, k))
        n -= k
        if k == count:
            queue.popleft()
        else:
            queue[0] = (arrived, count - k)
    return taken


def simulate(policy: str, wait_on_rate_limit: bool, seed: int = 16) -> Result:
    """One day, second by second. policy is "cpu" (A) or "load" (B and C)."""
    rng = random.Random(seed)
    seconds = len(HOURLY_RATE) * 3600
    result = Result()
    ready, booting = MIN_INSTANCES, deque()  # booting: the second each one is ready
    queue, queued, in_flight = deque(), 0, 0
    finishing = [0] * (seconds + LATENCY)
    cpu_window = deque(maxlen=60)  # per-instance CPU over the last minute
    last_scale_in = 0
    hour_timeouts = 0
    for t in range(seconds):
        in_flight -= finishing[t]
        while booting and booting[0] <= t:
            booting.popleft()
            ready += 1

        arrivals = rng.binomialvariate(1_000, rate(t) / 1_000)
        result.arrived += arrivals
        if arrivals:
            queue.append((t, arrivals))
            queued += arrivals
        while queue and queue[0][0] <= t - TIMEOUT:
            result.timed_out += queue[0][1]
            hour_timeouts += queue[0][1]
            queued -= queue.popleft()[1]

        free = max(0, ready * POOL - in_flight)
        if wait_on_rate_limit:
            started, refused = min(free, queued, RATE_LIMIT), 0
        else:
            sent = min(free, queued)
            started, refused = min(sent, RATE_LIMIT), max(0, sent - RATE_LIMIT)
        for arrived, k in take(queue, started):
            result.waits[t - arrived] = result.waits.get(t - arrived, 0) + k
        take(queue, refused)
        queued -= started + refused
        result.answered += started
        result.rate_limited += refused
        in_flight += started
        finishing[t + LATENCY] += started

        cpu_window.append(started * CPU_PER_REQUEST / ready)
        cpu = sum(cpu_window) / len(cpu_window)
        result.max_cpu = max(result.max_cpu, cpu)

        if t % 15 == 0:  # the autoscaler looks every fifteen seconds
            current = ready + len(booting)
            # TODO 4: for policy "load", decide with desired_by_load(in_flight, queued).
            #   As supplied every policy scales on CPU, which never reaches the threshold
            #   because the instances spend their time waiting for the provider.
            desired = desired_by_cpu(cpu, current)
            desired = max(MIN_INSTANCES, min(MAX_INSTANCES, desired))
            for _ in range(desired - current):
                booting.append(t + BOOT)
            if desired < ready and not booting and t - last_scale_in >= 300:
                ready -= 1  # scale in gently: one instance every five minutes at most
                last_scale_in = t
            result.peak_instances = max(result.peak_instances, ready + len(booting))

        if t % 3600 == 3599:  # on the hour: the state now, and the hour's timeouts
            hour = START_HOUR + t // 3600 + 1
            result.hourly.append((hour, rate(t), in_flight, queued, cpu, ready, hour_timeouts))
            hour_timeouts = 0
    return result


def main() -> None:
    a = simulate("cpu", wait_on_rate_limit=False)
    b = simulate("load", wait_on_rate_limit=False)
    c = simulate("load", wait_on_rate_limit=True)

    print("A: add an instance when CPU passes 70%, hour by hour")
    print(
        f"  {'hour':<5} {'req/s':>5} {'in flight':>9} {'queued':>7} {'CPU':>4} {'instances':>9} {'timeouts':>9}"
    )
    for hour, req_s, flying, queued, cpu, instances, timeouts in a.hourly:
        print(
            f"  {hour:02d}:00 {req_s:>5.0f} {flying:>9,} {queued:>7,} {cpu:>4.0%} {instances:>9} {timeouts:>9,}"
        )

    print("\nThree ways through the day")
    print("  A  scale on CPU above 70%")
    print("  B  scale on requests in flight and queue depth")
    print("  C  B, with rate-limited requests waiting in the queue")
    print(f"  {'':<22} {'A':>10} {'B':>10} {'C':>10}")
    rows = [
        ("requests answered", lambda r: f"{r.answered:,}"),
        ("timed out", lambda r: f"{r.timed_out:,}"),
        ("failed on rate limit", lambda r: f"{r.rate_limited:,}"),
        ("waited in the queue", lambda r: f"{r.waited():,}"),
        ("longest wait", lambda r: f"{r.longest_wait()} s"),
        ("most instances", lambda r: f"{r.peak_instances}"),
        ("highest CPU", lambda r: f"{r.max_cpu:.0%}"),
    ]
    for label, cell in rows:
        print(f"  {label:<22} {cell(a):>10} {cell(b):>10} {cell(c):>10}")


if __name__ == "__main__":
    main()
