"""Tools for the Lab 11 ReAct agent: a mocked web search, a calculator, and the date.

The search results are canned, so the lab runs offline. The figures in them are the World
Bank's 2024 values; everything else is general knowledge.
"""

import math
from datetime import date

SEARCH_RESULTS = {
    "france gdp 2024": "France GDP (2024): approximately $3.16 trillion USD (World Bank).",
    "population of japan": "Japan population (2024): approximately 124.0 million people (World Bank).",
    "python creator": "Python was created by Guido van Rossum, first released in 1991.",
    "eiffel tower height": "The Eiffel Tower is 330 meters tall including the broadcast antenna.",
    "speed of light": "The speed of light in a vacuum is exactly 299,792,458 meters per second.",
    "shipment wf-2291": "Shipment WF-2291: in transit; last scanned at the depot 3 days ago.",
}

ALLOWED_CHARACTERS = set("0123456789+-*/().,e E")


def web_search(query: str) -> str:
    """Mock web search returning canned results for demonstration."""
    key = query.lower().strip()
    for k, v in SEARCH_RESULTS.items():
        if k in key or key in k:
            return v
    return f"No results found for: {query}"


def validate_expression(expression: str) -> bool:
    """Allow only digits, arithmetic operators, brackets and scientific notation."""
    return bool(expression.strip()) and all(c in ALLOWED_CHARACTERS for c in expression)


def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression in a namespace with no builtins."""
    if not validate_expression(expression):
        return "Error: expression contains invalid characters."
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def get_current_date(_args: str = "") -> str:
    """Return today's date."""
    return str(date.today())


TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "get_current_date": get_current_date,
}

TOOL_DESCRIPTIONS = """
Available tools:
- web_search(query: str): Search the web for factual information.
- calculator(expression: str): Evaluate a Python arithmetic expression. E.g. "3.16e12 * 0.15"
- get_current_date(): Return today's date in YYYY-MM-DD format.
- finish(answer: str): Return the final answer and stop.
"""
