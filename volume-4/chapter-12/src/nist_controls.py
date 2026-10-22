# nist_controls.py — controls grouped by NIST AI RMF function
from compliance_runner import ComplianceControl, ControlSeverity, ControlStatus


def build_nist_controls() -> list[ComplianceControl]:
    controls = [
        # GOVERN
        ComplianceControl(
            control_id="GV-1.1",
            framework="NIST AI RMF",
            category="GOVERN",
            title="AI Risk Management Policy",
            description="Organization has documented AI risk management policy.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_ai_policy else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="GV-1.2",
            framework="NIST AI RMF",
            category="GOVERN",
            title="AI Risk Register",
            description="AI risks are tracked in a formal risk register.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_risk_register else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="GV-1.3",
            framework="NIST AI RMF",
            category="GOVERN",
            title="Designated AI Accountability",
            description="A named individual or role is accountable for AI governance.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.has_designated_ai_officer
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="GV-1.4",
            framework="NIST AI RMF",
            category="GOVERN",
            title="AI Incident Response Plan",
            description="A documented plan exists for AI-related incidents.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.has_incident_response_plan
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        # MAP
        ComplianceControl(
            control_id="MP-2.1",
            framework="NIST AI RMF",
            category="MAP",
            title="System Documentation",
            description="System card and model card are documented and current.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if (p.has_system_card and p.has_model_card)
                else ControlStatus.PARTIAL
                if (p.has_system_card or p.has_model_card)
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MP-2.2",
            framework="NIST AI RMF",
            category="MAP",
            title="AI Impact Assessment",
            description="Documented assessment of potential harms to affected groups.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_impact_assessment else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MP-2.3",
            framework="NIST AI RMF",
            category="MAP",
            title="Affected Groups Documented",
            description="Groups affected by AI decisions are identified.",
            severity=ControlSeverity.MEDIUM,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.affected_groups_documented
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        # MEASURE
        ComplianceControl(
            control_id="MS-3.1",
            framework="NIST AI RMF",
            category="MEASURE",
            title="Bias Evaluation",
            description="System has been evaluated for bias across relevant demographic groups.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_bias_evaluation else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MS-3.2",
            framework="NIST AI RMF",
            category="MEASURE",
            title="Performance Benchmarks",
            description="Performance benchmarks are documented and current.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.has_performance_benchmarks
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MS-3.3",
            framework="NIST AI RMF",
            category="MEASURE",
            title="Adversarial Testing",
            description="System has been tested for adversarial inputs and prompt injection.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.has_adversarial_testing
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        # MANAGE
        ComplianceControl(
            control_id="MG-4.1",
            framework="NIST AI RMF",
            category="MANAGE",
            title="Audit Logging",
            description="Comprehensive audit logging is enabled with adequate retention.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if (p.has_audit_logging and p.log_retention_days >= 180)
                else ControlStatus.PARTIAL
                if p.has_audit_logging
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MG-4.2",
            framework="NIST AI RMF",
            category="MANAGE",
            title="Human Oversight",
            description="Humans can review, override, and correct AI decisions.",
            severity=ControlSeverity.CRITICAL,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_human_oversight else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MG-4.3",
            framework="NIST AI RMF",
            category="MANAGE",
            title="Rollback Procedure",
            description="Documented procedure to rollback AI system to previous version.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT if p.has_rollback_procedure else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MG-4.4",
            framework="NIST AI RMF",
            category="MANAGE",
            title="Monitoring and Alerting",
            description="Real-time monitoring with automated alerts for anomalies.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if (p.has_monitoring_dashboard and p.has_alerting)
                else ControlStatus.PARTIAL
                if (p.has_monitoring_dashboard or p.has_alerting)
                else ControlStatus.NON_COMPLIANT
            ),
        ),
        ComplianceControl(
            control_id="MG-4.5",
            framework="NIST AI RMF",
            category="MANAGE",
            title="Data Provenance",
            description="Training and inference data provenance is documented.",
            severity=ControlSeverity.HIGH,
            evaluator=lambda p: (
                ControlStatus.COMPLIANT
                if p.has_data_provenance_docs
                else ControlStatus.NON_COMPLIANT
            ),
        ),
    ]
    return controls
