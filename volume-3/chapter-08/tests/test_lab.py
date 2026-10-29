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
    ScriptedModel,
    calculate_cost,
    get_shipment_status,
    get_weather,
    run_conversation,
    search_database,
    validate_arguments,
)

SHIPMENT_PARAMETERS = next(
    t["function"]["parameters"]
    for t in TOOL_SCHEMAS
    if t["function"]["name"] == "get_shipment_status"
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
    def broken(city, units="celsius"):
        raise RuntimeError("weather service down")

    orchestrator = MockOrchestrator({**TOOL_REGISTRY, "get_weather": broken}, TOOL_SCHEMAS)
    out = orchestrator._execute_tool_call(MockToolCall("tc", "get_weather", {"city": "Paris"}))
    assert out == {"error": "weather service down"}


def test_wrong_argument_name_is_caught_before_the_tool_runs():
    out = run("get_weather", {"town": "Paris"})
    assert out == {"error": "Invalid arguments: missing required argument 'city'"}


def test_validation_checks_types_enums_patterns_and_extra_arguments():
    weather = TOOL_SCHEMAS[0]["function"]["parameters"]
    assert validate_arguments(weather, {"city": "Paris", "units": "kelvin"}) == [
        "'units' must be one of ['celsius', 'fahrenheit']"
    ]
    assert validate_arguments(weather, {"city": 7}) == ["'city' must be of type string"]
    assert validate_arguments(SHIPMENT_PARAMETERS, {"tracking_number": "WF-2291"}) == []
    assert validate_arguments(SHIPMENT_PARAMETERS, {"tracking_number": "the blue one"}) == [
        "'tracking_number' does not match the pattern ^WF-[0-9]{4}$"
    ]
    assert validate_arguments(SHIPMENT_PARAMETERS, {"tracking_number": "WF-2291", "x": 1}) == [
        "unexpected argument 'x'"
    ]


def test_a_postcode_never_reaches_the_shipment_tool():
    calls = []

    def recording(tracking_number):
        calls.append(tracking_number)
        return get_shipment_status(tracking_number)

    orchestrator = MockOrchestrator(
        {**TOOL_REGISTRY, "get_shipment_status": recording}, TOOL_SCHEMAS
    )
    call = MockToolCall("tc", "get_shipment_status", {"tracking_number": "SW1A 1AA"})
    assert orchestrator._execute_tool_call(call)["error"].startswith("Invalid arguments")
    assert calls == []


def test_the_loop_answers_from_the_tool_result(capsys):
    orchestrator = MockOrchestrator(TOOL_REGISTRY, TOOL_SCHEMAS)
    answer = run_conversation("Where is my parcel? It is WF-2291.", ScriptedModel(), orchestrator)
    assert answer == (
        "Your parcel WF-2291 is in transit, last scanned at the Leeds depot, expected Thursday."
    )


def test_the_loop_asks_for_a_tracking_number_when_given_a_postcode(capsys):
    orchestrator = MockOrchestrator(TOOL_REGISTRY, TOOL_SCHEMAS)
    answer = run_conversation(
        "Where is my parcel? I live at SW1A 1AA.", ScriptedModel(), orchestrator
    )
    assert "tracking number" in answer
    assert "does not match the pattern" in capsys.readouterr().out


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
