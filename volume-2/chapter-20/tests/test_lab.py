"""Tests for Lab 20 (capstone). Run against solution/ in CI. Standard library only."""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    CLASSIFIER_OUTPUT_SCHEMA,
    CLASSIFIER_TEMPLATE,
    RESPONSE_GENERATOR_TEMPLATE_A,
    RESPONSE_GENERATOR_TEMPLATE_B,
    STREAMNEST_TEST_CASES,
    StreamNestPipeline,
    render,
    run_ab_comparison,
    run_streamnest_baseline,
    streamnest_mock_llm,
    validate,
)


@pytest.fixture
def pipeline():
    return StreamNestPipeline(streamnest_mock_llm, streamnest_mock_llm, streamnest_mock_llm)


def case(case_id):
    return next(c for c in STREAMNEST_TEST_CASES if c["id"] == case_id)["input"]


def test_nine_cases_three_per_tier():
    assert Counter(c["tier"] for c in STREAMNEST_TEST_CASES) == {
        "standard": 3,
        "edge": 3,
        "adversarial": 3,
    }


def test_templates_end_with_begin_marker():
    for template in (
        CLASSIFIER_TEMPLATE,
        RESPONSE_GENERATOR_TEMPLATE_A,
        RESPONSE_GENERATOR_TEMPLATE_B,
    ):
        assert template.rstrip().endswith(("BEGIN:", "BEGIN OUTPUT:"))


def test_variants_are_meaningfully_different():
    assert "BRAND VOICE" in RESPONSE_GENERATOR_TEMPLATE_B
    assert "BRAND VOICE" not in RESPONSE_GENERATOR_TEMPLATE_A


def test_render_keeps_json_braces():
    prompt = render(CLASSIFIER_TEMPLATE, ticket="hello")
    assert "hello" in prompt and '{"category":' in prompt


def test_validate_reports_missing_and_mistyped_fields():
    problems = validate({"category": 3, "confidence": 1}, CLASSIFIER_OUTPUT_SCHEMA)
    assert "category should be str" in problems
    assert "missing field: flags" in problems
    assert not any("confidence" in p for p in problems)


@pytest.mark.parametrize(
    "case_id, category",
    [
        ("T001", "subscription_billing"),
        ("T002", "streaming_quality"),
        ("T003", "content_questions"),
    ],
)
def test_standard_cases_classified(pipeline, case_id, category):
    assert pipeline.classify(case(case_id))["category"] == category


def test_identifiers_extracted(pipeline):
    assert pipeline.classify(case("T001"))["extracted_ids"] == ["SN-44821"]


def test_prompt_injection_goes_to_a_human(pipeline):
    run = pipeline.run(case("T007"))
    assert run["route"] == "human"
    assert "prompt_injection" in run["classification"]["flags"]


def test_low_confidence_goes_to_a_human(pipeline):
    assert pipeline.run(case("T004"))["route"] == "human"


def test_evaluator_total_is_recomputed():
    def judge(prompt):
        scores = {"accuracy": 5, "resolution": 5, "brand_voice": 5, "safety": 5}
        return json.dumps(
            {"scores": scores, "weighted_total": 0.0, "pass": False, "top_improvement": "-"}
        )

    p = StreamNestPipeline(streamnest_mock_llm, streamnest_mock_llm, judge)
    result = p.evaluate("ticket", "reply")
    assert result["weighted_total"] == 1.0 and result["pass"] is True


def test_broken_output_contract_is_rejected():
    p = StreamNestPipeline(lambda _: "{}", streamnest_mock_llm, streamnest_mock_llm)
    with pytest.raises(ValueError):
        p.classify("anything")


def test_unknown_category_is_rejected():
    bad = json.dumps({"category": "weather", "confidence": 0.9, "extracted_ids": [], "flags": []})
    p = StreamNestPipeline(lambda _: bad, streamnest_mock_llm, streamnest_mock_llm)
    with pytest.raises(ValueError):
        p.classify("anything")


def test_baseline_metrics(pipeline):
    metrics = run_streamnest_baseline(pipeline, STREAMNEST_TEST_CASES)["metrics"]
    assert metrics["classification_accuracy"] == 1.0
    assert metrics["escalation_rate"] == pytest.approx(5 / 9, abs=0.001)


def test_ab_comparison_names_a_winner():
    result = run_ab_comparison(streamnest_mock_llm, STREAMNEST_TEST_CASES)
    assert result["winner"] == "B"
    assert result["variants"]["A"]["cases"] == result["variants"]["B"]["cases"] == 4
    assert "not statistically significant" in result["caveat"]
