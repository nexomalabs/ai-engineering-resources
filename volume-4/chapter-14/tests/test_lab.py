"""Tests for Lab 14. Run against solution/ in CI, with the mock judge."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

SOLUTION = Path(__file__).resolve().parent.parent / "solution"
sys.path.insert(0, str(SOLUTION))

import evaluation_runner as er  # noqa: E402
from llm_judge import EvaluationItem, EvaluationScore, build_judge_prompt  # noqa: E402


def score(**overrides):
    values = {
        "accuracy": 1.0,
        "helpfulness": 1.0,
        "safety": 1.0,
        "conciseness": 1.0,
        "justification": "x",
    }
    return EvaluationScore(**(values | overrides))


def test_overall_uses_the_weights():
    s = score(accuracy=0.0)
    assert s.overall() == pytest.approx(0.65)
    assert (
        s.overall({"accuracy": 1.0, "helpfulness": 0.0, "safety": 0.0, "conciseness": 0.0}) == 0.0
    )


def test_scores_outside_zero_to_one_are_rejected():
    with pytest.raises(ValidationError):
        score(safety=1.2)


def test_judge_prompt_includes_the_reference_only_when_there_is_one():
    item = EvaluationItem("i", "Q?", "A.", reference="Ref")
    assert "REFERENCE ANSWER:\nRef" in build_judge_prompt(item)
    assert "REFERENCE" not in build_judge_prompt(EvaluationItem("i", "Q?", "A."))


def test_mock_judge_is_deterministic():
    item = er.SAMPLE_ITEMS[0]
    assert er.mock_judge(item) == er.mock_judge(item)


def test_wrong_answer_and_refusal_are_flagged():
    report = er.EvaluationPipeline(er.mock_judge)
    report.add_items(
        [
            EvaluationItem(
                **{k: getattr(i, k) for k in ("item_id", "question", "response", "reference")}
            )
            for i in er.SAMPLE_ITEMS
        ]
    )
    result = report.run()
    low = {i.item_id for i in result.items if i.score.overall() < 0.60}
    assert low == {"q003", "q005"}
    assert result.aggregate()["safety"] == 0.98


def test_detect_regressions_reports_only_drops_beyond_tolerance():
    baseline = {"accuracy": 0.80, "helpfulness": 0.70, "safety": 0.98}
    candidate = {"accuracy": 0.70, "helpfulness": 0.68, "safety": 0.99}
    assert er.detect_regressions(baseline, candidate) == {"accuracy": 0.1}
    assert er.detect_regressions(baseline, baseline) == {}


def test_csv_items_load_with_optional_references(tmp_path):
    path = tmp_path / "qa.csv"
    path.write_text(
        "item_id,question,response,reference\na,Q1,R1,Ref\nb,Q2,R2,\n", encoding="utf-8"
    )
    items = er.load_items_from_csv(str(path))
    assert [(i.item_id, i.reference) for i in items] == [("a", "Ref"), ("b", None)]


def test_bundled_csv_finds_the_wrong_planet_and_the_refusal():
    pipeline = er.EvaluationPipeline(er.mock_judge)
    pipeline.add_items(er.load_items_from_csv(str(SOLUTION / "sample_qa.csv")))
    low = {i.item_id for i in pipeline.run().items if i.score.overall() < 0.60}
    assert low == {"c002", "c004"}


import quality_gate as qg  # noqa: E402


def scored_item(item_id, value, **slices):
    item = EvaluationItem(item_id, "Q?", "A.", slices=slices)
    item.score = score(accuracy=value, helpfulness=value, safety=value, conciseness=value)
    return item


def run(version):
    return qg.score_run(str(SOLUTION / f"refund_{version}.csv"), er.mock_judge)


def test_csv_columns_beyond_the_four_become_slices(tmp_path):
    path = tmp_path / "qa.csv"
    path.write_text(
        "item_id,language,tier,question,response,reference\na,pt,business,Q,R,\n",
        encoding="utf-8",
    )
    (item,) = er.load_items_from_csv(str(path))
    assert item.slices == {"language": "pt", "tier": "business"}


def test_a_slice_that_falls_too_far_blocks_a_change_that_raised_the_average():
    baseline = [scored_item("a", 0.6, language="en"), scored_item("b", 0.6, language="en")]
    candidate = [scored_item("a", 0.8, language="en"), scored_item("b", 0.8, language="en")]
    baseline.append(scored_item("c", 0.8, language="pt"))
    candidate.append(scored_item("c", 0.7, language="pt"))
    rows, blocked = qg.quality_gate(baseline, candidate, keys=("language",))
    assert rows[0][3] > rows[0][2]
    assert blocked == ["language=pt"]


def test_the_story_prompt_raises_the_average_and_is_blocked_on_portuguese_alone():
    rows, blocked = qg.quality_gate(run("v1"), run("v2"))
    _, _, old, new = rows[0]
    assert new > old
    assert blocked == ["language=pt"]


def test_the_fixed_prompt_passes_every_language_and_tier():
    rows, blocked = qg.quality_gate(run("v1"), run("v3"))
    names = [name for name, *_ in rows]
    assert names == [
        "all",
        "language=en",
        "language=es",
        "language=pt",
        "tier=business",
        "tier=personal",
    ]
    assert blocked == []
