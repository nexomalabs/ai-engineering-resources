"""Tests for Lab 12. Run against solution/ in CI."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from audit_runner import AuditReport, ComplianceAuditRunner  # noqa: E402
from compliance_runner import (  # noqa: E402
    AISystemProfile,
    ComplianceControl,
    ControlResult,
    ControlSeverity,
    ControlStatus,
)
from nist_controls import build_nist_controls  # noqa: E402

DEMO = dict(
    has_ai_policy=True,
    has_risk_register=True,
    has_incident_response_plan=True,
    has_system_card=True,
    has_impact_assessment=True,
    risk_tier="limited",
    affected_groups_documented=True,
    has_bias_evaluation=True,
    has_performance_benchmarks=True,
    has_audit_logging=True,
    log_retention_days=90,
    has_human_oversight=True,
    has_rollback_procedure=True,
    has_monitoring_dashboard=True,
    has_alerting=True,
)
ALL_TRUE = {
    name: True for name, f in AISystemProfile.__dataclass_fields__.items() if f.type == "bool"
}


def profile(**flags):
    return AISystemProfile(
        system_name="Bot", system_version="1", deployment_date="2026-01-01", **flags
    )


def audit(**flags):
    return ComplianceAuditRunner(profile(**flags)).run()


def result(severity, status):
    return ControlResult("X", "x", "f", "c", severity, status)


def test_catalogue_covers_the_four_functions_with_unique_ids():
    controls = build_nist_controls()
    assert len({c.control_id for c in controls}) == len(controls) == 15
    assert {c.category for c in controls} == {"GOVERN", "MAP", "MEASURE", "MANAGE"}


def test_demo_profile_scores_74_percent():
    assert audit(**DEMO).compliance_score() == 74.0


def test_score_is_weighted_by_severity():
    report = AuditReport(
        "s",
        "1",
        "d",
        [
            result(ControlSeverity.CRITICAL, ControlStatus.COMPLIANT),
            result(ControlSeverity.LOW, ControlStatus.NON_COMPLIANT),
        ],
    )
    assert report.compliance_score() == 80.0


def test_partial_earns_half_and_counts_as_a_gap():
    report = AuditReport("s", "1", "d", [result(ControlSeverity.HIGH, ControlStatus.PARTIAL)])
    assert report.compliance_score() == 50.0
    assert len(report.gap_results()) == 1


def test_demo_gaps():
    gaps = audit(**DEMO).gap_results()
    assert [g.control_id for g in gaps] == ["GV-1.3", "MP-2.1", "MS-3.3", "MG-4.1", "MG-4.5"]


def test_fully_compliant_profile_scores_100_with_no_gaps():
    report = audit(**ALL_TRUE, log_retention_days=365)
    assert report.compliance_score() == 100.0
    assert report.gap_results() == []


def test_log_retention_below_180_days_is_partial():
    statuses = {
        r.control_id: r.status
        for r in audit(has_audit_logging=True, log_retention_days=179).results
    }
    assert statuses["MG-4.1"] == ControlStatus.PARTIAL


def test_failing_evaluator_is_not_evaluated():
    def broken(p):
        raise RuntimeError("missing evidence")

    ctrl = ComplianceControl("T-1", "f", "GOVERN", "t", "d", ControlSeverity.LOW, broken)
    assert ctrl.evaluate(profile()).status == ControlStatus.NOT_EVALUATED


def test_json_export_round_trips():
    report = audit(**DEMO)
    data = json.loads(report.to_json())
    assert data["compliance_score"] == 74.0
    assert len(data["results"]) == 15
    assert data["results"][0] == {
        "control_id": "GV-1.1",
        "title": "AI Risk Management Policy",
        "framework": "NIST AI RMF",
        "category": "GOVERN",
        "severity": "CRITICAL",
        "status": "COMPLIANT",
    }


import transparency  # noqa: E402
from compliance_runner import AISystemProfile  # noqa: E402


def greeting_status(greeting):
    profile = AISystemProfile("Wren", "4.2.0", "2026-12-01", greeting=greeting)
    return transparency.CHATBOT_DISCLOSURE.evaluate(profile).status.value


def test_the_story_greeting_does_not_disclose_the_ai():
    assert greeting_status("Hi, I'm Wren!") == "NON_COMPLIANT"


def test_disclosing_the_ai_without_a_route_to_a_person_is_partial():
    assert greeting_status(transparency.GREETINGS["a first fix"]) == "PARTIAL"


def test_the_new_greeting_is_compliant():
    assert greeting_status(transparency.GREETINGS["after the mapping"]) == "COMPLIANT"


def test_a_system_that_does_not_chat_is_not_applicable():
    profile = AISystemProfile("Customs pipeline", "1.3.0", "2026-12-01")
    assert transparency.CHATBOT_DISCLOSURE.evaluate(profile).status.value == "NOT_APPLICABLE"


def test_words_that_merely_contain_ai_are_not_a_disclosure():
    assert greeting_status("Hi, I'm Wren. Ask me about mail and email.") == "NON_COMPLIANT"
