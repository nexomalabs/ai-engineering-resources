"""Lab 8 — Tool-Calling System (reference solution).

Demonstrates the complete tool-calling lifecycle with three mock tools and no API key.

    python solution/lab.py
"""

import json
from dataclasses import dataclass, field
from types import SimpleNamespace


# ── Tool Implementations (Mock) ──────────────────────────────────────────────
def get_weather(city: str, units: str = "celsius") -> dict:
    """Mock weather API."""
    weather_data = {
        "Paris": {"temp": 18, "condition": "Partly cloudy", "humidity": 65},
        "London": {"temp": 14, "condition": "Overcast", "humidity": 82},
        "Tokyo": {"temp": 24, "condition": "Clear", "humidity": 55},
        "New York": {"temp": 20, "condition": "Sunny", "humidity": 48},
    }
    if city not in weather_data:
        return {"error": f"City '{city}' not found in weather database."}
    data = weather_data[city].copy()
    if units == "fahrenheit":
        data["temp"] = round(data["temp"] * 9 / 5 + 32, 1)
    data["units"] = units
    data["city"] = city
    return data


def search_database(query: str, limit: int = 3) -> dict:
    """Mock database search."""
    records = [
        {"id": 1, "name": "Neural Network Fundamentals", "type": "course", "rating": 4.8},
        {"id": 2, "name": "Python for Data Science", "type": "course", "rating": 4.6},
        {"id": 3, "name": "Transformer Architecture", "type": "article", "rating": 4.9},
        {"id": 4, "name": "Prompt Engineering Guide", "type": "book", "rating": 4.7},
        {"id": 5, "name": "RAG System Design", "type": "course", "rating": 4.5},
    ]
    query_lower = query.lower()
    results = [r for r in records if any(word in r["name"].lower() for word in query_lower.split())]
    return {"results": results[:limit], "total_found": len(results), "query": query}


def calculate_cost(items: list[dict]) -> dict:
    """
    Mock cost calculator.
    items: list of {"name": str, "quantity": int, "unit_price": float}
    """
    if not items:
        return {"error": "No items provided."}
    line_items = []
    subtotal = 0.0
    for item in items:
        name = item.get("name", "Unknown")
        qty = item.get("quantity", 1)
        price = item.get("unit_price", 0.0)
        total = round(qty * price, 2)
        subtotal += total
        line_items.append({"name": name, "quantity": qty, "unit_price": price, "total": total})
    tax = round(subtotal * 0.08, 2)
    return {
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "tax_8pct": tax,
        "grand_total": round(subtotal + tax, 2),
        "currency": "USD",
    }


# ── Tool Registry and Schemas ─────────────────────────────────────────────────
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_database": search_database,
    "calculate_cost": calculate_cost,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Returns temperature, humidity, and condition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "Search the content database for courses, articles, and books.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search terms"},
                    "limit": {"type": "integer", "description": "Max results (1-10)", "default": 3},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_cost",
            "description": "Calculate total cost for a list of items including 8% tax.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "unit_price": {"type": "number"},
                            },
                            "required": ["name", "quantity", "unit_price"],
                        },
                        "description": "List of items to price.",
                    }
                },
                "required": ["items"],
            },
        },
    },
]


# ── Mock LLM (simulates tool calling decisions) ──────────────────────────────
@dataclass
class MockToolCall:
    id: str
    function_name: str
    function_args: dict

    class _Function:
        def __init__(self, name, args):
            self.name = name
            self.arguments = json.dumps(args)

    def __post_init__(self):
        self.function = self._Function(self.function_name, self.function_args)


@dataclass
class MockLLMResponse:
    finish_reason: str
    content: str | None = None
    tool_calls: list = field(default_factory=list)

    @property
    def choices(self):
        # Mirrors the shape of an OpenAI response: response.choices[0].message
        message = SimpleNamespace(content=self.content, tool_calls=self.tool_calls)
        return [SimpleNamespace(finish_reason=self.finish_reason, message=message)]


# ── Orchestrator ─────────────────────────────────────────────────────────────
class MockOrchestrator:
    """Demonstrates the tool-calling loop without a real LLM API."""

    def __init__(self, registry, schemas):
        self.registry = registry
        self.schemas = schemas

    def _execute_tool_call(self, tool_call: MockToolCall) -> dict:
        name = tool_call.function_name
        args = tool_call.function_args
        if name not in self.registry:
            return {"error": f"Unknown tool: {name}"}
        try:
            return self.registry[name](**args)
        except Exception as e:
            return {"error": str(e)}

    def demonstrate_scenario(self, scenario_name: str, tool_calls: list[MockToolCall]):
        """Run a demonstration scenario."""
        print(f"\n{'=' * 60}")
        print(f"SCENARIO: {scenario_name}")
        print("=" * 60)
        for tc in tool_calls:
            print(f"\n→ Tool Call: {tc.function_name}({tc.function_args})")
            result = self._execute_tool_call(tc)
            print(f"← Result:    {json.dumps(result, indent=2)}")


# ── Main demonstration ────────────────────────────────────────────────────────
def main():
    orch = MockOrchestrator(TOOL_REGISTRY, TOOL_SCHEMAS)

    # Scenario 1: Single weather lookup
    orch.demonstrate_scenario(
        "Weather Query — Paris",
        [MockToolCall("tc_001", "get_weather", {"city": "Paris"})],
    )

    # Scenario 2: Parallel weather comparison
    orch.demonstrate_scenario(
        "Parallel Weather Comparison",
        [
            MockToolCall("tc_002", "get_weather", {"city": "London", "units": "celsius"}),
            MockToolCall("tc_003", "get_weather", {"city": "Tokyo", "units": "celsius"}),
            MockToolCall("tc_004", "get_weather", {"city": "New York", "units": "fahrenheit"}),
        ],
    )

    # Scenario 3: Database search
    orch.demonstrate_scenario(
        "Database Search",
        [
            MockToolCall(
                "tc_005", "search_database", {"query": "neural network transformer", "limit": 3}
            )
        ],
    )

    # Scenario 4: Cost calculation
    orch.demonstrate_scenario(
        "Cost Calculation",
        [
            MockToolCall(
                "tc_006",
                "calculate_cost",
                {
                    "items": [
                        {"name": "Pro License", "quantity": 5, "unit_price": 49.99},
                        {"name": "Support Plan", "quantity": 1, "unit_price": 199.00},
                    ]
                },
            )
        ],
    )

    # Scenario 5: Error handling — unknown city
    orch.demonstrate_scenario(
        "Error Handling — Unknown City",
        [MockToolCall("tc_007", "get_weather", {"city": "Atlantis"})],
    )

    print("\n✓ All tool calling scenarios completed successfully.")


if __name__ == "__main__":
    main()
