"""Lab 17 — Build a Three-Pattern Prompt Framework (starter).

This file RUNS as supplied. The quality gate trusts the model's own arithmetic, and a
low-confidence classification is never sent to error recovery. Complete the two TODOs.

    python src/lab.py
"""

# framework_lab.py

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from jinja2 import BaseLoader, Environment

# ── Utility ──────────────────────────────────────────────────────────────


def mock_llm(prompt: str) -> str:
    """
    Mock LLM that returns deterministic test responses. It reads the request
    text, so each test case takes a different path through the workflow.
    Replace with real OpenAI/Anthropic call in production.
    """
    text = prompt.lower()
    if "begin classification" in text:
        request = text.split("input request:")[1].split("respond only")[0]
        if "charged" in request or "invoice" in request:
            return json.dumps(
                {
                    "category": "billing_dispute",
                    "priority": "high",
                    "confidence": 0.91,
                    "routing_queue": "billing_team",
                    "flags": [],
                }
            )
        if "package" in request or "delivery" in request:
            return json.dumps(
                {
                    "category": "shipment_tracking",
                    "priority": "high",
                    "confidence": 0.88,
                    "routing_queue": "logistics_team",
                    "flags": ["sla_breach"],
                }
            )
        return json.dumps(
            {
                "category": "general_inquiry",
                "priority": "low",
                "confidence": 0.42,
                "routing_queue": "general_queue",
                "flags": ["ambiguous_request"],
            }
        )
    if "evaluate" in text or "assess" in text:
        if "shipment_tracking" in text:
            return json.dumps(
                {
                    "scores": {
                        "accuracy": {
                            "score": 5,
                            "justification": "Gives the current location and a delivery estimate.",
                        },
                        "clarity": {"score": 5, "justification": "Short and specific."},
                        "completeness": {
                            "score": 2,
                            "justification": "Does not say what happens if today's delivery is missed.",
                        },
                    },
                    "weighted_total": 0.82,
                    "pass": True,
                    "top_improvement": "State the next step if the package does not arrive today.",
                }
            )
        return json.dumps(
            {
                "scores": {
                    "accuracy": {
                        "score": 4,
                        "justification": "Response addresses the billing discrepancy correctly.",
                    },
                    "clarity": {
                        "score": 5,
                        "justification": "Clear and concise language used throughout.",
                    },
                    "completeness": {
                        "score": 3,
                        "justification": "Missing information about refund timeline.",
                    },
                },
                "weighted_total": 0.80,
                "pass": True,
                "top_improvement": "Include expected refund processing time in the response.",
            }
        )
    return json.dumps(
        {
            "recovery_action": "request_clarification",
            "clarifying_questions": [
                "Which part of your account is affected: billing, deliveries, or sign-in?",
                "What happened, and when did you first notice it?",
            ],
            "confidence_after_clarification": 0.85,
        }
    )


# ── Task Dispatcher Framework (Template Pattern) ──────────────────────────


@dataclass
class TaskDispatcherFramework:
    name: str = "task-dispatcher"
    version: str = "1.0.0"
    _env: Environment = field(default_factory=lambda: Environment(loader=BaseLoader()))

    TEMPLATE = """\
You are a logistics support operations specialist responsible for classifying
and routing incoming customer requests to the correct team.

CLASSIFICATION RULES:
- billing_dispute: Payment, invoice, or charge-related issues
- shipment_tracking: Location, delivery status, or delay inquiries
- damage_claim: Damaged goods reports, insurance requests
- account_management: Account setup, credentials, preferences
- general_inquiry: Everything else

ROUTING PRIORITY:
- high: Financial impact > $500 or SLA breach
- medium: Standard operational issues
- low: Informational requests

INPUT REQUEST:
{{ input_text }}

Respond ONLY with valid JSON:
{
  "category": "<string>",
  "priority": "high|medium|low",
  "confidence": <0.0-1.0>,
  "routing_queue": "<string>",
  "flags": ["<string>"]
}

BEGIN CLASSIFICATION:"""

    def render(self, input_text: str) -> str:
        tmpl = self._env.from_string(self.TEMPLATE)
        return tmpl.render(input_text=input_text)

    def execute(self, input_text: str, llm_fn: Callable = mock_llm) -> dict:
        prompt = self.render(input_text)
        raw = llm_fn(prompt)
        return json.loads(raw)


# ── Quality Gate Framework (Evaluation Pattern) ──────────────────────────


@dataclass
class QualityGateFramework:
    name: str = "quality-gate"
    version: str = "1.0.0"
    pass_threshold: float = 0.75
    _env: Environment = field(default_factory=lambda: Environment(loader=BaseLoader()))

    TEMPLATE = """\
You are a response quality evaluator for a logistics customer support system.

TASK CONTEXT:
{{ task_context }}

GENERATED RESPONSE TO EVALUATE:
{{ target_response }}

EVALUATE ON THREE DIMENSIONS (score each 1–5):

1. ACCURACY (weight 40%): Is the response factually correct and does it address the actual issue?
   5=Fully accurate  4=Minor omissions  3=Partially correct  2=Significant errors  1=Incorrect

2. CLARITY (weight 30%): Is the response clearly written and easy for the customer to understand?
   5=Exceptionally clear  4=Clear  3=Adequate  2=Confusing in places  1=Unclear

3. COMPLETENESS (weight 30%): Does the response cover all aspects of the customer's issue?
   5=Comprehensive  4=Mostly complete  3=Partially complete  2=Incomplete  1=Barely addresses the issue

Respond ONLY with valid JSON matching this exact structure:
{
  "scores": {
    "accuracy": {"score": <int>, "justification": "<string>"},
    "clarity": {"score": <int>, "justification": "<string>"},
    "completeness": {"score": <int>, "justification": "<string>"}
  },
  "weighted_total": <float>,
  "pass": <bool>,
  "top_improvement": "<string>"
}

BEGIN EVALUATION:"""

    def render(self, task_context: str, target_response: str) -> str:
        tmpl = self._env.from_string(self.TEMPLATE)
        return tmpl.render(task_context=task_context, target_response=target_response)

    def execute(self, task_context: str, target_response: str, llm_fn: Callable = mock_llm) -> dict:
        prompt = self.render(task_context, target_response)
        raw = llm_fn(prompt)
        result = json.loads(raw)
        # TODO 1: Do not trust the model's arithmetic. Recompute "weighted_total"
        # from the three scores (each out of 5; weights accuracy 0.40, clarity 0.30,
        # completeness 0.30), round it to 3 places, and set "pass" by comparing it
        # with self.pass_threshold. Until then the model's own numbers are used.
        return result


# ── Error Recovery Framework (Role Pattern) ──────────────────────────────


@dataclass
class ErrorRecoveryFramework:
    name: str = "error-recovery"
    version: str = "1.0.0"
    _env: Environment = field(default_factory=lambda: Environment(loader=BaseLoader()))

    TEMPLATE = """\
You are a logistics support resolution specialist trained in ambiguity handling
and customer communication recovery.

RECOVERY PROTOCOL:
- When a request cannot be classified with confidence >= 0.70, initiate clarification.
- When critical information is missing, formulate targeted clarifying questions.
- Never guess at unstated financial figures or shipment details.
- Maximum 3 clarifying questions per interaction.

AMBIGUOUS OR FAILED INPUT:
{{ failed_input }}

FAILURE REASON:
{{ failure_reason }}

Determine the recovery action and respond ONLY with valid JSON:
{
  "recovery_action": "request_clarification|escalate_to_human|acknowledge_and_wait",
  "clarifying_questions": ["<string>"],
  "confidence_after_clarification": <0.0-1.0>
}

BEGIN RECOVERY:"""

    def render(self, failed_input: str, failure_reason: str) -> str:
        tmpl = self._env.from_string(self.TEMPLATE)
        return tmpl.render(failed_input=failed_input, failure_reason=failure_reason)

    def execute(self, failed_input: str, failure_reason: str, llm_fn: Callable = mock_llm) -> dict:
        prompt = self.render(failed_input, failure_reason)
        raw = llm_fn(prompt)
        return json.loads(raw)


# ── Framework Library ─────────────────────────────────────────────────────


class FrameworkLibrary:
    def __init__(self):
        self._registry = {}

    def register(self, fw, owner: str, tags: list[str] = None):
        key = f"{fw.name}@{fw.version}"
        self._registry[key] = {
            "framework": fw,
            "owner": owner,
            "tags": tags or [],
            "usage_count": 0,
        }
        print(f"[Library] Registered: {key}")
        return key

    def get(self, name: str) -> Any:
        candidates = [(k, v) for k, v in self._registry.items() if k.startswith(f"{name}@")]
        if not candidates:
            raise KeyError(f"Framework '{name}' not found.")
        # Compare versions numerically, so 1.10.0 is newer than 1.9.0.
        key, entry = max(
            candidates, key=lambda kv: tuple(int(part) for part in kv[0].split("@")[1].split("."))
        )
        entry["usage_count"] += 1
        return entry["framework"]


# ── Workflow Demonstration ────────────────────────────────────────────────


def run_workflow(library: FrameworkLibrary, customer_input: str, draft_response: str) -> dict:
    """
    Full three-stage framework workflow:
    1. Classify the input (Task Dispatcher)
    2. Evaluate the draft response (Quality Gate)
    3. Recover if classification confidence is low (Error Recovery)
    """
    dispatcher: TaskDispatcherFramework = library.get("task-dispatcher")
    gate: QualityGateFramework = library.get("quality-gate")
    recovery: ErrorRecoveryFramework = library.get("error-recovery")

    # Stage 1: Classify
    classification = dispatcher.execute(customer_input)
    print(f"\n[Stage 1 – Dispatch]\n{json.dumps(classification, indent=2)}")

    # TODO 2: If classification["confidence"] is below 0.70, call recovery.execute()
    # with the input and the reason, print the result under "[Stage 3 – Recovery
    # Triggered]", and return {"status": "recovery", "recovery": <result>} instead of
    # sending a low-confidence classification on to the quality gate.
    _ = recovery

    # Stage 2: Evaluate draft response
    task_context = (
        f"Customer category: {classification['category']}, priority: {classification['priority']}"
    )
    evaluation = gate.execute(task_context=task_context, target_response=draft_response)
    print(f"\n[Stage 2 – Quality Gate]\n{json.dumps(evaluation, indent=2)}")

    return {
        "status": "pass" if evaluation["pass"] else "fail",
        "classification": classification,
        "evaluation": evaluation,
    }


if __name__ == "__main__":
    library = FrameworkLibrary()
    library.register(
        TaskDispatcherFramework(), owner="ops-team", tags=["classification", "routing", "logistics"]
    )
    library.register(
        QualityGateFramework(), owner="quality-team", tags=["evaluation", "quality-assurance"]
    )
    library.register(
        ErrorRecoveryFramework(), owner="ops-team", tags=["recovery", "error-handling"]
    )

    # Test Case 1: Billing dispute
    print("\n" + "=" * 60)
    print("TEST CASE 1: Billing Dispute")
    run_workflow(
        library,
        customer_input="I was charged $847 for shipment SH-20241103 but I have a contract rate of $620. Please correct this immediately.",
        draft_response="We have reviewed your account and identified the billing discrepancy. "
        "A credit of $227 will be applied to your account. Our billing team will process this within 3–5 business days.",
    )

    # Test Case 2: Shipment tracking
    print("\n" + "=" * 60)
    print("TEST CASE 2: Shipment Tracking")
    run_workflow(
        library,
        customer_input="Where is my package TRK-98732? It was due yesterday and the portal shows no updates.",
        draft_response="Shipment TRK-98732 is currently in transit. Last scan shows it arrived at our regional hub at 11:47 PM. Expected delivery is today by 6 PM.",
    )

    # Test Case 3: Ambiguous input
    print("\n" + "=" * 60)
    print("TEST CASE 3: Ambiguous Input")
    run_workflow(
        library,
        customer_input="There's an issue with my account and I need it fixed.",
        draft_response="We understand you have an issue. Please contact our support team.",
    )
