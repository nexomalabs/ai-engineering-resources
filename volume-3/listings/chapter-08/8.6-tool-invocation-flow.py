# Applied AI Engineering, Volume III, Chapter 8
# Section 8.6, Tool Invocation Flow
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
from typing import Callable

class ToolCallingOrchestrator:
    """
    Manages the multi-turn tool calling loop.
    Compatible with OpenAI-style chat completions API.
    """

    def __init__(self, llm_client, tool_registry: dict[str, Callable], tool_schemas: list[dict]):
        self.client = llm_client
        self.registry = tool_registry
        self.schemas = tool_schemas
        self.max_iterations = 10  # Safety limit

    def run(self, user_query: str, model: str = "gpt-6-luna") -> str:
        messages = [{"role": "user", "content": user_query}]

        for iteration in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.schemas,
                tool_choice="auto",
            )
            message = response.choices[0].message

            if response.choices[0].finish_reason == "stop":
                return message.content

            if response.choices[0].finish_reason == "tool_calls":
                messages.append(message)  # Append assistant message with tool calls
                tool_results = self._execute_tool_calls(message.tool_calls)
                messages.extend(tool_results)
            else:
                # Unexpected finish reason
                return message.content or ""

        return "Maximum iterations reached without a final response."

    def _execute_tool_calls(self, tool_calls) -> list[dict]:
        """Execute all requested tool calls and return result messages."""
        results = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
                if name not in self.registry:
                    result = {"error": f"Tool '{name}' not found."}
                else:
                    result = self.registry[name](**args)
            except json.JSONDecodeError as e:
                result = {"error": f"Invalid argument JSON: {e}"}
            except TypeError as e:
                result = {"error": f"Argument mismatch: {e}"}
            except Exception as e:
                result = {"error": f"Tool execution failed: {type(e).__name__}: {e}"}

            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })
        return results
