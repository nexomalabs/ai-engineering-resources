"""Lab 15 — Cost Tracking and Optimization Dashboard (starter).

This file RUNS as supplied. The monthly projection is just the sample's cost, prompt
compression is assumed to shrink the whole bill, and (in cost_tracker.py) a cached request
is still charged. Complete the three TODOs. Run from the lab folder:

    python src/cost_analyzer.py
"""

import random

from cost_tracker import PRICING, RequestRecord, generate_sample_requests
from tabulate import tabulate


class CostAnalyzer:
    def __init__(self, records: list[RequestRecord]):
        self.records = records

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def cost_by_feature(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for r in self.records:
            result[r.feature] = result.get(r.feature, 0.0) + r.cost_usd
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def cost_by_model(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for r in self.records:
            result[r.model_id] = result.get(r.model_id, 0.0) + r.cost_usd
        return result

    def monthly_projection(self, sample_days: float = 1.0) -> float:
        """Project monthly cost from a sample period."""
        # TODO 2: Scale the sample to 30 days: cost per day of the sample, times 30.
        return self.total_cost()

    def avg_cost_per_request(self) -> float:
        return self.total_cost() / len(self.records) if self.records else 0.0

    def print_summary(self, sample_days: float = 1.0):
        total = self.total_cost()
        monthly = self.monthly_projection(sample_days)
        avg = self.avg_cost_per_request()

        print(f"\n{'=' * 60}")
        print("  COST ANALYSIS REPORT")
        print(f"  Requests analyzed: {len(self.records):,}")
        print(f"  Sample period:     {sample_days} day(s)")
        print(f"  Total cost:        ${total:.4f}")
        print(f"  Avg per request:   ${avg:.6f}")
        print(f"  Monthly projection: ${monthly:.2f}")
        print(f"{'=' * 60}\n")

        # By feature
        print("Cost by Feature:")
        feature_data = [
            [feat, f"${cost:.4f}", f"{cost / total * 100:.1f}%"]
            for feat, cost in self.cost_by_feature().items()
        ]
        print(tabulate(feature_data, headers=["Feature", "Cost", "% Total"], tablefmt="simple"))

        # By model
        print("\nCost by Model:")
        model_data = [
            [model, f"${cost:.4f}", f"{cost / total * 100:.1f}%"]
            for model, cost in self.cost_by_model().items()
        ]
        print(tabulate(model_data, headers=["Model", "Cost", "% Total"], tablefmt="simple"))


class OptimizationSimulator:
    """Simulate cost savings from three optimization strategies."""

    def __init__(self, records: list[RequestRecord]):
        self.original = records
        self.baseline_cost = sum(r.cost_usd for r in records)

    def simulate_prompt_compression(
        self, compression_ratio: float = 0.25
    ) -> tuple[list[RequestRecord], float]:
        """
        Simulate prompt compression reducing input tokens by compression_ratio.
        E.g., 0.25 = 25% reduction in input tokens.
        """
        import copy

        compressed = []
        for r in self.original:
            new_r = copy.copy(r)
            # TODO 3: Compression shortens the input only. Reduce tokens_in by
            #   compression_ratio and reprice the request with its unchanged tokens_out.
            new_r.cost_usd = r.cost_usd * (1 - compression_ratio)
            compressed.append(new_r)
        return compressed, sum(r.cost_usd for r in compressed)

    def simulate_model_downgrade(
        self, downgrade_fraction: float = 0.60, downgrade_to: str = "gpt-6-luna"
    ) -> tuple[list[RequestRecord], float]:
        """
        Simulate routing downgrade_fraction of gpt-6.1-sol requests to a cheaper model.
        Assumes quality is acceptable for the downgraded requests.
        """
        import copy
        import random

        downgraded = []
        for r in self.original:
            new_r = copy.copy(r)
            if r.model_id == "gpt-6.1-sol" and random.random() < downgrade_fraction:
                new_r.model_id = downgrade_to
                pricing = PRICING[downgrade_to]
                new_r.cost_usd = pricing.cost(r.tokens_in, r.tokens_out)
            downgraded.append(new_r)
        return downgraded, sum(r.cost_usd for r in downgraded)

    def simulate_semantic_caching(
        self, cache_hit_rate: float = 0.35
    ) -> tuple[list[RequestRecord], float]:
        """
        Simulate semantic caching with a given cache hit rate.
        Cached requests have zero cost.
        """
        import copy
        import random

        cached_records = []
        for r in self.original:
            new_r = copy.copy(r)
            if random.random() < cache_hit_rate:
                new_r.cached = True
                new_r.cost_usd = 0.0
            cached_records.append(new_r)
        return cached_records, sum(r.cost_usd for r in cached_records)

    def print_optimization_report(self, sample_days: float = 1.0):
        monthly_baseline = self.baseline_cost / sample_days * 30

        _, compression_cost = self.simulate_prompt_compression(0.25)
        _, downgrade_cost = self.simulate_model_downgrade(0.60)
        _, caching_cost = self.simulate_semantic_caching(0.35)

        strategies = [
            ("Baseline (no optimization)", self.baseline_cost, 0),
            (
                "Prompt compression (25%)",
                compression_cost,
                (self.baseline_cost - compression_cost) / self.baseline_cost * 100,
            ),
            (
                "Model routing (60% to Luna)",
                downgrade_cost,
                (self.baseline_cost - downgrade_cost) / self.baseline_cost * 100,
            ),
            (
                "Semantic caching (35% hit rate)",
                caching_cost,
                (self.baseline_cost - caching_cost) / self.baseline_cost * 100,
            ),
        ]

        print(f"\n{'=' * 65}")
        print("  OPTIMIZATION SIMULATION REPORT")
        print(f"  Baseline sample cost: ${self.baseline_cost:.4f}")
        print(f"  Baseline monthly projection: ${monthly_baseline:.2f}")
        print(f"{'=' * 65}\n")

        table = []
        for name, cost, savings_pct in strategies:
            monthly = cost / sample_days * 30
            monthly_savings = monthly_baseline - monthly
            table.append(
                [name, f"${monthly:.2f}", f"${monthly_savings:.2f}", f"{savings_pct:.1f}%"]
            )

        print(
            tabulate(
                table,
                headers=["Strategy", "Monthly Est.", "Monthly Savings", "Savings %"],
                tablefmt="simple",
            )
        )


if __name__ == "__main__":
    random.seed(42)  # reproducible sample traffic and simulations
    print("Generating 1,000 sample requests (representing 1 day of traffic)...")
    records = generate_sample_requests(1000)

    analyzer = CostAnalyzer(records)
    analyzer.print_summary(sample_days=1.0)

    optimizer = OptimizationSimulator(records)
    optimizer.print_optimization_report(sample_days=1.0)
