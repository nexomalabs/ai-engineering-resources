"""Lab 12 — Compliance Audit Checklist Runner (starter).

This file RUNS as supplied. The score treats every control as equally important, the gap
report leaves out partially met controls, and (in compliance_runner.py) an evaluator that
raises crashes the audit. Complete the three TODOs. Run from the lab folder:

    python src/audit_runner.py
"""

import datetime
import json

from compliance_runner import AISystemProfile, ControlResult, ControlSeverity, ControlStatus
from nist_controls import build_nist_controls
from tabulate import tabulate

SEVERITY_WEIGHT = {
    ControlSeverity.CRITICAL: 4,
    ControlSeverity.HIGH: 3,
    ControlSeverity.MEDIUM: 2,
    ControlSeverity.LOW: 1,
}

STATUS_SCORE = {
    ControlStatus.COMPLIANT: 1.0,
    ControlStatus.PARTIAL: 0.5,
    ControlStatus.NOT_APPLICABLE: 1.0,
    ControlStatus.NON_COMPLIANT: 0.0,
    ControlStatus.NOT_EVALUATED: 0.0,
}


class ComplianceAuditRunner:
    def __init__(self, profile: AISystemProfile):
        self.profile = profile
        self.controls = build_nist_controls()

    def run(self) -> "AuditReport":
        results = [ctrl.evaluate(self.profile) for ctrl in self.controls]
        return AuditReport(
            system_name=self.profile.system_name,
            system_version=self.profile.system_version,
            audit_date=datetime.date.today().isoformat(),
            results=results,
        )


class AuditReport:
    def __init__(
        self,
        system_name: str,
        system_version: str,
        audit_date: str,
        results: list[ControlResult],
    ):
        self.system_name = system_name
        self.system_version = system_version
        self.audit_date = audit_date
        self.results = results

    def compliance_score(self) -> float:
        # TODO 1: Weight each control by SEVERITY_WEIGHT[r.severity], so the score is
        #   earned weight / total weight x 100, rounded to one decimal place.
        earned = sum(STATUS_SCORE[r.status] for r in self.results)
        return round(earned / len(self.results) * 100, 1) if self.results else 0.0

    def gap_results(self) -> list[ControlResult]:
        return [
            r
            for r in self.results
            # TODO 2: A PARTIAL control is also a gap that needs remediation.
            if r.status == ControlStatus.NON_COMPLIANT
        ]

    def print_report(self):
        print(f"\n{'=' * 60}")
        print("  COMPLIANCE AUDIT REPORT")
        print(f"  System:  {self.system_name} v{self.system_version}")
        print(f"  Date:    {self.audit_date}")
        print(f"  Score:   {self.compliance_score()}%")
        print(f"{'=' * 60}\n")

        # Results table
        table_data = [
            [
                r.control_id,
                r.category,
                r.title[:40],
                r.severity.value,
                r.status.value,
            ]
            for r in self.results
        ]
        print(
            tabulate(
                table_data,
                headers=["Control ID", "Category", "Title", "Severity", "Status"],
                tablefmt="simple",
            )
        )

        # Gap report
        gaps = self.gap_results()
        if gaps:
            print(f"\n{'=' * 60}")
            print(f"  GAP REPORT — {len(gaps)} controls require attention")
            print(f"{'=' * 60}\n")
            for g in gaps:
                print(f"  [{g.severity.value}] {g.control_id}: {g.title}")
                print(f"  Status: {g.status.value}")
                print()
        else:
            print("\n  All controls COMPLIANT or NOT_APPLICABLE.\n")

    def to_json(self) -> str:
        return json.dumps(
            {
                "system_name": self.system_name,
                "system_version": self.system_version,
                "audit_date": self.audit_date,
                "compliance_score": self.compliance_score(),
                "results": [
                    {
                        "control_id": r.control_id,
                        "title": r.title,
                        "framework": r.framework,
                        "category": r.category,
                        "severity": r.severity.value,
                        "status": r.status.value,
                    }
                    for r in self.results
                ],
            },
            indent=2,
        )


# --- Run audit ---
if __name__ == "__main__":
    # Example profile: partially compliant system
    profile = AISystemProfile(
        system_name="CustomerSupportBot",
        system_version="2.1.0",
        deployment_date="2026-01-15",
        # GOVERN
        has_ai_policy=True,
        has_risk_register=True,
        has_designated_ai_officer=False,
        has_incident_response_plan=True,
        # MAP
        has_system_card=True,
        has_model_card=False,
        has_impact_assessment=True,
        risk_tier="limited",
        affected_groups_documented=True,
        # MEASURE
        has_bias_evaluation=True,
        has_performance_benchmarks=True,
        has_adversarial_testing=False,
        # MANAGE
        has_audit_logging=True,
        log_retention_days=90,  # Under 180-day threshold
        has_human_oversight=True,
        has_rollback_procedure=True,
        has_monitoring_dashboard=True,
        has_alerting=True,
        has_data_provenance_docs=False,
    )

    runner = ComplianceAuditRunner(profile)
    report = runner.run()
    report.print_report()

    # Save JSON report
    with open("compliance_report.json", "w") as f:
        f.write(report.to_json())
    print("Report saved to compliance_report.json")
