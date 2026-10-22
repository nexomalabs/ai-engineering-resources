"""Lab 9 — Multi-Step Function Calling Pipeline (reference solution).

Three functions with sequential data dependencies: step 3 uses results from steps 1 and 2.
No API key is required.

    python solution/lab.py
"""

import json

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


if __name__ == "__main__":
    for cid in ["C001", "C002", "C003", "C999"]:
        simulate_multi_step_pipeline(cid)
