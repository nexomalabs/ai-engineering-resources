"""Step 3: the release gate from the chapter's opening story, checked slice by slice.

Dev's new refund prompt raised the average score on Wren's evaluation suite and sank one
slice: Portuguese conversations, which it answered in English. A gate on the average would
have passed it. This gate compares the whole suite and every slice, each language and each
customer tier, and blocks a change when any of them falls by more than the tolerance.

refund_v1.csv, refund_v2.csv and refund_v3.csv hold three prompt versions' answers to the
same twelve refund questions: v1 is the prompt in production, v2 is Dev's new prompt, and v3
is v2 with the Portuguese replies fixed. The mock judge scores them, so the output repeats;
with NEXOMA_LAB_MODE=live the real judge does. The tolerance is fixed because the mock judge
gives the same scores on every run. With a real judge, set it from the spread of repeated
runs of the unchanged prompt.

    python solution/quality_gate.py
"""

import os
import statistics
from collections import defaultdict

from evaluation_runner import choose_judge, load_items_from_csv
from llm_judge import EvaluationItem

HERE = os.path.dirname(os.path.abspath(__file__))
TOLERANCE = 0.05


def score_run(path: str, judge) -> list[EvaluationItem]:
    """One prompt version's answers to the suite, each scored by the judge."""
    items = load_items_from_csv(path)
    for item in items:
        item.score = judge(item)
    return items


def mean_score(items: list[EvaluationItem]) -> float:
    return statistics.mean(item.score.overall() for item in items)


def slice_means(items: list[EvaluationItem], key: str) -> dict[str, tuple[int, float]]:
    """For each value of one slice, such as each language: its item count and mean score."""
    groups = defaultdict(list)
    for item in items:
        groups[item.slices[key]].append(item)
    return {value: (len(group), mean_score(group)) for value, group in sorted(groups.items())}


def quality_gate(
    baseline: list[EvaluationItem],
    candidate: list[EvaluationItem],
    keys: tuple[str, ...] = ("language", "tier"),
    tolerance: float = TOLERANCE,
) -> tuple[list[tuple[str, int, float, float]], list[str]]:
    """Compare two scored runs of the same suite, overall and then slice by slice.

    Returns a row (name, items, baseline mean, candidate mean) for the whole suite and for
    every slice, and the names of those whose mean fell by more than `tolerance`. Any name
    in that list blocks the change.
    """
    rows = [("all", len(baseline), mean_score(baseline), mean_score(candidate))]
    for key in keys:
        before, after = slice_means(baseline, key), slice_means(candidate, key)
        for value, (n, mean) in before.items():
            rows.append((f"{key}={value}", n, mean, after[value][1]))
    blocked = [name for name, _, old, new in rows if old - new > tolerance]
    return rows, blocked


def main() -> None:
    judge = choose_judge()
    runs = {v: score_run(os.path.join(HERE, f"refund_{v}.csv"), judge) for v in ("v1", "v2", "v3")}
    for version in ("v2", "v3"):
        rows, blocked = quality_gate(runs["v1"], runs[version])
        print(f"Refund prompt {version} against v1, tolerance {TOLERANCE}")
        print(f"  {'slice':<15} {'items':>5} {'v1':>6} {version:>6} {'change':>7}")
        for name, n, old, new in rows:
            flag = "  BLOCK" if name in blocked else ""
            print(f"  {name:<15} {n:>5} {old:>6.3f} {new:>6.3f} {new - old:>+7.3f}{flag}")
        print(f"  Gate: {'blocked by ' + ', '.join(blocked) if blocked else 'passed'}\n")


if __name__ == "__main__":
    main()
