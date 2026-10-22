"""Tests for Lab 8. Run against solution/ in CI."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    TOOL_REGISTRY,
    TOOL_SCHEMAS,
    MockLLMResponse,
    MockOrchestrator,
    MockToolCall,
    calculate_cost,
    get_weather,
    search_database,
)


def run(name, args):
    return MockOrchestrator(TOOL_REGISTRY, TOOL_SCHEMAS)._execute_tool_call(
        MockToolCall("tc_test", name, args)
    )


def test_every_registered_tool_has_a_schema():
    names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert names == set(TOOL_REGISTRY)


def test_weather_celsius_and_fahrenheit():
    assert get_weather("Paris")["temp"] == 18
    ny = get_weather("New York", units="fahrenheit")
    assert ny["temp"] == 68.0
    assert ny["units"] == "fahrenheit"


def test_unknown_city_is_an_error_not_an_exception():
    assert "error" in get_weather("Atlantis")


def test_search_matches_words_and_respects_limit():
    out = search_database("neural network transformer", limit=1)
    assert out["total_found"] == 2
    assert [r["id"] for r in out["results"]] == [1]


def test_search_with_no_match_returns_nothing():
    out = search_database("quantum chemistry")
    assert out["results"] == []
    assert out["total_found"] == 0


def test_cost_with_tax():
    out = calculate_cost([{"name": "A", "quantity": 5, "unit_price": 49.99}])
    assert out["line_items"][0]["total"] == 249.95
    assert out["tax_8pct"] == 20.0
    assert out["grand_total"] == 269.95


def test_unknown_tool_returns_an_error():
    assert run("delete_everything", {}) == {"error": "Unknown tool: delete_everything"}


def test_tool_exception_returns_an_error():
    out = run("get_weather", {"town": "Paris"})  # wrong argument name
    assert "error" in out
    assert "town" in out["error"]


def test_tool_call_carries_json_arguments():
    tc = MockToolCall("tc_1", "get_weather", {"city": "Tokyo"})
    assert tc.function.name == "get_weather"
    assert json.loads(tc.function.arguments) == {"city": "Tokyo"}


def test_mock_response_has_the_openai_shape():
    tc = MockToolCall("tc_1", "get_weather", {"city": "Tokyo"})
    choice = MockLLMResponse("tool_calls", tool_calls=[tc]).choices[0]
    assert choice.finish_reason == "tool_calls"
    assert choice.message.tool_calls == [tc]
    assert choice.message.content is None
