# alert_evaluator.py
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

import httpx


@dataclass
class AlertRule:
    name: str
    description: str
    severity: str
    metric_query: str  # Prometheus metric name to check
    threshold: float
    comparison: str  # "gt", "lt", "gte", "lte"
    window_seconds: int  # evaluation window
    evaluator: Callable[[], float]  # callable returning current metric value
    runbook_url: str = ""


@dataclass
class AlertFiring:
    rule_name: str
    severity: str
    current_value: float
    threshold: float
    fired_at: float
    description: str


class AlertEvaluator:
    def __init__(self, prometheus_url: str = "http://localhost:8000"):
        self.prometheus_url = prometheus_url
        self.fired_alerts: dict[str, AlertFiring] = {}
        self.rules: list[AlertRule] = []

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)

    def _compare(self, value: float, threshold: float, op: str) -> bool:
        ops = {
            "gt": value > threshold,
            "gte": value >= threshold,
            "lt": value < threshold,
            "lte": value <= threshold,
        }
        return ops.get(op, False)

    def _fetch_metric(self, metric_name: str) -> Optional[float]:
        """Fetch a metric value from the /metrics endpoint."""
        try:
            resp = httpx.get(f"{self.prometheus_url}/metrics", timeout=5)
            resp.raise_for_status()
            for line in resp.text.splitlines():
                if line.startswith(metric_name + " ") or line.startswith(metric_name + "{"):
                    # Extract the last numeric value
                    match = re.search(r"(\d+\.?\d*(?:e[+-]?\d+)?)$", line)
                    if match:
                        return float(match.group(1))
        except Exception:
            return None
        return None

    def evaluate(self) -> list[AlertFiring]:
        """Evaluate all rules and return currently firing alerts."""
        firing = []
        for rule in self.rules:
            try:
                current_value = rule.evaluator()
            except Exception:
                continue

            if current_value is None:
                continue

            is_firing = self._compare(current_value, rule.threshold, rule.comparison)

            if is_firing:
                if rule.name not in self.fired_alerts:
                    alert = AlertFiring(
                        rule_name=rule.name,
                        severity=rule.severity,
                        current_value=current_value,
                        threshold=rule.threshold,
                        fired_at=time.time(),
                        description=rule.description,
                    )
                    self.fired_alerts[rule.name] = alert
                    print(
                        f"  🔴 ALERT FIRING [{rule.severity.upper()}]: {rule.name}\n"
                        f"     Value: {current_value:.4f} {rule.comparison} {rule.threshold}\n"
                        f"     {rule.description}\n"
                    )
                firing.append(self.fired_alerts[rule.name])
            # TODO 3: When a rule that was firing no longer fires, print
            #   "ALERT RESOLVED: <name>" and remove it from self.fired_alerts.

        return firing


def run_alert_evaluation_loop(service_url: str = "http://localhost:8000"):
    """Run continuous alert evaluation against a live service."""
    evaluator = AlertEvaluator(prometheus_url=service_url)

    # Define alert rules with simple evaluators that call /metrics. The counters
    # are cumulative since the service started; a production rule would use
    # Prometheus's rate() over window_seconds instead.
    def error_rate_evaluator():
        """Estimate error rate from counter values."""
        metrics_text = httpx.get(f"{service_url}/metrics", timeout=5).text
        success = 0
        errors = 0
        for line in metrics_text.splitlines():
            if 'ai_requests_total{endpoint="complete",status="success"}' in line:
                val = line.split()[-1]
                success = float(val)
            if 'ai_requests_total{endpoint="complete",status="error"}' in line:
                val = line.split()[-1]
                errors = float(val)
        total = success + errors
        return errors / total if total > 0 else 0.0

    def safety_rate_evaluator():
        """Get total safety filter triggers."""
        metrics_text = httpx.get(f"{service_url}/metrics", timeout=5).text
        for line in metrics_text.splitlines():
            if "ai_safety_filter_triggered_total" in line and not line.startswith("#"):
                return float(line.split()[-1])
        return 0.0

    evaluator.add_rule(
        AlertRule(
            name="high_error_rate",
            description="Error rate since the service started exceeds 5%.",
            severity="high",
            metric_query="ai_errors_total",
            threshold=0.05,
            comparison="gt",
            window_seconds=300,
            evaluator=error_rate_evaluator,
            runbook_url="https://runbooks.internal/ai/high-error-rate",
        )
    )

    evaluator.add_rule(
        AlertRule(
            name="safety_filter_spike",
            description="Safety filter triggered 10 or more times.",
            severity="critical",
            metric_query="ai_safety_filter_triggered_total",
            threshold=10.0,
            comparison="gte",
            window_seconds=60,
            evaluator=safety_rate_evaluator,
            runbook_url="https://runbooks.internal/ai/safety-filter-spike",
        )
    )

    print("Alert evaluator running. Press Ctrl+C to stop.\n")
    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Evaluating alert rules...")
        evaluator.evaluate()
        time.sleep(30)


if __name__ == "__main__":
    # To run: start ai_service_monitored.py first, then run this script
    run_alert_evaluation_loop()
