# compliance_runner.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class ControlStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class ControlSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ComplianceControl:
    """A single compliance control with automated evaluation logic."""

    control_id: str
    framework: str
    category: str
    title: str
    description: str
    severity: ControlSeverity
    evaluator: Optional[Callable[["AISystemProfile"], ControlStatus]] = field(
        default=None, repr=False
    )

    def evaluate(self, profile: "AISystemProfile") -> "ControlResult":
        if self.evaluator is None:
            status = ControlStatus.NOT_EVALUATED
        else:
            try:
                status = self.evaluator(profile)
            except Exception:
                status = ControlStatus.NOT_EVALUATED
        return ControlResult(
            control_id=self.control_id,
            title=self.title,
            framework=self.framework,
            category=self.category,
            severity=self.severity,
            status=status,
        )


@dataclass
class ControlResult:
    control_id: str
    title: str
    framework: str
    category: str
    severity: ControlSeverity
    status: ControlStatus
    evidence: str = ""
    remediation: str = ""


@dataclass
class AISystemProfile:
    """Describes the AI system under audit."""

    system_name: str
    system_version: str
    deployment_date: str

    # GOVERN dimension
    has_ai_policy: bool = False
    has_risk_register: bool = False
    has_designated_ai_officer: bool = False
    has_incident_response_plan: bool = False

    # MAP dimension
    has_system_card: bool = False
    has_model_card: bool = False
    has_impact_assessment: bool = False
    risk_tier: str = "unknown"  # minimal, limited, high, prohibited
    affected_groups_documented: bool = False

    # MEASURE dimension
    has_bias_evaluation: bool = False
    has_performance_benchmarks: bool = False
    has_adversarial_testing: bool = False
    bias_evaluation_date: Optional[str] = None

    # MANAGE dimension
    has_audit_logging: bool = False
    log_retention_days: int = 0
    has_human_oversight: bool = False
    has_rollback_procedure: bool = False
    has_monitoring_dashboard: bool = False
    has_alerting: bool = False

    # Data governance
    has_data_provenance_docs: bool = False
    pii_processing: bool = False
    has_data_processing_agreement: bool = False

    # Transparency: a chatbot's opening message; None if the system does not chat
    greeting: Optional[str] = None
