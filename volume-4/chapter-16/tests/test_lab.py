"""Tests for Lab 16. Run against solution/ in CI."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from load_balancer import AILoadBalancer  # noqa: E402
from queue_simulation import (  # noqa: E402
    AIRequest,
    AIServiceSimulation,
    AIWorker,
    AutoscalingController,
)


def test_scale_up_when_the_queue_is_deep():
    ctrl = AutoscalingController(min_workers=2, max_workers=8)
    assert ctrl.decide(queue_depth=6, active_workers=2) == 4


def test_scale_up_is_capped_at_max_workers():
    ctrl = AutoscalingController(min_workers=2, max_workers=5)
    assert ctrl.decide(queue_depth=50, active_workers=4) == 5


def test_scale_down_when_the_queue_drains_but_not_below_min():
    assert AutoscalingController(min_workers=2).decide(queue_depth=0, active_workers=5) == 4
    assert AutoscalingController(min_workers=2).decide(queue_depth=0, active_workers=2) == 2


def test_cooldown_blocks_a_second_change():
    ctrl = AutoscalingController(min_workers=2, max_workers=8)
    assert ctrl.decide(queue_depth=6, active_workers=2) == 4
    assert ctrl.decide(queue_depth=20, active_workers=4) == 4
    ctrl._last_scale_event = time.time() - ctrl.cooldown_seconds - 1
    assert ctrl.decide(queue_depth=20, active_workers=4) == 6


def test_scale_down_keeps_busy_workers():
    sim = AIServiceSimulation()
    for w in sim.workers:
        w.is_busy = True
    sim.workers.append(AIWorker("worker-03"))
    sim.workers[0].is_busy = False

    class Shrink:
        def decide(self, queue_depth, active_workers):
            return 1

    sim.autoscaler = Shrink()
    sim._autoscale()
    assert [w.is_busy for w in sim.workers] == [True]


def test_worker_is_busy_as_soon_as_it_is_dispatched():
    done = []
    worker = AIWorker("w")
    worker.process(AIRequest("r", tokens_in=1, tokens_out=1), done.append)
    assert worker.is_busy
    worker._thread.join()
    assert done and not worker.is_busy
    assert done[0].processing_seconds >= 0.2


def test_round_robin_cycles_through_every_worker():
    lb = AILoadBalancer(["a", "b", "c"])
    assert [lb.round_robin() for _ in range(6)] == ["a", "b", "c", "a", "b", "c"]


def test_least_connections_picks_the_least_busy():
    lb = AILoadBalancer(["a", "b"])
    lb.active_requests["a"] = 3
    assert lb.least_connections() == "b"


def test_weighted_routing_counts_complexity():
    lb = AILoadBalancer(["a", "b"])
    assert lb.weighted_least_connections(0.9) == "a"
    assert lb.weighted_least_connections(0.1) == "b"
    assert lb.weighted_least_connections(0.1) == "b"  # b carries 0.1, a carries 0.9
    assert lb.active_load["b"] == 0.2
