"""Canary routing with automated rollback, as in the chapter's opening story.

A share of requests goes to the canary model version, and each version's requests, errors
and cost are counted. Once the canary has served enough requests to compare, the
controller rolls it back, sending it no more traffic, if its cost per request passes 1.5
times the stable version's or its error rate passes twice the stable version's.
"""

import random
from dataclasses import asdict, dataclass

# Illustrative prices per million tokens. Both versions are priced the same here, so any
# difference in cost per request comes from how many tokens each version uses.
PRICE_PER_MILLION_TOKENS = {"input": 2.00, "output": 10.00}


@dataclass
class VersionStats:
    requests: int = 0
    errors: int = 0
    cost_usd: float = 0.0

    @property
    def cost_per_request(self) -> float:
        served = self.requests - self.errors
        return self.cost_usd / served if served else 0.0

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests if self.requests else 0.0


class Canary:
    def __init__(
        self,
        stable_model: str,
        canary_model: str = "",
        percent: float = 0.0,
        *,
        min_requests: int = 20,
        cost_ratio_limit: float = 1.5,
        error_ratio_limit: float = 2.0,
        seed: int | None = None,
    ):
        self.stable_model = stable_model
        self.canary_model = canary_model
        self.percent = percent if canary_model else 0.0
        self.min_requests = min_requests
        self.cost_ratio_limit = cost_ratio_limit
        self.error_ratio_limit = error_ratio_limit
        self.rng = random.Random(seed)
        self.stats = {"stable": VersionStats(), "canary": VersionStats()}
        self.rollback_reason = ""

    def route(self) -> tuple[str, str]:
        """Choose the track for the next request: ("canary", model) or ("stable", model)."""
        if self.percent > 0 and self.rng.random() * 100 < self.percent:
            return "canary", self.canary_model
        return "stable", self.stable_model

    def record(
        self, track: str, prompt_tokens: int = 0, completion_tokens: int = 0, error: bool = False
    ) -> str:
        """Count one request, then check the canary. Returns the rollback reason, if any."""
        stats = self.stats[track]
        stats.requests += 1
        if error:
            stats.errors += 1
        else:
            prices = PRICE_PER_MILLION_TOKENS
            tokens_cost = prompt_tokens * prices["input"] + completion_tokens * prices["output"]
            stats.cost_usd += tokens_cost / 1_000_000
        return self.check()

    def check(self) -> str:
        """Roll the canary back if it breaches a limit. Returns the reason, or ""."""
        # TODO 4: Once the canary has served at least min_requests (and still has traffic),
        #   compare it with the stable version. If its cost_per_request is more than
        #   cost_ratio_limit times the stable one, or its error_rate is above
        #   max(error_ratio_limit x the stable error rate, 0.01), call self._roll_back()
        #   with a reason and return it. As supplied, the canary is never rolled back.
        return ""

    def _roll_back(self, reason: str) -> str:
        self.percent = 0.0
        self.rollback_reason = reason
        return reason

    def status(self) -> dict:
        def describe(stats: VersionStats) -> dict:
            return {**asdict(stats), "cost_per_request_usd": round(stats.cost_per_request, 6)}

        return {
            "stable_model": self.stable_model,
            "canary_model": self.canary_model,
            "canary_percent": self.percent,
            "rolled_back": bool(self.rollback_reason),
            "rollback_reason": self.rollback_reason,
            "stable": describe(self.stats["stable"]),
            "canary": describe(self.stats["canary"]),
        }
