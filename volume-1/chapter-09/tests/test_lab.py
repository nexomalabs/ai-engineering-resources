"""Tests for Lab 9. Run against solution/ in CI, replaying recorded fixtures.
No API key, no network — see fixtures/chapter-09/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))
sys.path.insert(0, str(ROOT.parent / "shared"))

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")

from lab import (  # noqa: E402
    FIXTURES_DIR,
    MODEL_STANDARD,
    PROBLEMS,
    call_reasoning,
    call_standard,
    check_accuracy,
)
from nexoma_labs.client import LabClient  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return LabClient(FIXTURES_DIR, MODEL_STANDARD)


class TestCheckAccuracy:
    def test_exact_match(self):
        assert check_accuracy("The answer is 3:13 PM.", "3:13 PM")

    def test_case_insensitive(self):
        assert check_accuracy("the answer is 3:13 pm", "3:13 PM")

    def test_digits_only_match_counts(self):
        assert check_accuracy("I calculate 2/15 as the probability.", "2/15")

    def test_wrong_answer_rejected(self):
        assert not check_accuracy("The probability is 4/25.", "2/15")

    def test_latex_fraction_counts(self):
        assert check_accuracy(r"\(\frac{2}{15}\)", "2/15")
        assert check_accuracy(r"\boxed{\dfrac{2}{15}}", "2/15")

    def test_partial_digit_overlap_is_not_a_false_positive(self):
        """'2/15' must not match a response that only contains '15' alone."""
        assert not check_accuracy("There are 15 total balls in the bag.", "2/15")


class TestFixtureReplay:
    def test_all_three_problems_have_all_three_conditions(self, client):
        for prob in PROBLEMS:
            direct = call_standard(client, prob["problem"], chain_of_thought=False)
            cot = call_standard(client, prob["problem"], chain_of_thought=True)
            reasoning = call_reasoning(client, prob["problem"])
            assert direct.content and cot.content and reasoning["content"]

    def test_replay_is_repeatable(self, client):
        a = call_standard(client, PROBLEMS[0]["problem"], chain_of_thought=True).content
        b = call_standard(client, PROBLEMS[0]["problem"], chain_of_thought=True).content
        assert a == b

    def test_reasoning_call_reports_reasoning_tokens(self, client):
        r = call_reasoning(client, PROBLEMS[0]["problem"])
        assert r["reasoning_tokens"] and r["reasoning_tokens"] > 0

    def test_direct_and_cot_prompts_produce_different_fixtures(self, client):
        """A regression guard: if both conditions ever hashed to the same
        fixture key, this lab's central comparison would be meaningless."""
        direct = call_standard(client, PROBLEMS[0]["problem"], chain_of_thought=False)
        cot = call_standard(client, PROBLEMS[0]["problem"], chain_of_thought=True)
        assert direct.content != cot.content


class TestExperimentOutcome:
    """The lab's actual claims, checked against the bundled fixtures."""

    def test_direct_answer_misses_the_train_problem(self, client):
        """The lab's contrast depends on at least one direct failure: P1 needs
        a head-start step that an answer-only reply skips."""
        p1 = PROBLEMS[0]
        r = call_standard(client, p1["problem"], chain_of_thought=False)
        assert not check_accuracy(r.content, p1["answer"])

    def test_reasoning_model_gets_everything_right(self, client):
        for prob in PROBLEMS:
            r = call_reasoning(client, prob["problem"])
            assert check_accuracy(r["content"], prob["answer"]), (
                f"{prob['id']}: reasoning model unexpectedly wrong"
            )

    def test_chain_of_thought_beats_direct(self, client):
        def score(cot: bool) -> int:
            return sum(
                check_accuracy(
                    call_standard(client, p["problem"], chain_of_thought=cot).content,
                    p["answer"],
                )
                for p in PROBLEMS
            )

        assert score(cot=True) > score(cot=False)

    def test_reasoning_uses_more_tokens_than_direct(self, client):
        direct = call_standard(client, PROBLEMS[0]["problem"], chain_of_thought=False)
        reasoning = call_reasoning(client, PROBLEMS[0]["problem"])
        assert reasoning["total_tokens"] > direct.total_tokens * 2
