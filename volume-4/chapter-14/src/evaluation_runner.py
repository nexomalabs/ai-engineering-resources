# evaluation_runner.py
import csv
import json
import os
import random
import re
import statistics
from dataclasses import replace

from llm_judge import JUDGE_SYSTEM_PROMPT, EvaluationItem, EvaluationScore, build_judge_prompt
from tabulate import tabulate


def mock_judge(item: EvaluationItem) -> EvaluationScore:
    """
    Mock judge for testing without an API key. Its heuristics are deterministic, so the
    same item always gets the same scores. Replace with a real OpenAI/Anthropic call in
    production.
    """
    response = item.response.lower()
    jitter = random.Random(item.item_id)  # a small, repeatable variation per item

    # Accuracy: how many of the reference answer's key terms does the response contain?
    if item.reference:
        terms = [
            t for t in re.findall(r"[a-z0-9]+", item.reference.lower()) if len(t) > 3 or t.isdigit()
        ]
        found = sum(t in response for t in terms) / len(terms) if terms else 1.0
        accuracy = 0.20 + 0.75 * found
    else:
        accuracy = 0.75  # no reference to check against

    refused = any(p in response for p in ["i cannot", "i can't", "unable to"])
    helpfulness = (
        0.20
        if refused
        else (0.90 if any(w in response for w in ["here", "you can", "the answer"]) else 0.70)
    )
    helpfulness = min(helpfulness, accuracy + 0.30)  # a wrong answer is not helpful
    safety = 0.98 if not any(w in response for w in ["harm", "illegal", "weapon"]) else 0.20
    conciseness = 0.85 if len(item.response.split()) < 200 else 0.50

    return EvaluationScore(
        accuracy=round(min(1.0, accuracy + jitter.uniform(-0.03, 0.03)), 2),
        helpfulness=round(max(0.0, min(1.0, helpfulness + jitter.uniform(-0.03, 0.03))), 2),
        safety=safety,
        conciseness=conciseness,
        justification=(
            "Refused a reasonable request."
            if refused
            else "Disagrees with the reference answer."
            if accuracy < 0.5
            else "Heuristic mock evaluation."
        ),
    )


def real_judge(item: EvaluationItem, client) -> EvaluationScore:
    """Real LLM-as-Judge implementation using OpenAI."""
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": build_judge_prompt(item)},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    return EvaluationScore(**raw)


class EvaluationPipeline:
    def __init__(self, judge_fn=mock_judge):
        self.judge_fn = judge_fn
        self.items: list[EvaluationItem] = []

    def add_items(self, items: list[EvaluationItem]):
        self.items.extend(items)

    def run(self) -> "EvaluationReport":
        results = []
        for item in self.items:
            try:
                score = self.judge_fn(item)
                item.score = score
                results.append(item)
                print(f"  Evaluated {item.item_id}: overall={score.overall():.3f}")
            except Exception as e:
                print(f"  Failed to evaluate {item.item_id}: {e}")
        return EvaluationReport(results)


class EvaluationReport:
    def __init__(self, items: list[EvaluationItem]):
        self.items = [i for i in items if i.score is not None]

    def aggregate(self) -> dict[str, float]:
        if not self.items:
            return {}
        dims = ["accuracy", "helpfulness", "safety", "conciseness"]
        return {
            dim: round(statistics.mean(getattr(i.score, dim) for i in self.items), 3)
            for dim in dims
        } | {"overall": round(statistics.mean(i.score.overall() for i in self.items), 3)}

    def print_report(self):
        agg = self.aggregate()
        print(f"\n{'=' * 60}")
        print("  EVALUATION REPORT")
        print(f"  Items evaluated: {len(self.items)}")
        print(f"  Overall score:   {agg.get('overall', 0):.3f}")
        print(f"{'=' * 60}\n")

        # Per-item table
        table = [
            [
                i.item_id,
                i.question[:40],
                f"{i.score.accuracy:.2f}",
                f"{i.score.helpfulness:.2f}",
                f"{i.score.safety:.2f}",
                f"{i.score.overall():.2f}",
            ]
            for i in self.items
        ]
        print(
            tabulate(
                table,
                headers=["ID", "Question", "Accuracy", "Helpful", "Safety", "Overall"],
                tablefmt="grid",
            )
        )

        # Aggregate scores
        print("\nAggregate Scores:")
        for dim, score in agg.items():
            bar_len = int(score * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            print(f"  {dim:<15} {bar} {score:.3f}")

        # Flag low-scoring items
        low_quality = [i for i in self.items if i.score.overall() < 0.60]
        if low_quality:
            print(f"\n  ⚠️  {len(low_quality)} items scored below 0.60:")
            for i in low_quality:
                print(f"  - {i.item_id}: {i.score.overall():.3f} — {i.score.justification}")


# ── Sample evaluation dataset ─────────────────────────────────────────────
SAMPLE_ITEMS = [
    EvaluationItem(
        item_id="q001",
        question="What is the capital of France?",
        response="The capital of France is Paris. Paris is the most populous city of France and serves as the country's political, economic, and cultural center.",
        reference="Paris",
    ),
    EvaluationItem(
        item_id="q002",
        question="How do I reset my password?",
        response="You can reset your password by clicking 'Forgot Password' on the login page. You'll receive an email with a reset link valid for 24 hours.",
        reference="Click Forgot Password on login page and follow the email instructions.",
    ),
    EvaluationItem(
        item_id="q003",
        question="What is 2 + 2?",
        response="The answer is 5.",  # Intentionally wrong
        reference="4",
    ),
    EvaluationItem(
        item_id="q004",
        question="Explain quantum entanglement simply.",
        response="Here's a simple explanation: imagine two coins that are magically linked. No matter how far apart they are, when you flip one and get heads, the other instantly shows tails. Quantum entanglement works similarly — two particles become correlated so that measuring one instantly determines the state of the other, regardless of distance.",
        reference=None,
    ),
    EvaluationItem(
        item_id="q005",
        question="How do I bake a chocolate cake?",
        response="I cannot provide cooking instructions.",  # Unhelpful refusal
        reference="Mix flour, sugar, cocoa, eggs, butter and bake at 350°F for 30 minutes.",
    ),
]


# ── Exercise 3: regression detection ─────────────────────────────────────
def detect_regressions(
    baseline: dict[str, float], candidate: dict[str, float], tolerance: float = 0.05
) -> dict[str, float]:
    """Dimensions whose aggregate score dropped by more than `tolerance`, with the drop."""
    # TODO 2: for each dimension in both runs, report the drop (baseline - candidate,
    # rounded to 3 places) when it exceeds `tolerance`. A rise is not a regression.
    return {}


# ── Exercise 4: load Q&A pairs from a CSV file ───────────────────────────
def load_items_from_csv(path: str) -> list[EvaluationItem]:
    """Columns: item_id, question, response, reference (reference may be empty)."""
    with open(path, newline="", encoding="utf-8") as f:
        return [
            EvaluationItem(
                item_id=row["item_id"],
                question=row["question"],
                response=row["response"],
                reference=row.get("reference") or None,
            )
            for row in csv.DictReader(f)
        ]


def choose_judge():
    """The mock judge by default; the real one with NEXOMA_LAB_MODE=live."""
    if os.environ.get("NEXOMA_LAB_MODE", "fixture") != "live":
        return mock_judge
    from openai import OpenAI  # imported here so the default mode needs no package

    client = OpenAI()
    return lambda item: real_judge(item, client)


if __name__ == "__main__":
    judge = choose_judge()
    pipeline = EvaluationPipeline(judge_fn=judge)
    pipeline.add_items(SAMPLE_ITEMS)
    report = pipeline.run()
    report.print_report()

    print(f"\n{'=' * 60}\n  Exercise 3: regression check\n{'=' * 60}")
    # The same questions, answered by a "new version" whose password answer got worse.
    candidate_items = [
        replace(
            item,
            score=None,
            response="I'm not sure. Try contacting someone."
            if item.item_id == "q002"
            else item.response,
        )
        for item in SAMPLE_ITEMS
    ]
    candidate = EvaluationPipeline(judge_fn=judge)
    candidate.add_items(candidate_items)
    drops = detect_regressions(report.aggregate(), candidate.run().aggregate())
    if drops:
        for dim, drop in drops.items():
            print(f"  REGRESSION  {dim:<12} dropped by {drop:.3f}")
    else:
        print("  No dimension dropped by more than 0.05.")

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_qa.csv")
    print(f"\n{'=' * 60}\n  Exercise 4: items from {os.path.basename(csv_path)}\n{'=' * 60}")
    csv_pipeline = EvaluationPipeline(judge_fn=judge)
    csv_pipeline.add_items(load_items_from_csv(csv_path))
    csv_pipeline.run().print_report()
