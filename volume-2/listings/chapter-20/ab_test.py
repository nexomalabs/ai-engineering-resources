# Applied AI Engineering, Volume II, Chapter 20
# Section 20.7, Optimization Results
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# ab_test.py

import random
from collections import defaultdict

VARIANT_A_RESPONSE_TEMPLATE = """\
You are Alex, a ShopCore customer support specialist.

BRAND VOICE: Warm, professional, solution-focused. 40-80 words.

TICKET CATEGORY: {{category}}
CUSTOMER TICKET: {{ticket_text}}

Draft a response. Respond ONLY with valid JSON:
{"response_draft": "<string>", "tone": "<string>", "word_count": <int>}
BEGIN:"""

VARIANT_B_RESPONSE_TEMPLATE = """\
You are Alex, a ShopCore customer support specialist with expertise in
e-commerce logistics and customer satisfaction recovery.

BRAND VOICE REQUIREMENTS:
- Open with acknowledgment of the customer's situation
- Provide specific, actionable information (not generic)
- Close with a proactive next step
- Target length: 50–100 words for routine issues, up to 150 for complex

TICKET CATEGORY: {{category}}
CUSTOMER TICKET: {{ticket_text}}
EXTRACTED ORDER/ACCOUNT CONTEXT: {{extracted_ids}}

Constraints:
- Never speculate about delivery dates beyond what tracking shows
- Always offer an alternative if the requested action is unavailable
- Do not repeat the customer's question back to them

Draft a response. Respond ONLY with valid JSON:
{"response_draft": "<string>", "tone": "<string>", "word_count": <int>}
BEGIN:"""


def run_ab_test(pipeline_a: SupportPipeline, pipeline_b: SupportPipeline,
                test_cases: list[dict], runs_per_case: int = 3) -> dict:
    """
    Run an A/B test comparing two pipeline variants on the same test cases.
    Returns aggregated quality metrics for both variants.
    """
    scores_a = defaultdict(list)
    scores_b = defaultdict(list)

    for tc in test_cases:
        for _ in range(runs_per_case):
            result_a = pipeline_a.run(tc["input"])
            result_b = pipeline_b.run(tc["input"])

            if result_a.get("evaluation"):
                for dim, data in result_a["evaluation"]["scores"].items():
                    scores_a[dim].append(data["score"])
                scores_a["weighted_total"].append(result_a["evaluation"]["weighted_total"])

            if result_b.get("evaluation"):
                for dim, data in result_b["evaluation"]["scores"].items():
                    scores_b[dim].append(data["score"])
                scores_b["weighted_total"].append(result_b["evaluation"]["weighted_total"])

    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    summary_a = {k: avg(v) for k, v in scores_a.items()}
    summary_b = {k: avg(v) for k, v in scores_b.items()}

    winner = "B" if summary_b.get("weighted_total", 0) > summary_a.get("weighted_total", 0) else "A"

    return {
        "variant_a": summary_a,
        "variant_b": summary_b,
        "winner": winner,
        "improvement": round(
            summary_b.get("weighted_total", 0) - summary_a.get("weighted_total", 0), 3
        )
    }
