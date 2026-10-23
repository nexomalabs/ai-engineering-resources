import sys
from pathlib import Path

# Find the volume's shared/ folder, which holds the recording client.
sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in Path(__file__).resolve().parents
            if (p / "shared" / "nexoma_labs").is_dir()
        )
    ),
)

import json
import os

from nexoma_labs import OpenAI  # records and replays responses; see shared/
from rouge_score import rouge_scorer

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# TEST DATA: Articles and Summaries to Evaluate
# ============================================================

ARTICLES = [
    {
        "article": """The James Webb Space Telescope has captured unprecedented images of the Carina Nebula,
revealing thousands of previously unseen young stars in intricate detail. The nebula, located 7,600
light-years from Earth, is a stellar nursery where new stars are constantly forming. The telescope's
infrared capabilities allow it to peer through the thick dust clouds that blocked visible-light
observations, exposing the birth of stars for the first time. Scientists believe this data will
fundamentally change our understanding of stellar formation processes.""",
        "reference_summary": "The James Webb Space Telescope has revealed thousands of previously hidden young stars in the Carina Nebula using infrared imaging that penetrates dust clouds, potentially revolutionizing our understanding of stellar formation.",
        "candidate_summaries": [
            # Good summary
            "Webb's infrared telescope revealed thousands of new young stars in the Carina Nebula, 7,600 light-years away, by seeing through dust clouds that blocked previous observations, potentially transforming understanding of stellar birth.",
            # Missing key info
            "The James Webb Space Telescope took pictures of a nebula.",
            # Hallucinated fact
            "The James Webb Space Telescope discovered a new galaxy 7,600 light-years away and captured images of 50,000 new stars, proving theories about dark matter formation.",
        ],
    }
]

# ============================================================
# PART 1: ROUGE SCORING
# ============================================================

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

print("ROUGE SCORING")
print("=" * 60)

for article_data in ARTICLES:
    ref = article_data["reference_summary"]
    for i, candidate in enumerate(article_data["candidate_summaries"], 1):
        scores = scorer.score(ref, candidate)
        print(f"\nCandidate {i}: '{candidate[:60]}...'")
        print(f"  ROUGE-1 F1: {scores['rouge1'].fmeasure:.3f}")
        print(f"  ROUGE-2 F1: {scores['rouge2'].fmeasure:.3f}")
        print(f"  ROUGE-L F1: {scores['rougeL'].fmeasure:.3f}")

# ============================================================
# PART 2: LLM-AS-JUDGE
# ============================================================

JUDGE_PROMPT = """Evaluate this article summary on three dimensions, each scored 1-5.

Dimensions:
- Faithfulness (1=contains false information, 5=fully accurate to source)
- Coverage (1=misses key information, 5=captures all important points)
- Conciseness (1=too long or short, 5=optimal length)

Article: {article}
Reference: {reference}
Candidate summary: {candidate}

Return JSON:
{{"faithfulness": int, "coverage": int, "conciseness": int, "overall": int,
  "reasoning": str}}"""

print("\n\nLLM JUDGE SCORING")
print("=" * 60)

judge_results = []

for article_data in ARTICLES:
    for i, candidate in enumerate(article_data["candidate_summaries"], 1):
        r = client.chat.completions.create(
            model="gpt-6-sol",
            reasoning_effort="none",
            messages=[
                {
                    "role": "user",
                    "content": JUDGE_PROMPT.format(
                        article=article_data["article"],
                        reference=article_data["reference_summary"],
                        candidate=candidate,
                    ),
                }
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        result = json.loads(r.choices[0].message.content)
        judge_results.append(result)
        print(f"\nCandidate {i}:")
        print(f"  Faithfulness: {result['faithfulness']}/5")
        print(f"  Coverage: {result['coverage']}/5")
        print(f"  Conciseness: {result['conciseness']}/5")
        print(f"  Overall: {result['overall']}/5")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')[:100]}...")

print("\n\nEvaluation complete.")
