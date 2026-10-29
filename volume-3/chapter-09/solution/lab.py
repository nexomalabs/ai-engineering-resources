"""Lab 9 — Multi-Step Function Calling Pipeline (reference solution).

Three functions with sequential data dependencies: step 3 uses results from steps 1 and 2.
Then the claim intake from the chapter's opening story: a strict function schema shapes
the model's output, and a Pydantic model checks the data before anything is imported.
No API key is required.

    python solution/lab.py
"""

import json

from pydantic import BaseModel, Field, ValidationError

# ── Tool Implementations ──────────────────────────────────────────────────────
CUSTOMER_DB = {
    "C001": {"name": "Acme Corp", "tier": "enterprise", "credit_limit": 50000.0},
    "C002": {"name": "Beta LLC", "tier": "standard", "credit_limit": 10000.0},
    "C003": {"name": "Gamma Inc", "tier": "premium", "credit_limit": 25000.0},
}
ORDER_HISTORY = {
    "C001": [{"order_id": "ORD-1001", "amount": 12500.0, "status": "completed"}],
    "C002": [{"order_id": "ORD-1002", "amount": 2300.0, "status": "completed"}],
    "C003": [{"order_id": "ORD-1003", "amount": 8900.0, "status": "pending"}],
}


def get_customer(customer_id: str) -> dict:
    """Step 1: Look up a customer record."""
    if customer_id not in CUSTOMER_DB:
        return {"error": f"Customer '{customer_id}' not found."}
    return {"customer_id": customer_id, **CUSTOMER_DB[customer_id]}


def get_order_history(customer_id: str, limit: int = 5) -> dict:
    """Step 2: Retrieve order history for a customer."""
    if customer_id not in ORDER_HISTORY:
        return {"customer_id": customer_id, "orders": [], "total_orders": 0, "total_value": 0.0}
    orders = ORDER_HISTORY[customer_id][:limit]
    total_value = sum(o["amount"] for o in orders)
    return {
        "customer_id": customer_id,
        "orders": orders,
        "total_orders": len(orders),
        "total_value": total_value,
    }


def generate_credit_report(
    customer_id: str,
    customer_tier: str,
    credit_limit: float,
    total_order_value: float,
) -> dict:
    """Step 3: Generate a credit report using data from steps 1 and 2."""
    utilization = (total_order_value / credit_limit * 100) if credit_limit > 0 else 0
    # A higher score means lower risk. Larger accounts weigh utilization more heavily,
    # because the same percentage is a larger exposure in dollars.
    tier_multipliers = {"standard": 1.0, "premium": 1.2, "enterprise": 1.5}
    risk_score = max(0, min(100, 100 - utilization * tier_multipliers.get(customer_tier, 1.0)))
    recommendation = "Approve" if risk_score >= 70 else "Review" if risk_score >= 40 else "Decline"
    return {
        "customer_id": customer_id,
        "credit_limit": credit_limit,
        "utilized_amount": round(total_order_value, 2),
        "utilization_pct": round(utilization, 1),
        "risk_score": round(risk_score, 1),
        "recommendation": recommendation,
        "tier": customer_tier,
    }


REGISTRY = {
    "get_customer": get_customer,
    "get_order_history": get_order_history,
    "generate_credit_report": generate_credit_report,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Look up a customer by ID. Returns name, tier (standard/premium/enterprise), and credit limit.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_history",
            "description": "Get the recent order history for a customer. Returns orders with amounts and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_credit_report",
            "description": "Generate a credit risk report. Requires customer tier and credit limit from get_customer, and total order value from get_order_history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "customer_tier": {
                        "type": "string",
                        "enum": ["standard", "premium", "enterprise"],
                    },
                    "credit_limit": {"type": "number", "description": "Credit limit in USD"},
                    "total_order_value": {
                        "type": "number",
                        "description": "Sum of all orders in USD",
                    },
                },
                "required": ["customer_id", "customer_tier", "credit_limit", "total_order_value"],
            },
        },
    },
]


# ── Pipeline Runner (with mock multi-step scenario) ────────────────────────
def simulate_multi_step_pipeline(customer_id: str):
    """
    Simulate a 3-step dependent function calling pipeline.
    Mimics the conversation flow without requiring an LLM API.
    """
    print(f"\n{'=' * 60}")
    print(f"CREDIT ASSESSMENT PIPELINE — Customer: {customer_id}")
    print("=" * 60)

    # Step 1: get_customer
    print("\n[Step 1] get_customer")
    args1 = {"customer_id": customer_id}
    result1 = get_customer(**args1)
    print(f"  args:   {args1}")
    print(f"  result: {json.dumps(result1, indent=10)}")
    if "error" in result1:
        print("  ✗ Customer not found. Aborting.")
        return

    # Step 2: get_order_history (depends on customer_id from step 1)
    print("\n[Step 2] get_order_history")
    args2 = {"customer_id": result1["customer_id"], "limit": 5}
    result2 = get_order_history(**args2)
    print(f"  args:   {args2}")
    print(f"  result: {json.dumps(result2, indent=10)}")

    # Step 3: generate_credit_report (depends on steps 1 AND 2)
    print("\n[Step 3] generate_credit_report")
    args3 = {
        "customer_id": result1["customer_id"],
        "customer_tier": result1["tier"],
        "credit_limit": result1["credit_limit"],
        "total_order_value": result2["total_value"],
    }
    result3 = generate_credit_report(**args3)
    print(f"  args:   {args3}")
    print(f"  result: {json.dumps(result3, indent=10)}")

    # Final summary
    print("\n── Credit Assessment Summary ──────────────────────────────")
    print(f"  Customer:     {result1['name']} ({result1['tier']})")
    print(f"  Credit Limit: ${result1['credit_limit']:,.2f}")
    print(f"  Order Value:  ${result2['total_value']:,.2f}")
    print(f"  Utilization:  {result3['utilization_pct']}%")
    print(f"  Risk Score:   {result3['risk_score']}/100")
    print(f"  Decision:     {result3['recommendation']}")


# ── Claim intake: valid JSON is not the same as valid data ────────────────────
# A forced call to this function turns a customer's email into a claim record. With
# "strict": True the API guarantees the arguments match the schema's shape and types,
# which strict mode requires to forbid extra properties and to list every property.
CLAIM_TOOL = {
    "type": "function",
    "function": {
        "name": "record_claim",
        "description": "Record a damage claim from a customer's email.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "Wrenfield tracking number, such as WF-2291",
                },
                "damage_description": {"type": "string"},
                "declared_value": {
                    "type": "number",
                    "description": "Value of the damaged item, in pounds",
                },
            },
            "required": ["tracking_number", "damage_description", "declared_value"],
            "additionalProperties": False,
        },
    },
}


class ClaimRecord(BaseModel):
    """What the claims system accepts. Checked after the call, before the import."""

    tracking_number: str = Field(pattern=r"^WF-[0-9]{4}$")
    damage_description: str = Field(min_length=1)
    declared_value: float = Field(gt=0, le=10_000)


# The arguments the model returned for three emails. E2 is the response from the story,
# from a call made without strict mode: valid JSON, with a string where the schema has a
# number. E3 came from a call with strict mode on: every type matches, and the data is
# still wrong. Strict mode prevents the first kind of failure; only validation catches both.
MODEL_ARGUMENTS = {
    "E1": '{"tracking_number": "WF-2291", "damage_description": "Cracked monitor screen", "declared_value": 189.0}',
    "E2": '{"tracking_number": "WF-3107", "damage_description": "Dented kettle", "declared_value": "about two hundred pounds"}',
    "E3": '{"tracking_number": "order 5531", "damage_description": "Broken lamp", "declared_value": 0}',
}


def intake_claim(email_id: str, arguments: str) -> dict:
    """Validate the model's arguments; import a valid claim, send anything else to a person."""
    try:
        claim = ClaimRecord.model_validate_json(arguments)
    except ValidationError as e:
        problems = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        return {"email": email_id, "status": "sent to a person", "problems": problems}
    return {"email": email_id, "status": "imported", "claim": claim.model_dump()}


def run_claim_intake():
    print(f"\n{'=' * 60}")
    print("CLAIM INTAKE — valid JSON is not the same as valid data")
    print("=" * 60)
    for email_id, arguments in MODEL_ARGUMENTS.items():
        result = intake_claim(email_id, arguments)
        print(f"\n[{email_id}] arguments: {arguments}")
        if result["status"] == "imported":
            print(f"  ✓ imported: {result['claim']}")
        else:
            print("  ✗ sent to a person:")
            for problem in result["problems"]:
                print(f"      {problem}")


if __name__ == "__main__":
    for cid in ["C001", "C002", "C003", "C999"]:
        simulate_multi_step_pipeline(cid)
    run_claim_intake()
