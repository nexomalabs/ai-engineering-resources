# Applied AI Engineering, Volume III, Chapter 9
# Section 9.5, Handling Function Call Results
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
from datetime import datetime, timezone

def format_tool_result(tool_call_id: str, result: dict | str) -> dict:
    """Format a tool execution result as a conversation message."""
    if isinstance(result, dict) and "error" in result:
        # Errors should be clearly labeled
        content = json.dumps({
            "status": "error",
            "error": result["error"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    elif isinstance(result, dict):
        content = json.dumps({
            "status": "success",
            **result,
        })
    else:
        content = str(result)

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }
