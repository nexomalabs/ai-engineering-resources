# Applied AI Engineering, Volume IV, Chapter 5
# Section 5.10, Rollback Procedures
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import logging
from typing import Callable

logger = logging.getLogger("auto-rollback")

class CanaryController:
    def __init__(
        self,
        get_metrics: Callable[[], dict],
        execute_rollback: Callable[[], None],
        check_interval: int = 60,
        error_rate_threshold: float = 0.02,
        latency_multiplier_threshold: float = 1.5,
    ):
        self.get_metrics = get_metrics
        self.execute_rollback = execute_rollback
        self.check_interval = check_interval
        self.error_rate_threshold = error_rate_threshold
        self.latency_multiplier_threshold = latency_multiplier_threshold
        self._baseline_latency: float | None = None

    def set_baseline(self, latency_p95: float) -> None:
        self._baseline_latency = latency_p95

    async def monitor(self, duration_minutes: int = 60) -> bool:
        """
        Monitor canary metrics for the specified duration.
        Returns True if canary is healthy; False if rollback was triggered.
        """
        checks = (duration_minutes * 60) // self.check_interval
        for _ in range(checks):
            metrics = self.get_metrics()
            if self._should_rollback(metrics):
                logger.warning(
                    "Canary metrics breached thresholds. Triggering automatic rollback."
                )
                self.execute_rollback()
                return False
            await asyncio.sleep(self.check_interval)
        return True

    def _should_rollback(self, metrics: dict) -> bool:
        if metrics.get("error_rate", 0) > self.error_rate_threshold:
            logger.warning(
                "Error rate %.3f exceeds threshold %.3f",
                metrics["error_rate"], self.error_rate_threshold
            )
            return True
        if (self._baseline_latency
                and metrics.get("p95_latency_ms", 0)
                > self._baseline_latency * self.latency_multiplier_threshold):
            logger.warning("P95 latency %.0fms exceeds %.1f× baseline",
                           metrics["p95_latency_ms"], self.latency_multiplier_threshold)
            return True
        return False
