"""Step 5: the quality drift from the chapter's opening story, found by model version.

For six days nothing on Wren's infrastructure dashboard changed, while the quality score of
its refund answers drifted down and their length drifted up. The provider was rolling a new
model out behind the alias Wren called, a larger share of traffic each day. A short-window
alert cannot see a slide that slow; a long-window one can. And grouping quality by the
model version recorded with each response shows the cause at once: each version is steady,
and the new one is worse. Pinning the old version stopped the drift.

The log is simulated, from a fixed seed. The snapshot names are illustrative.

    python solution/quality_drift.py
"""

import random
import statistics
from collections import defaultdict

OLD, NEW = "gpt-6.1-sol-2026-11-04", "gpt-6.1-sol-2026-12-08"
ROLLOUT_STARTS = 8  # the day the provider began moving the alias to the new version
PINNED_FROM = 15  # the day Wren's configuration pinned the old version


def simulate_log(days: int = 16, per_day: int = 400, seed: int = 4) -> list[dict]:
    """One record per refund answer: the day, the reported model version, quality, length."""
    rng = random.Random(seed)
    log = []
    for day in range(1, days + 1):
        share_new = min(1.0, max(0.0, (day - ROLLOUT_STARTS + 1) / 6))
        if day >= PINNED_FROM:
            share_new = 0.0
        for _ in range(per_day):
            version = NEW if rng.random() < share_new else OLD
            quality = rng.gauss(0.82 if version == OLD else 0.70, 0.08)
            words = rng.gauss(118 if version == OLD else 172, 20)
            log.append({"day": day, "model_version": version, "quality": quality, "words": words})
    return log


def daily_means(log: list[dict], field: str) -> dict[int, float]:
    by_day = defaultdict(list)
    for record in log:
        by_day[record["day"]].append(record[field])
    return {day: statistics.mean(values) for day, values in sorted(by_day.items())}


def long_window_alert(
    quality: dict[int, float], window: int = 4, baseline_days: int = 7, drop: float = 0.08
) -> int | None:
    """The first day the mean of the last `window` days falls `drop` below the baseline."""
    days = sorted(quality)
    baseline = statistics.mean(quality[d] for d in days[:baseline_days])
    for i in range(baseline_days + window - 1, len(days)):
        recent = statistics.mean(quality[d] for d in days[i - window + 1 : i + 1])
        if baseline - recent >= drop:
            return days[i]
    return None


def quality_by_version(log: list[dict]) -> dict[str, tuple[float, float, int]]:
    """Mean quality, mean length in words, and count, for each reported model version."""
    groups = defaultdict(list)
    for record in log:
        groups[record["model_version"]].append(record)
    return {
        version: (
            statistics.mean(r["quality"] for r in records),
            statistics.mean(r["words"] for r in records),
            len(records),
        )
        for version, records in sorted(groups.items())
    }


def main() -> None:
    log = simulate_log()
    quality, words = daily_means(log, "quality"), daily_means(log, "words")
    alert_day = long_window_alert(quality)
    print(f"{'day':>3} {'quality':>8} {'words':>6}  note")
    for day in quality:
        note = ""
        if day == ROLLOUT_STARTS:
            note = "provider starts moving the alias"
        if day == alert_day:
            note = "long-window alert fires"
        if day == PINNED_FROM:
            note = "old version pinned"
        print(f"{day:>3} {quality[day]:>8.2f} {words[day]:>6.0f}  {note}")
    print("\nQuality by the model version recorded with each response:")
    for version, (mean_quality, mean_words, n) in quality_by_version(log).items():
        print(f"  {version:<24} quality {mean_quality:.2f}, {mean_words:.0f} words, {n} answers")


if __name__ == "__main__":
    main()
