"""Tests for Lab 1. Run against solution/ in CI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from context_pipeline import (  # noqa: E402
    ContextBlock,
    ContextPipeline,
    build_customer_support_context,
)

QUERY = "Is there a way to check how many API calls I've used today?"


def block(name, layer, priority=1, content="some words here"):
    return ContextBlock(name=name, content=content, priority=priority, layer=layer)


def test_block_counts_its_own_tokens():
    assert block("a", "system").token_count > 0
    assert block("e", "system", content="").token_count == 0


def test_blocks_sort_by_layer_then_priority():
    pipeline = ContextPipeline()
    for b in (
        block("req", "request"),
        block("kb2", "knowledge", priority=2),
        block("sys", "system"),
        block("kb1", "knowledge", priority=1),
        block("odd", "unknown-layer"),
    ):
        pipeline.add_block(b)
    assert [b.name for b in pipeline._sort_blocks()] == ["sys", "kb1", "kb2", "req", "odd"]


def test_full_budget_assembles_six_messages_in_layer_order():
    result = build_customer_support_context(QUERY)
    roles = [m["role"] for m in result["messages"]]
    assert roles == ["system"] * 5 + ["user"]
    assert result["messages"][1]["content"].startswith("[KB_API_LIMITS]")
    assert result["messages"][-1]["content"] == QUERY
    assert result["report"]["blocks_included"] == 7
    assert result["report"]["excluded_blocks"] == []


def test_small_budget_excludes_lower_layers_first():
    report = build_customer_support_context(QUERY, token_budget=800)["report"]
    assert report["excluded_blocks"] == ["user_profile", "conversation_history"]
    assert report["tokens_used"] <= 800 - 512


def test_mandatory_layers_survive_any_budget():
    result = build_customer_support_context(QUERY, token_budget=1)
    contents = [m["content"] for m in result["messages"]]
    assert contents[0].startswith("You are a senior customer support specialist")
    assert contents[-1] == QUERY
    assert len(result["report"]["excluded_blocks"]) == 4


def test_report_accounts_for_every_block():
    report = build_customer_support_context(QUERY, token_budget=800)["report"]
    assert report["blocks_included"] + report["blocks_excluded"] == 7
    assert report["tokens_available"] == report["token_budget"] - report["tokens_used"]
