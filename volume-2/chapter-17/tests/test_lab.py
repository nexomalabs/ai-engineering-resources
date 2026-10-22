"""Tests for Lab 17. Run against solution/ in CI."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    ErrorRecoveryFramework,
    FrameworkLibrary,
    QualityGateFramework,
    TaskDispatcherFramework,
    run_workflow,
)

BILLING = "I was charged $847 for shipment SH-20241103 but I have a contract rate of $620."
TRACKING = "Where is my package TRK-98732? It was due yesterday and the portal shows no updates."
AMBIGUOUS = "There's an issue with my account and I need it fixed."


@pytest.fixture
def library():
    lib = FrameworkLibrary()
    lib.register(TaskDispatcherFramework(), owner="ops", tags=["classification"])
    lib.register(QualityGateFramework(), owner="qa", tags=["evaluation"])
    lib.register(ErrorRecoveryFramework(), owner="ops", tags=["recovery"])
    return lib


def fake_judge(a, c, k):
    def llm(prompt):
        return json.dumps(
            {
                "scores": {
                    "accuracy": {"score": a, "justification": "-"},
                    "clarity": {"score": c, "justification": "-"},
                    "completeness": {"score": k, "justification": "-"},
                },
                "weighted_total": 0.123,
                "pass": False,
                "top_improvement": "-",
            }
        )

    return llm


def test_dispatcher_renders_the_request():
    assert "TRK-98732" in TaskDispatcherFramework().render(TRACKING)


@pytest.mark.parametrize(
    "text, category",
    [
        (BILLING, "billing_dispute"),
        (TRACKING, "shipment_tracking"),
        (AMBIGUOUS, "general_inquiry"),
    ],
)
def test_dispatcher_classifies_each_case(text, category):
    assert TaskDispatcherFramework().execute(text)["category"] == category


def test_ambiguous_input_has_low_confidence():
    assert TaskDispatcherFramework().execute(AMBIGUOUS)["confidence"] < 0.70


def test_quality_gate_recomputes_the_total():
    result = QualityGateFramework().execute("ctx", "resp", llm_fn=fake_judge(5, 5, 5))
    assert result["weighted_total"] == 1.0
    assert result["pass"] is True


def test_quality_gate_fails_below_threshold():
    result = QualityGateFramework().execute("ctx", "resp", llm_fn=fake_judge(2, 3, 3))
    assert result["weighted_total"] == pytest.approx(0.52)
    assert result["pass"] is False


def test_library_returns_newest_version_numerically(library):
    old = TaskDispatcherFramework()
    old.version = "1.9.0"
    new = TaskDispatcherFramework()
    new.version = "1.10.0"
    library.register(old, owner="ops")
    library.register(new, owner="ops")
    assert library.get("task-dispatcher").version == "1.10.0"


def test_unknown_framework_raises(library):
    with pytest.raises(KeyError):
        library.get("does-not-exist")


def test_billing_case_passes_the_gate(library):
    assert run_workflow(library, BILLING, "A credit of $227 will be applied.")["status"] == "pass"


def test_ambiguous_case_goes_to_recovery(library):
    result = run_workflow(library, AMBIGUOUS, "Please contact support.")
    assert result["status"] == "recovery"
    assert result["recovery"]["clarifying_questions"]
