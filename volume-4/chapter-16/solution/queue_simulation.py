"""Lab 16 — Request Queue Simulation with Autoscaling (reference solution).

A real-time simulation of a request queue served by worker threads, with an autoscaler
that adds and removes workers as the queue grows and drains. It runs for about 40
seconds. Run from the lab folder:

    python solution/queue_simulation.py
"""

import random
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from rich.console import Console

console = Console()


@dataclass
class AIRequest:
    request_id: str
    tokens_in: int
    tokens_out: int
    priority: int = 1  # 1=high, 2=medium, 3=low
    enqueued_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def queue_wait_seconds(self) -> float:
        if self.started_at > 0:
            return self.started_at - self.enqueued_at
        return time.time() - self.enqueued_at

    @property
    def processing_seconds(self) -> float:
        if self.completed_at > 0 and self.started_at > 0:
            return self.completed_at - self.started_at
        return 0.0


class AIWorker:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.is_busy = False
        self.requests_processed = 0
        self.current_request: AIRequest | None = None
        self._thread: threading.Thread | None = None

    def process(self, request: AIRequest, on_complete):
        """Process a request in a background thread."""
        # Mark the worker busy before the thread starts, so the dispatcher cannot
        # hand it a second request in the moment before the thread runs.
        self.is_busy = True
        self.current_request = request
        request.started_at = time.time()

        def _run():
            # Simulate LLM inference latency
            base_latency = (request.tokens_in + request.tokens_out) / 500.0
            latency = max(0.2, base_latency + random.gauss(0, 0.3))
            time.sleep(latency)

            request.completed_at = time.time()
            self.requests_processed += 1
            self.is_busy = False
            self.current_request = None
            on_complete(request)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()


class AutoscalingController:
    """Adjusts worker count based on queue depth."""

    def __init__(self, min_workers: int = 1, max_workers: int = 8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = 5  # queue depth to trigger scale up
        self.scale_down_threshold = 1  # queue depth to trigger scale down
        self.cooldown_seconds = 10.0
        self._last_scale_event = 0.0

    def decide(self, queue_depth: int, active_workers: int) -> int:
        """Return the desired number of workers."""
        now = time.time()
        if now - self._last_scale_event < self.cooldown_seconds:
            return active_workers  # In cooldown, no change

        if queue_depth > self.scale_up_threshold and active_workers < self.max_workers:
            new_count = min(active_workers + 2, self.max_workers)
            console.print(
                f"  [bold yellow]↑ Scale UP:[/] {active_workers} → {new_count} workers "
                f"(queue_depth={queue_depth})"
            )
            self._last_scale_event = now
            return new_count
        elif queue_depth <= self.scale_down_threshold and active_workers > self.min_workers:
            new_count = max(active_workers - 1, self.min_workers)
            console.print(
                f"  [bold blue]↓ Scale DOWN:[/] {active_workers} → {new_count} workers "
                f"(queue_depth={queue_depth})"
            )
            self._last_scale_event = now
            return new_count
        return active_workers


class AIServiceSimulation:
    def __init__(self):
        self.request_queue: deque[AIRequest] = deque()
        self.workers: list[AIWorker] = []
        self.completed: list[AIRequest] = []
        self.autoscaler = AutoscalingController(min_workers=2, max_workers=8)
        self._lock = threading.Lock()
        self._request_counter = 0
        self.peak_workers = 2

        # Start with 2 workers
        for i in range(2):
            self.workers.append(AIWorker(f"worker-{i + 1:02d}"))

    def enqueue(self, tokens_in: int = None, tokens_out: int = None, priority: int = 1):
        with self._lock:
            self._request_counter += 1
            req = AIRequest(
                request_id=f"req-{self._request_counter:04d}",
                tokens_in=tokens_in or random.randint(100, 1000),
                tokens_out=tokens_out or random.randint(50, 400),
                priority=priority,
            )
            self.request_queue.append(req)

    def _on_complete(self, request: AIRequest):
        with self._lock:
            self.completed.append(request)

    def _dispatch(self):
        """Assign queued requests to idle workers."""
        with self._lock:
            for worker in self.workers:
                if not worker.is_busy and self.request_queue:
                    request = self.request_queue.popleft()
                    worker.process(request, self._on_complete)

    def _autoscale(self):
        """Adjust worker pool based on queue depth."""
        with self._lock:
            queue_depth = len(self.request_queue)
            active_workers = len(self.workers)

        desired = self.autoscaler.decide(queue_depth, active_workers)

        with self._lock:
            while len(self.workers) < desired:
                new_id = len(self.workers) + 1
                self.workers.append(AIWorker(f"worker-{new_id:02d}"))
            while len(self.workers) > desired:
                # Only remove idle workers
                idle = [w for w in self.workers if not w.is_busy]
                if idle:
                    self.workers.remove(idle[-1])
                else:
                    break
            self.peak_workers = max(self.peak_workers, len(self.workers))

    def stats(self) -> dict:
        with self._lock:
            completed = list(self.completed)
            queue_depth = len(self.request_queue)
            active = sum(1 for w in self.workers if w.is_busy)
            total_workers = len(self.workers)

        latencies = [r.processing_seconds for r in completed if r.processing_seconds > 0]
        wait_times = [r.queue_wait_seconds for r in completed if r.started_at > 0]

        return {
            "completed": len(completed),
            "queue_depth": queue_depth,
            "active_workers": active,
            "total_workers": total_workers,
            "avg_latency": statistics.mean(latencies) if latencies else 0,
            "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)]
            if len(latencies) > 20
            else 0,
            "avg_wait_time": statistics.mean(wait_times) if wait_times else 0,
        }

    def run(self, duration_seconds: float = 30.0, arrival_rate: float = 3.0):
        """
        Run the simulation for a given duration.
        arrival_rate = requests per second.
        """
        start = time.time()
        last_arrival = start
        interval = 1.0 / arrival_rate

        console.print(
            f"\n[bold green]Starting simulation:[/] {duration_seconds}s, "
            f"{arrival_rate} req/s, initial workers: {len(self.workers)}"
        )

        # Traffic pattern: normal for 15s, spike for 5s, normal for 10s
        while time.time() - start < duration_seconds:
            elapsed = time.time() - start

            # Spike phase: 3x traffic from t=15 to t=20
            if 15 <= elapsed <= 20:
                current_interval = interval / 3
            else:
                current_interval = interval

            now = time.time()
            if now - last_arrival >= current_interval:
                self.enqueue()
                last_arrival = now

            self._dispatch()
            self._autoscale()
            time.sleep(0.05)

        # Wait for remaining requests
        time.sleep(3)

        # Print final stats
        stats = self.stats()
        console.print("\n[bold]Simulation Complete[/]")
        console.print(f"Requests completed:  {stats['completed']}")
        console.print(f"Queue remaining:     {stats['queue_depth']}")
        console.print(f"Peak workers:        {self.peak_workers}")
        console.print(f"Workers at end:      {stats['total_workers']}")
        console.print(f"Avg processing:      {stats['avg_latency']:.2f}s")
        console.print(f"p95 latency:         {stats['p95_latency']:.2f}s")
        console.print(f"Avg queue wait:      {stats['avg_wait_time']:.2f}s")


if __name__ == "__main__":
    sim = AIServiceSimulation()
    sim.run(duration_seconds=35.0, arrival_rate=2.0)
