# streamnest_capstone_starter.py
"""
Volume II Capstone Lab — StreamNest Support AI
Complete the TODO sections using the patterns and frameworks from Chapters 1–18.
"""

import json
from dataclasses import dataclass
from typing import Callable

# ── TODO 1: Define your output schemas ────────────────────────────────────
# Define JSON schemas for:
# - Classifier output (category, confidence, extracted_ids, flags)
# - Response generator output (response_draft, tone, word_count)
# - Evaluator output (scores per dimension, weighted_total, pass, top_improvement)

CLASSIFIER_OUTPUT_SCHEMA = {
    # TODO: fill in required fields and their types
}

RESPONSE_OUTPUT_SCHEMA = {
    # TODO: fill in required fields and their types
}

EVALUATOR_OUTPUT_SCHEMA = {
    # TODO: fill in required fields and their types
}


# ── TODO 2: Write your three prompt templates ──────────────────────────────
# Follow the Template Pattern from Chapter 17.
# All templates must:
# - Declare a clear role
# - Specify the output format constraint
# - End with "BEGIN:" or "BEGIN OUTPUT:"

CLASSIFIER_TEMPLATE = """
# TODO: Write the StreamNest ticket classifier prompt
# Must classify into: subscription_billing | streaming_quality | content_questions | escalate_to_human
"""

RESPONSE_GENERATOR_TEMPLATE_A = """
# TODO: Write Variant A — basic response generator
"""

RESPONSE_GENERATOR_TEMPLATE_B = """
# TODO: Write Variant B — enhanced response generator with explicit brand voice guidelines
# This variant should outperform Variant A on brand voice dimension
"""

EVALUATOR_TEMPLATE = """
# TODO: Write the quality evaluator prompt
# Use a 3-4 dimension rubric appropriate for streaming service support
"""


# ── TODO 3: Implement your pipeline ───────────────────────────────────────


@dataclass
class StreamNestPipeline:
    classify_llm: Callable[[str], str]
    respond_llm: Callable[[str], str]
    evaluate_llm: Callable[[str], str]
    response_template: str = RESPONSE_GENERATOR_TEMPLATE_A
    quality_threshold: float = 0.78
    confidence_threshold: float = 0.85

    def classify(self, ticket_text: str) -> dict:
        # TODO: render CLASSIFIER_TEMPLATE and call classify_llm
        pass

    def generate_response(self, category: str, ticket_text: str) -> dict:
        # TODO: render response_template and call respond_llm
        pass

    def evaluate(self, ticket_text: str, response_draft: str) -> dict:
        # TODO: render EVALUATOR_TEMPLATE and call evaluate_llm
        # Must recompute weighted_total from raw scores
        pass

    def run(self, ticket_text: str) -> dict:
        # TODO: run classify → generate → evaluate pipeline
        # Handle low-confidence routing to human
        pass


# ── TODO 4: Build your test cases ─────────────────────────────────────────
# Define at least 9 test cases:
# - 3 standard cases (one per category)
# - 3 edge cases (short ticket, multi-category, ambiguous)
# - 3 adversarial cases

STREAMNEST_TEST_CASES = [
    # TODO: fill in test cases
    # {"id": "T001", "tier": "standard", "input": "...", "expected_category": "..."},
]


# ── TODO 5: Implement A/B comparison ──────────────────────────────────────


def run_ab_comparison(mock_llm: Callable, test_cases: list) -> dict:
    """
    Compare RESPONSE_GENERATOR_TEMPLATE_A vs RESPONSE_GENERATOR_TEMPLATE_B.
    Return metrics for both variants and identify the winner.
    """
    # TODO: Implement A/B test using the framework from Section 20.7
    pass


# ── TODO 6: Run your baseline ─────────────────────────────────────────────


def run_streamnest_baseline(pipeline: StreamNestPipeline, test_cases: list) -> dict:
    """Run all test cases and return baseline metrics."""
    # TODO: Run pipeline on each test case
    # Compute: classification_accuracy, avg_quality_score, escalation_rate
    pass


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # TODO: Implement a mock LLM that returns deterministic responses
    # appropriate for StreamNest test cases.
    def streamnest_mock_llm(prompt: str) -> str:
        # TODO: Return appropriate mock responses based on prompt content
        pass

    pipeline = StreamNestPipeline(
        classify_llm=streamnest_mock_llm,
        respond_llm=streamnest_mock_llm,
        evaluate_llm=streamnest_mock_llm,
    )

    print("StreamNest Support AI — Capstone Baseline")
    baseline_results = run_streamnest_baseline(pipeline, STREAMNEST_TEST_CASES)
    if baseline_results:
        print(json.dumps(baseline_results.get("metrics", {}), indent=2))

    print("\nA/B Test: Response Generator Variant Comparison")
    ab_results = run_ab_comparison(streamnest_mock_llm, STREAMNEST_TEST_CASES)
    if ab_results:
        print(json.dumps(ab_results, indent=2))
