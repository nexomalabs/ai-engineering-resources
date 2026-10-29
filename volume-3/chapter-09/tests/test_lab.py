"""Tests for Lab 9. Run against solution/ in CI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402
from lab import (  # noqa: E402
    REGISTRY,
    TOOLS,
    generate_credit_report,
    get_customer,
    get_order_history,
    simulate_multi_step_pipeline,
)


def test_every_function_has_a_schema():
    assert {t["function"]["name"] for t in TOOLS} == set(REGISTRY)


def test_get_customer_found_and_missing():
    assert get_customer("C002")["tier"] == "standard"
    assert "error" in get_customer("C999")


def test_order_history_totals():
    out = get_order_history("C003")
    assert out["total_orders"] == 1
    assert out["total_value"] == 8900.0


def test_empty_history_has_the_same_shape():
    out = get_order_history("C404")
    assert out["orders"] == []
    assert out["total_value"] == 0.0


def test_report_for_a_standard_customer():
    out = generate_credit_report("C002", "standard", 10000.0, 2300.0)
    assert out["utilization_pct"] == 23.0
    assert out["risk_score"] == 77.0
    assert out["recommendation"] == "Approve"


def test_tier_weighting_lowers_the_score_for_larger_accounts():
    standard = generate_credit_report("X", "standard", 10000.0, 3000.0)["risk_score"]
    enterprise = generate_credit_report("X", "enterprise", 10000.0, 3000.0)["risk_score"]
    assert enterprise < standard


def test_score_is_clamped():
    out = generate_credit_report("X", "enterprise", 1000.0, 5000.0)
    assert out["risk_score"] == 0
    assert out["recommendation"] == "Decline"


def test_zero_credit_limit_does_not_divide_by_zero():
    assert generate_credit_report("X", "standard", 0.0, 100.0)["utilization_pct"] == 0


def test_pipeline_passes_step_results_forward(monkeypatch, capsys):
    seen = {}
    real = lab.generate_credit_report

    def spy(**kwargs):
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(lab, "generate_credit_report", spy)
    simulate_multi_step_pipeline("C003")
    assert seen == {
        "customer_id": "C003",
        "customer_tier": "premium",
        "credit_limit": 25000.0,
        "total_order_value": 8900.0,
    }
    assert "Decision:     Review" in capsys.readouterr().out


def test_pipeline_stops_after_a_failed_lookup(capsys):
    simulate_multi_step_pipeline("C999")
    out = capsys.readouterr().out
    assert "Aborting" in out
    assert "[Step 2]" not in out


def test_the_claim_schema_meets_strict_mode_requirements():
    fn = lab.CLAIM_TOOL["function"]
    params = fn["parameters"]
    assert fn["strict"] is True
    assert params["additionalProperties"] is False
    assert set(params["required"]) == set(params["properties"])


def test_a_valid_claim_is_imported():
    result = lab.intake_claim("E1", lab.MODEL_ARGUMENTS["E1"])
    assert result["status"] == "imported"
    assert result["claim"]["declared_value"] == 189.0


def test_the_story_claim_is_sent_to_a_person_not_imported():
    result = lab.intake_claim("E2", lab.MODEL_ARGUMENTS["E2"])
    assert result["status"] == "sent to a person"
    assert result["problems"] == [
        "declared_value: Input should be a valid number, unable to parse string as a number"
    ]


def test_strictly_typed_but_wrong_data_is_caught_too():
    result = lab.intake_claim("E3", lab.MODEL_ARGUMENTS["E3"])
    assert result["status"] == "sent to a person"
    assert [p.split(":")[0] for p in result["problems"]] == ["tracking_number", "declared_value"]
