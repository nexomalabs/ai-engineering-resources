# Applied AI Engineering, Volume III, Chapter 9
# Section 9.6, Multi-Step Function Calls
# Copied from the book by scripts/export_listings.py. Report errors as errata.

"""
Multi-step function calling demonstration.
Each step depends on the result of the previous step.
"""

import json
import os
from openai import OpenAI

# ── Mock tool implementations ────────────────────────────────────────────────
PRODUCT_DB = {
    "ELEC-001": {"name": "Wireless Headphones Pro", "price": 149.99, "category": "Electronics"},
    "ELEC-002": {"name": "Smart Watch Series 5",    "price": 299.99, "category": "Electronics"},
    "ELEC-003": {"name": "Bluetooth Speaker Mini",  "price": 59.99,  "category": "Electronics"},
}
INVENTORY_DB = {"ELEC-001": 234, "ELEC-002": 87, "ELEC-003": 512}

def search_products(category: str, sort_by: str = "popularity") -> dict:
    products = [
        {"product_id": pid, **data}
        for pid, data in PRODUCT_DB.items()
        if data["category"].lower() == category.lower()
    ]
    if sort_by == "price_asc":
        products.sort(key=lambda p: p["price"])
    elif sort_by == "price_desc":
        products.sort(key=lambda p: p["price"], reverse=True)
    return {"products": products, "count": len(products), "category": category}

def get_inventory(product_id: str) -> dict:
    if product_id not in INVENTORY_DB:
        return {"error": f"Product '{product_id}' not found."}
    return {
        "product_id": product_id,
        "stock_quantity": INVENTORY_DB[product_id],
        "reorder_point": 50,
        "status": "in_stock" if INVENTORY_DB[product_id] > 0 else "out_of_stock",
    }

def calculate_revenue(unit_price: float, quantity: int, discount_pct: float = 0.0) -> dict:
    gross = unit_price * quantity
    discount_amount = gross * (discount_pct / 100.0)
    net = gross - discount_amount
    return {
        "unit_price": unit_price,
        "quantity": quantity,
        "gross_revenue": round(gross, 2),
        "discount_pct": discount_pct,
        "discount_amount": round(discount_amount, 2),
        "net_revenue": round(net, 2),
        "currency": "USD",
    }

TOOL_REGISTRY = {
    "search_products":   search_products,
    "get_inventory":     get_inventory,
    "calculate_revenue": calculate_revenue,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog. Returns a list of products with IDs and prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category, e.g. 'Electronics', 'Clothing'",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["popularity", "price_asc", "price_desc"],
                        "description": "Sort order for results.",
                        "default": "popularity",
                    },
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": "Get current stock level for a product by its product_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product ID, e.g. 'ELEC-001'"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_revenue",
            "description": "Calculate gross and net revenue for a sale. Returns revenue breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_price":   {"type": "number",  "description": "Price per unit in USD"},
                    "quantity":     {"type": "integer", "description": "Number of units sold"},
                    "discount_pct": {"type": "number",  "description": "Discount percentage (0-100)", "default": 0.0},
                },
                "required": ["unit_price", "quantity"],
            },
        },
    },
]


def run_multi_step_pipeline(query: str, verbose: bool = True) -> str:
    """Run a multi-step function calling pipeline."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "mock"))
    messages = [{"role": "user", "content": query}]
    step = 0

    while True:
        step += 1
        if verbose:
            print(f"\n── Step {step}: Calling LLM ──────────────────────────────────")

        response = client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if response.choices[0].finish_reason == "stop":
            if verbose:
                print(f"Final response: {message.content}")
            return message.content

        if response.choices[0].finish_reason == "tool_calls":
            messages.append(message)
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                if verbose:
                    print(f"  → {tc.function.name}({args})")
                result = TOOL_REGISTRY[tc.function.name](**args)
                if verbose:
                    print(f"  ← {json.dumps(result, indent=4)}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        if step > 10:
            return "Error: Maximum steps exceeded."
