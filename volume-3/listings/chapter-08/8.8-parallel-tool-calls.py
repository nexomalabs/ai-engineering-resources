# Applied AI Engineering, Volume III, Chapter 8
# Section 8.8, Parallel Tool Calls
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import json

async def execute_tool_calls_parallel(
    tool_calls: list,
    registry: dict[str, Callable],
) -> list[dict]:
    """Execute multiple tool calls in parallel using asyncio."""

    async def execute_one(tool_call) -> dict:
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
            func = registry.get(name)
            if func is None:
                result = {"error": f"Tool '{name}' not found."}
            elif asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                # Run sync functions in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: func(**args))
        except Exception as e:
            result = {"error": str(e)}
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        }

    return await asyncio.gather(*[execute_one(tc) for tc in tool_calls])
