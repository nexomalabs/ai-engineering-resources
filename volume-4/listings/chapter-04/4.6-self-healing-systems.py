# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.6, Self-Healing Systems
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from dataclasses import dataclass
from typing import Callable
import logging

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    component: str
    healthy: bool
    metric_name: str
    metric_value: float
    threshold: float
    message: str

class HealthMonitor:
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._checks: list[tuple[str, Callable, float, Callable]] = []

    def register_check(
        self,
        name: str,
        metric_fn: Callable[[], float],
        threshold: float,
        remediation: Callable[[HealthStatus], None],
    ) -> None:
        self._checks.append((name, metric_fn, threshold, remediation))

    async def run(self) -> None:
        while True:
            for name, metric_fn, threshold, remediation in self._checks:
                try:
                    value = metric_fn()
                    healthy = value <= threshold
                    status = HealthStatus(
                        component=name,
                        healthy=healthy,
                        metric_name="value",
                        metric_value=value,
                        threshold=threshold,
                        message="OK" if healthy else f"{value:.2f} exceeds {threshold:.2f}",
                    )
                    if not healthy:
                        logger.warning(
                            "[SELF-HEAL] %s unhealthy: %s", name, status.message
                        )
                        remediation(status)
                except Exception as exc:
                    logger.error("Health check '%s' failed: %s", name, exc)
            await asyncio.sleep(self.check_interval)
