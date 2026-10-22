# Applied AI Engineering, Volume II, Chapter 20
# Section 20.5, Building the Evaluation Pipeline
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# shopcore_support_pipeline.py

import json
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import datetime, timezone

# ── Mock LLM ─────────────────────────────────────────────────────────────

def mock_llm_classify(prompt: str) -> str:
    return json.dumps({
        "category": "order_status",
        "confidence": 0.94,
        "extracted_ids": {"order_id": "ORD-48291", "account_id": None},
        "flags": []
    })

def mock_llm_respond(prompt: str) -> str:
    return json.dumps({
        "response_draft": (
            "Hi there! Thank you for reaching out to ShopCore. "
            "I've pulled up order ORD-48291 and can see it shipped on July 24 via FedEx Ground. "
            "Your tracking number is 1Z999AA10123456784. "
            "Expected delivery is July 28. "
            "Is there anything else I can help you with today?"
        ),
        "tone": "empathetic",
        "word_count": 52
    })

def mock_llm_evaluate(prompt: str) -> str:
    return json.dumps({
        "scores": {
            "relevance": {"score": 5, "justification": "Directly addresses the order status inquiry with specific tracking information."},
            "brand_voice": {"score": 4, "justification": "Warm and professional tone. Could include a more personalized closing."},
            "completeness": {"score": 4, "justification": "Provides tracking number and delivery date. Does not offer proactive resolution if package is delayed."},
            "accuracy_risk": {"score": 4, "justification": "References specific order and tracking data. Risk exists if system data is stale."}
        },
        "weighted_total": 0.86,
        "pass": True,
        "top_improvement": "Add a contingency statement if the delivery date passes without delivery."
    })

# ── Pipeline Components ───────────────────────────────────────────────────

CLASSIFIER_TEMPLATE = """\
You are a customer support ticket classification specialist for ShopCore,
an e-commerce platform.

CLASSIFICATION CATEGORIES:
- order_status: Questions about order location, delivery date, tracking
- return_request: Requests to return merchandise or receive refunds
- account_access: Login problems, password resets, account locked
- product_info: Questions about product specifications, availability, sizing
- escalate_to_human: Complaints, legal threats, sensitive billing disputes, ambiguous requests

EXTRACTION RULES:
- Extract order IDs matching pattern ORD-NNNNN
- Extract account identifiers if mentioned
- Flag any PII (phone numbers, addresses, SSNs) as a compliance flag

TICKET:
{{ticket_text}}

Respond ONLY with valid JSON matching the classifier output schema.
BEGIN:"""

RESPONSE_GENERATOR_TEMPLATE = """\
You are Alex, a ShopCore customer support specialist.

BRAND VOICE GUIDELINES:
- Warm but professional. Use the customer's implicit tone as a guide.
- Solution-focused: every response ends with a clear next step or resolution.
- Honest: never make specific delivery promises that depend on third-party carriers.
- Concise: 40–80 words for routine inquiries; up to 150 for complex issues.

TICKET CATEGORY: {{category}}
CUSTOMER TICKET: {{ticket_text}}
EXTRACTED CONTEXT: {{extracted_ids}}

Draft a response that fully resolves or meaningfully progresses this ticket.
Respond ONLY with valid JSON:
{
  "response_draft": "<string>",
  "tone": "empathetic|informational|apologetic|neutral",
  "word_count": <int>
}
BEGIN:"""

EVALUATOR_TEMPLATE = """\
You are a quality assurance evaluator for ShopCore's AI customer support system.

ORIGINAL CUSTOMER TICKET:
{{ticket_text}}

AI-GENERATED RESPONSE DRAFT:
{{response_draft}}

EVALUATE on four dimensions (1=Poor, 5=Excellent):

RELEVANCE (35%): Does the response directly and specifically address the customer's actual question?
BRAND VOICE (25%): Does the response match ShopCore's warm, professional, solution-focused brand voice?
COMPLETENESS (25%): Does the response provide all information needed to fully resolve the ticket?
ACCURACY RISK (15%): Does the response avoid specific unverifiable factual claims? (5=no risk, 1=high risk)

Respond ONLY with valid JSON matching the evaluator output schema.
BEGIN EVALUATION:"""


@dataclass
class SupportPipeline:
    classify_llm: Callable[[str], str]
    respond_llm: Callable[[str], str]
    evaluate_llm: Callable[[str], str]
    quality_threshold: float = 0.78
    confidence_threshold: float = 0.85

    # Evaluation weights
    WEIGHTS = {
        "relevance": 0.35,
        "brand_voice": 0.25,
        "completeness": 0.25,
        "accuracy_risk": 0.15,
    }

    def _render(self, template: str, **kwargs) -> str:
        rendered = template
        for k, v in kwargs.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    def classify(self, ticket_text: str) -> dict:
        prompt = self._render(CLASSIFIER_TEMPLATE, ticket_text=ticket_text)
        return json.loads(self.classify_llm(prompt))

    def generate_response(self, category: str, ticket_text: str,
                          extracted_ids: dict) -> dict:
        prompt = self._render(
            RESPONSE_GENERATOR_TEMPLATE,
            category=category,
            ticket_text=ticket_text,
            extracted_ids=json.dumps(extracted_ids)
        )
        return json.loads(self.respond_llm(prompt))

    def evaluate(self, ticket_text: str, response_draft: str) -> dict:
        prompt = self._render(
            EVALUATOR_TEMPLATE,
            ticket_text=ticket_text,
            response_draft=response_draft
        )
        result = json.loads(self.evaluate_llm(prompt))
        # Recompute weighted total for audit integrity
        total = sum(
            (result["scores"][dim]["score"] / 5) * weight
            for dim, weight in self.WEIGHTS.items()
        )
        result["weighted_total"] = round(total, 3)
        result["pass"] = result["weighted_total"] >= self.quality_threshold
        return result

    def run(self, ticket_text: str) -> dict:
        """Execute the full three-stage pipeline for a ticket."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Stage 1: Classify
        classification = self.classify(ticket_text)
        print(f"\n[Stage 1 - Classify]\n{json.dumps(classification, indent=2)}")

        # Route to human if low confidence or explicit escalation
        if (classification["confidence"] < self.confidence_threshold
                or classification["category"] == "escalate_to_human"):
            return {
                "ticket": ticket_text,
                "outcome": "routed_to_human",
                "reason": f"Low confidence ({classification['confidence']}) or escalation category",
                "timestamp": timestamp,
            }

        # Stage 2: Generate Response
        generation = self.generate_response(
            category=classification["category"],
            ticket_text=ticket_text,
            extracted_ids=classification["extracted_ids"]
        )
        print(f"\n[Stage 2 - Generate]\n{json.dumps(generation, indent=2)}")

        # Stage 3: Evaluate
        evaluation = self.evaluate(
            ticket_text=ticket_text,
            response_draft=generation["response_draft"]
        )
        print(f"\n[Stage 3 - Evaluate]\n{json.dumps(evaluation, indent=2)}")

        outcome = "delivered_to_customer" if evaluation["pass"] else "routed_to_human"
        return {
            "ticket": ticket_text,
            "outcome": outcome,
            "classification": classification,
            "response": generation,
            "evaluation": evaluation,
            "timestamp": timestamp,
        }
