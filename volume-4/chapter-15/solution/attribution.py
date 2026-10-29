"""Step 3: the cost attribution from the chapter's opening story.

When the first peak-month invoice arrived, everyone assumed Wren, which talks to the most
people, was the expensive system. Attributing every model call to the feature and the user
that made it said otherwise. The largest line was the warehouse assistant, and most of that
came from one user: a shift supervisor's script that asked "Are there any delayed parcels?"
every thirty seconds, around the clock, with the full depot status pasted into each request.
The script now runs a database query instead.

The day of calls is simulated from a fixed seed. The volumes and token counts are
illustrative; the prices are the list prices in cost_tracker.py.

    python solution/attribution.py
"""

import random
from collections import defaultdict
from dataclasses import dataclass

from cost_tracker import RequestRecord

SCRIPT_USER = "user_0042"  # the supervisor's account the script ran under
NIGHT = range(0, 6 * 60)  # midnight to 6 a.m., in minutes of the day
DAYS_IN_MONTH = 30


@dataclass
class TimedRecord(RequestRecord):
    minute: int = 0  # the minute of the day the call was made, 0 to 1439


def simulate_peak_day(seed: int = 15) -> list[TimedRecord]:
    """One peak day of Wrenfield's model calls, each tagged with its feature and user."""
    rng = random.Random(seed)
    records: list[TimedRecord] = []

    def call(feature, model, user, minute, tokens_in, tokens_out):
        rid = f"req_{len(records):05d}"
        records.append(TimedRecord(rid, model, tokens_in, tokens_out, feature, user, minute=minute))

    def between(start_hour, end_hour):
        return rng.randrange(start_hour * 60, end_hour * 60)

    for _ in range(15_000):  # Wren: customers, mostly from 7 a.m. to 11 p.m.
        minute = between(0, 24) if rng.random() < 0.1 else between(7, 23)
        tokens = rng.randint(1_200, 2_000), rng.randint(150, 350)
        call("wren", "gpt-6.1-sol", f"cust_{rng.randrange(9_000):04d}", minute, *tokens)
    for _ in range(1_500):  # the claims assistant: twenty claims handlers, office hours
        tokens = rng.randint(3_000, 6_000), rng.randint(300, 600)
        user = f"user_{rng.randrange(200, 220):04d}"
        call("claims_assistant", "gpt-6.1-sol", user, between(8, 18), *tokens)
    for _ in range(6_000):  # customs documents: a service account, around the clock
        tokens = rng.randint(2_000, 4_000), rng.randint(200, 400)
        call("customs_documents", "gpt-6-luna", "svc_customs", between(0, 24), *tokens)
    for _ in range(600):  # the warehouse assistant: forty staff, on shifts from 6 a.m. to 10 p.m.
        tokens = rng.randint(800, 1_500), rng.randint(100, 300)
        user = f"user_{rng.randrange(100, 140):04d}"
        call("warehouse_assistant", "gpt-6.1-sol", user, between(6, 22), *tokens)
    for i in range(24 * 60 * 2):  # the script: every thirty seconds, with the depot status
        tokens = rng.randint(17_000, 19_000), rng.randint(80, 160)
        call("warehouse_assistant", "gpt-6.1-sol", SCRIPT_USER, i // 2, *tokens)
    return records


def by_feature(records: list[TimedRecord]) -> dict[str, tuple[int, float]]:
    """Calls and cost for each feature, most expensive first."""
    totals = defaultdict(lambda: [0, 0.0])
    for r in records:
        totals[r.feature][0] += 1
        totals[r.feature][1] += r.cost_usd
    return {f: (n, cost) for f, (n, cost) in sorted(totals.items(), key=lambda x: -x[1][1])}


def users_of(records: list[TimedRecord], feature: str) -> dict[str, tuple[int, float, int]]:
    """For one feature: each user's calls, cost, and calls between midnight and 6 a.m."""
    totals = defaultdict(lambda: [0, 0.0, 0])
    for r in records:
        if r.feature != feature:
            continue
        user = totals[r.user_id]
        user[0] += 1
        user[1] += r.cost_usd
        user[2] += r.minute in NIGHT
    return {
        u: (n, cost, night)
        for u, (n, cost, night) in sorted(totals.items(), key=lambda x: -x[1][1])
    }


def print_features(title: str, records: list[TimedRecord]) -> None:
    print(title)
    print(f"  {'feature':<20} {'calls':>7} {'day $':>8} {'month $':>9}")
    for feature, (n, cost) in by_feature(records).items():
        print(f"  {feature:<20} {n:>7,} {cost:>8.2f} {cost * DAYS_IN_MONTH:>9,.2f}")
    total = sum(r.cost_usd for r in records)
    print(f"  {'total':<20} {len(records):>7,} {total:>8.2f} {total * DAYS_IN_MONTH:>9,.2f}\n")


def main() -> None:
    day = simulate_peak_day()
    print_features("A peak day of model calls, by feature", day)

    users = users_of(day, "warehouse_assistant")
    feature_cost = sum(cost for _, cost, _ in users.values())
    print("Inside warehouse_assistant, by user")
    print(f"  {'user':<12} {'calls':>6} {'day $':>8} {'share':>6} {'00:00-06:00':>12}")
    for user, (n, cost, night) in list(users.items())[:3]:
        print(f"  {user:<12} {n:>6,} {cost:>8.2f} {cost / feature_cost:>6.1%} {night:>12,}")
    rest = list(users.values())[3:]
    if rest:
        n, cost = sum(u[0] for u in rest), sum(u[1] for u in rest)
        print(f"  {len(rest)} more users: {n:,} calls, ${cost:.2f}\n")

    after = [r for r in day if r.user_id != SCRIPT_USER]
    print_features("With the script replaced by a database query", after)


if __name__ == "__main__":
    main()
