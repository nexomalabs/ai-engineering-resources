# Applied AI Engineering, Volume III, Chapter 11
# Section 11.6, Action
# Copied from the book by scripts/export_listings.py. Report errors as errata.

tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information.",
        "parameters": {
            "query": {"type": "string", "description": "The search query."}
        }
    },
    {
        "name": "calculator",
        "description": "Evaluate a mathematical expression.",
        "parameters": {
            "expression": {"type": "string", "description": "Python expression to evaluate."}
        }
    }
]
