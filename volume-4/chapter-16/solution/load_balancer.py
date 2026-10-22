"""Lab 16 — load balancing strategies compared (reference solution).

python solution/load_balancer.py
"""

import random
from collections import defaultdict


class AILoadBalancer:
    """Demonstrates different load balancing strategies."""

    def __init__(self, workers: list[str]):
        self.workers = workers
        self._rr_index = 0
        self.active_requests: dict[str, int] = defaultdict(int)
        # Sum of the complexity of each worker's in-flight requests
        self.active_load: dict[str, float] = defaultdict(float)

    def round_robin(self) -> str:
        worker = self.workers[self._rr_index % len(self.workers)]
        self._rr_index += 1
        return worker

    def least_connections(self) -> str:
        return min(self.workers, key=lambda w: self.active_requests[w])

    def weighted_least_connections(self, request_complexity: float) -> str:
        """Weight by complexity: send the request to the worker with the least
        in-flight work, counting complex requests as more work."""
        worker = min(self.workers, key=lambda w: self.active_load[w])
        self.active_load[worker] += request_complexity
        return worker

    def simulate_routing(self, strategy: str = "least_connections", n_requests: int = 20):
        distribution = defaultdict(int)
        for i in range(n_requests):
            complexity = random.uniform(0.1, 1.0)
            if strategy == "round_robin":
                worker = self.round_robin()
            elif strategy == "least_connections":
                worker = self.least_connections()
                self.active_requests[worker] += 1
                # Simulate completion after random time
                if random.random() > 0.6:
                    self.active_requests[worker] = max(0, self.active_requests[worker] - 1)
            else:
                worker = self.weighted_least_connections(complexity)
                self.active_requests[worker] += 1
            distribution[worker] += 1

        print(f"\nLoad Distribution ({strategy}):")
        for worker in sorted(distribution):
            count = distribution[worker]
            bar = "█" * count
            print(f"  {worker}: {bar} ({count})")
        ideal = n_requests / len(self.workers)
        # Include workers that received nothing: they are the most imbalanced
        imbalance = max(abs(distribution[w] - ideal) for w in self.workers) / ideal * 100
        print(f"  Load imbalance: {imbalance:.1f}%")


if __name__ == "__main__":
    workers = [f"worker-{i:02d}" for i in range(1, 5)]
    lb = AILoadBalancer(workers)

    lb.simulate_routing("round_robin", 40)
    lb = AILoadBalancer(workers)  # Reset
    lb.simulate_routing("least_connections", 40)
    lb = AILoadBalancer(workers)  # Reset
    lb.simulate_routing("weighted_least_connections", 40)
