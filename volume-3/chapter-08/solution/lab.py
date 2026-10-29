"""Lab 8 — Tool-Calling System (reference solution).

Demonstrates the complete tool-calling lifecycle with four mock tools and no API key:
schemas, argument validation before a tool runs, and the loop in which the model asks for
a tool, the tool runs, and its result goes back to the model.

    python solution/lab.py
"""

import json
import re
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


SHIPMENTS = {
    "WF-2291": {"status": "in transit", "last_scan": "Leeds depot", "expected": "Thursday"},
    "WF-3107": {"status": "delivered", "last_scan": "front door", "expected": "Monday"},
}


def get_shipment_status(tracking_number: str) -> dict:
    """Mock tracking for Wrenfield parcels: the tool from the chapter's opening story."""
    if tracking_number not in SHIPMENTS:
        return {"error": f"No shipment with tracking number '{tracking_number}'."}
    return {"tracking_number": tracking_number, **SHIPMENTS[tracking_number]}


# ── Tool Registry and Schemas ─────────────────────────────────────────────────
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_database": search_database,
    "calculate_cost": calculate_cost,
    "get_shipment_status": get_shipment_status,
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


# The rewritten tool from the story: a name that says what it does, a description that
# says what it returns and when to use it, and a parameter only a tracking number fits.
TOOL_SCHEMAS.append(
    {
        "type": "function",
        "function": {
            "name": "get_shipment_status",
            "description": (
                "Return the delivery status, last scan location and expected delivery day of "
                "one Wrenfield parcel. Use it only with a tracking number the customer gave."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "pattern": "^WF-[0-9]{4}$",
                        "description": (
                            "Wrenfield tracking number: WF- and four digits, such as WF-2291. "
                            "Never an order number or a postcode."
                        ),
                    }
                },
                "required": ["tracking_number"],
                "additionalProperties": False,
            },
        },
    }
)


# ── Argument validation (before any tool runs) ────────────────────────────────
JSON_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def validate_arguments(parameters: dict, args: dict) -> list[str]:
    """Check a tool call's arguments against the tool's JSON Schema; return the problems."""
    errors = []
    properties = parameters.get("properties", {})
    for name in parameters.get("required", []):
        if name not in args:
            errors.append(f"missing required argument '{name}'")
    for name, value in args.items():
        spec = properties.get(name)
        if spec is None:
            if parameters.get("additionalProperties") is False:
                errors.append(f"unexpected argument '{name}'")
            continue
        kind = spec.get("type")
        wrong_type = kind in JSON_TYPES and not isinstance(value, JSON_TYPES[kind])
        if kind in ("integer", "number") and isinstance(value, bool):
            wrong_type = True  # bool is a subclass of int in Python, but not in JSON
        if wrong_type:
            errors.append(f"'{name}' must be of type {kind}")
            continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"'{name}' must be one of {spec['enum']}")
        if "pattern" in spec and not re.search(spec["pattern"], value):
            errors.append(f"'{name}' does not match the pattern {spec['pattern']}")
    return errors


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
        self.parameters = {s["function"]["name"]: s["function"]["parameters"] for s in schemas}

    def _execute_tool_call(self, tool_call) -> dict:
        # Read the call as the API delivers it: a name, and arguments as a JSON string
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return {"error": "Arguments are not valid JSON."}
        if name not in self.registry:
            return {"error": f"Unknown tool: {name}"}
        problems = validate_arguments(self.parameters.get(name, {}), args)
        if problems:
            # The tool never runs; the model gets the reason and can correct itself
            return {"error": "Invalid arguments: " + "; ".join(problems)}
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


# ── The model–tool loop ───────────────────────────────────────────────────────
class ScriptedModel:
    """
    A stand-in for the model, returning responses shaped like OpenAI chat completions. Asked
    about a parcel, it calls the shipment tool with whatever looks like a tracking number in
    the customer's message or, failing that, with whatever identifier it can find, as the
    model in the chapter's story did. Given a tool result, it answers from it.
    """

    POSTCODE = re.compile(r"\b[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}\b")

    def create(self, messages: list[dict], tools: list[dict]) -> MockLLMResponse:
        last = messages[-1]
        if last["role"] == "tool":
            result = json.loads(last["content"])
            if "error" in result:
                return MockLLMResponse(
                    "stop",
                    content="I can look that up with your tracking number: WF- and four "
                    "digits, such as WF-2291. Could you send it?",
                )
            return MockLLMResponse(
                "stop",
                content=f"Your parcel {result['tracking_number']} is {result['status']}, "
                f"last scanned at the {result['last_scan']}, expected {result['expected']}.",
            )
        text = last["content"]
        found = re.search(r"WF-[0-9]+", text) or self.POSTCODE.search(text)
        guess = found.group(0) if found else text
        call = MockToolCall(
            f"call_{len(messages)}", "get_shipment_status", {"tracking_number": guess}
        )
        return MockLLMResponse("tool_calls", tool_calls=[call])


def run_conversation(user_message: str, model, orchestrator, max_turns: int = 4) -> str:
    """The loop: the model asks for tools, the tools run, and their results go back to it."""
    messages = [{"role": "user", "content": user_message}]
    print(f"\nUser: {user_message}")
    for _ in range(max_turns):
        message = model.create(messages, orchestrator.schemas).choices[0].message
        if not message.tool_calls:
            print(f"Assistant: {message.content}")
            return message.content
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            result = orchestrator._execute_tool_call(call)
            print(f"  → {call.function.name}({call.function.arguments})")
            print(f"  ← {json.dumps(result)}")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    return "Stopped: too many tool calls."


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

    # Scenario 6: the full loop, with the story's tool
    print(f"\n{'=' * 60}")
    print("SCENARIO: The model–tool loop — Where is my parcel?")
    print("=" * 60)
    model = ScriptedModel()
    run_conversation("Where is my parcel? The tracking number is WF-2291.", model, orch)
    run_conversation("Where is my parcel? I live at SW1A 1AA.", model, orch)

    print("\n✓ All tool calling scenarios completed successfully.")


if __name__ == "__main__":
    main()
