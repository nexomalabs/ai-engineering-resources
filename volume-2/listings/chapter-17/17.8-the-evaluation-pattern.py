# Applied AI Engineering, Volume II, Chapter 17
# Section 17.8, The Evaluation Pattern
# Copied from the book by scripts/export_listings.py. Report errors as errata.

@dataclass
class RubricDimension:
    name: str
    description: str
    weight: float  # Sum of weights should equal 1.0
    scoring_guide: dict[int, str]  # Score -> description
    min_score: int = 1
    max_score: int = 5


@dataclass
class EvaluationFramework:
    framework_id: str
    version: str
    dimensions: list[RubricDimension]
    pass_threshold: float  # Weighted score threshold for pass/fail

    def render_evaluation_prompt(self, target_output: str, task_context: str) -> str:
        rubric_text = ""
        for dim in self.dimensions:
            guide_text = "\n".join(
                f"    {score}: {desc}"
                for score, desc in dim.scoring_guide.items()
            )
            rubric_text += (
                f"\n### {dim.name} (weight: {dim.weight:.0%})\n"
                f"{dim.description}\n"
                f"Scoring guide:\n{guide_text}\n"
            )
        return f"""\
You are a quality evaluation specialist. Assess the following output against the rubric below.

TASK CONTEXT:
{task_context}

TARGET OUTPUT:
{target_output}

EVALUATION RUBRIC:
{rubric_text}

For each dimension, provide:
1. A score (integer within the stated range)
2. A one-sentence justification citing specific evidence from the output

Respond ONLY with valid JSON in this exact format:
{{
  "scores": {{
    "<dimension_name>": {{
      "score": <int>,
      "justification": "<string>"
    }}
  }},
  "weighted_total": <float>,
  "pass": <bool>,
  "top_improvement": "<string>"
}}

BEGIN EVALUATION:"""

    def compute_weighted_score(self, scores: dict) -> tuple[float, bool]:
        total = sum(
            (scores[dim.name]["score"] / dim.max_score) * dim.weight
            for dim in self.dimensions
            if dim.name in scores
        )
        return total, total >= self.pass_threshold
