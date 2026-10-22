"""Tests for Lab 2. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest
import tiktoken

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import ContentBlock, ContextWindowManager  # noqa: E402

ENC = tiktoken.get_encoding("cl100k_base")


def block(name, n_words, priority, required=False):
    return ContentBlock(
        name=name, text=" ".join(["word"] * n_words), priority=priority, required=required
    )


def test_token_count_matches_the_tokenizer():
    text = "Revenue rose 12.4% to $5,480 in Q2."
    assert ContentBlock("doc", text, priority=3).token_count == len(ENC.encode(text))


def test_budget_from_fraction_and_unknown_model_fallback():
    assert ContextWindowManager(model="gpt-4", budget_fraction=0.5).token_budget == 4096
    assert ContextWindowManager(model="no-such-model", budget_fraction=1.0).token_budget == 8192


def test_explicit_budget_overrides_fraction():
    assert ContextWindowManager(model="gpt-6.1-sol", token_budget=200).token_budget == 200


def test_everything_fits_at_default_budget():
    m = ContextWindowManager()
    m.add(block("system_role", 20, 1, required=True))
    m.add(block("doc", 50, 3))
    m.add(block("user_message", 10, 1, required=True))
    assert m.build()["report"]["blocks_excluded"] == 0


def test_required_blocks_survive_a_tight_budget():
    m = ContextWindowManager(token_budget=40)
    m.add(block("system_role", 30, 1, required=True))
    m.add(block("doc", 20, 2))
    report = m.build()["report"]
    assert report["blocks_included"] == 1
    assert [e["name"] for e in report["excluded"]] == ["doc"]


def test_required_blocks_over_budget_raise():
    m = ContextWindowManager(token_budget=10)
    m.add(block("system_role", 30, 1, required=True))
    with pytest.raises(ValueError, match="Required blocks"):
        m.build()


def test_higher_priority_block_gets_the_budget_first():
    m = ContextWindowManager(token_budget=60)
    m.add(block("low", 40, 9))
    m.add(block("high", 40, 2))
    report = m.build()["report"]
    assert [e["name"] for e in report["excluded"]] == ["low"]


def test_fill_is_greedy_a_smaller_lower_priority_block_still_fits():
    m = ContextWindowManager(token_budget=100)
    m.add(block("doc_1", 50, 3))
    m.add(block("doc_2", 60, 4))
    m.add(block("history", 30, 5))
    report = m.build()["report"]
    assert [e["name"] for e in report["excluded"]] == ["doc_2"]
    assert report["tokens_used"] <= 100


def test_messages_put_context_in_system_and_question_in_user():
    m = ContextWindowManager()
    m.add(ContentBlock("user_message", "What is the policy rate?", 1, required=True))
    m.add(ContentBlock("compliance_rules", "No investment advice.", 2, required=True))
    messages = m.build()["messages"]
    assert [msg["role"] for msg in messages] == ["system", "user"]
    assert messages[0]["content"].startswith("## COMPLIANCE RULES")
    assert messages[1]["content"] == "What is the policy rate?"


def test_report_counts_are_consistent():
    m = ContextWindowManager(token_budget=200)
    m.add(block("a", 20, 1, required=True))
    m.add(block("b", 20, 2))
    report = m.build()["report"]
    assert report["tokens_used"] == sum(len(ENC.encode(" ".join(["word"] * 20))) for _ in "ab")
    assert report["utilization_pct"] == round(report["tokens_used"] / 200 * 100, 1)
