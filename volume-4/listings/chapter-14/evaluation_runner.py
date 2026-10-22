# Applied AI Engineering, Volume IV, Chapter 14
# Hands-on Lab: LLM-as-Judge Evaluation Pipeline
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# evaluation_runner.py
import json
import random
import statistics
from llm_judge import EvaluationItem, EvaluationScore, build_judge_prompt, JUDGE_SYSTEM_PROMPT
from tabulate import tabulate


def mock_judge(item: EvaluationItem) -> EvaluationScore:
    """
    Mock judge for testing without an API key.
    Replace with a real OpenAI/Anthropic call in production.
    """
    # Simulate scoring based on response length and keyword heuristics
    response = item.response.lower()
    question = item.question.lower()

    # Simple heuristic scoring
    accuracy = random.gauss(0.78, 0.12)
    helpfulness = 0.9 if any(w in response for w in ["here", "you can", "the answer"]) else 0.65
    safety = 0.98 if not any(w in response for w in ["harm", "illegal", "weapon"]) else 0.20
    conciseness = 0.85 if len(item.response.split()) < 200 else 0.50

    return EvaluationScore(
        accuracy=max(0.0, min(1.0, accuracy)),
        helpfulness=max(0.0, min(1.0, helpfulness + random.gauss(0, 0.05))),
        safety=safety,
        conciseness=max(0.0, min(1.0, conciseness + random.gauss(0, 0.03))),
        justification="Heuristic mock evaluation for testing purposes.",
    )


def real_judge(item: EvaluationItem, client) -> EvaluationScore:
    """Real LLM-as-Judge implementation using OpenAI."""
    response = client.chat.completions.create(
        model="gpt-6-luna",
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
        print(f"\n{'='*60}")
        print("  EVALUATION REPORT")
        print(f"  Items evaluated: {len(self.items)}")
        print(f"  Overall score:   {agg.get('overall', 0):.3f}")
        print(f"{'='*60}\n")

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
        print(tabulate(
            table,
            headers=["ID", "Question", "Accuracy", "Helpful", "Safety", "Overall"],
            tablefmt="grid",
        ))

        # Aggregate scores
        print(f"\nAggregate Scores:")
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


if __name__ == "__main__":
    pipeline = EvaluationPipeline(judge_fn=mock_judge)
    pipeline.add_items(SAMPLE_ITEMS)
    report = pipeline.run()
    report.print_report()
