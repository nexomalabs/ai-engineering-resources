"""Lab 2 — Context Window Manager (reference solution).

Counts tokens with tiktoken, keeps required blocks, and fills the remaining budget with
optional blocks in priority order.

    python solution/lab.py
"""

# context_window_manager.py
import json
from dataclasses import dataclass, field
from typing import List, Optional

import tiktoken


@dataclass
class ContentBlock:
    name: str
    text: str
    priority: int  # 1 = highest, 10 = lowest
    required: bool = False  # Required blocks are never truncated
    token_count: int = field(init=False)

    def __post_init__(self):
        enc = tiktoken.get_encoding("cl100k_base")
        self.token_count = len(enc.encode(self.text))


class ContextWindowManager:
    """
    Manages a collection of ContentBlocks within a token budget.
    Applies priority-based truncation when budget is exceeded.
    """

    def __init__(
        self,
        model: str = "gpt-6.1-sol",
        budget_fraction: float = 0.85,
        token_budget: Optional[int] = None,
    ):
        """
        Args:
            model: The target model name (used to look up context window size).
            budget_fraction: Fraction of the model's max context to use for input.
            token_budget: An explicit budget in tokens; overrides budget_fraction.
        """
        self.model = model
        self.blocks: List[ContentBlock] = []
        self._encoder = tiktoken.get_encoding("cl100k_base")

        # Known model context windows (tokens)
        MODEL_WINDOWS = {
            "gpt-6.1-sol": 1_050_000,
            "gpt-6-luna": 1_050_000,
            "gpt-4": 8_192,  # retired; kept as a small-window example
        }
        max_window = MODEL_WINDOWS.get(model, 8_192)
        self.token_budget = token_budget or int(max_window * budget_fraction)

    def add(self, block: ContentBlock) -> None:
        self.blocks.append(block)

    def _total_tokens(self, blocks: List[ContentBlock]) -> int:
        return sum(b.token_count for b in blocks)

    def build(self) -> dict:
        """
        Build the context, applying truncation if necessary.
        Returns the final block list, token report, and OpenAI messages.
        """
        required = [b for b in self.blocks if b.required]
        optional = sorted([b for b in self.blocks if not b.required], key=lambda b: b.priority)

        required_tokens = self._total_tokens(required)
        if required_tokens > self.token_budget:
            raise ValueError(
                f"Required blocks alone ({required_tokens} tokens) exceed "
                f"budget ({self.token_budget} tokens). Cannot build context."
            )

        included = list(required)
        excluded = []
        current_tokens = required_tokens

        for block in optional:
            if current_tokens + block.token_count <= self.token_budget:
                included.append(block)
                current_tokens += block.token_count
            else:
                excluded.append(block)

        # Sort included by priority for message assembly
        included_sorted = sorted(included, key=lambda b: b.priority)

        messages = []
        # Combine all blocks into a system message followed by a user message
        system_content = []
        user_content = []

        for block in included_sorted:
            if block.name.startswith("user_message"):
                user_content.append(block.text)
            else:
                system_content.append(f"## {block.name.replace('_', ' ').upper()}\n{block.text}")

        if system_content:
            messages.append({"role": "system", "content": "\n\n".join(system_content)})
        if user_content:
            messages.append({"role": "user", "content": "\n".join(user_content)})

        report = {
            "model": self.model,
            "token_budget": self.token_budget,
            "tokens_used": current_tokens,
            "utilization_pct": round(current_tokens / self.token_budget * 100, 1),
            "blocks_total": len(self.blocks),
            "blocks_included": len(included),
            "blocks_excluded": len(excluded),
            "excluded": [
                {"name": b.name, "tokens": b.token_count, "priority": b.priority} for b in excluded
            ],
        }

        return {"messages": messages, "report": report}


def run_demo():
    # A deliberately small budget, so the demo shows truncation.
    # (The default, 85% of gpt-6.1-sol's 1.05M-token window, would include everything.)
    manager = ContextWindowManager(model="gpt-6.1-sol", token_budget=200)

    manager.add(
        ContentBlock(
            name="system_role",
            text="You are a senior financial analyst. Answer all questions with data-driven precision.",
            priority=1,
            required=True,
        )
    )

    manager.add(
        ContentBlock(
            name="compliance_rules",
            text=(
                "COMPLIANCE RULES:\n"
                "1. Do not provide specific investment advice.\n"
                "2. Always recommend consulting a licensed advisor.\n"
                "3. Cite sources when providing market data."
            ),
            priority=2,
            required=True,
        )
    )

    # The documents below are fictional sample data for this lab.
    manager.add(
        ContentBlock(
            name="retrieved_doc_1",
            text=(
                "MARKET REPORT (Q2): The Northwind 500 index closed the quarter at 5,480. "
                "Year-to-date return: 12.4%. Top performing sector: Technology (+21.8%). "
                "The central bank held its policy rate at 4.25-4.50% through Q2. "
                "Consumer prices rose 2.8% year over year in June."
            ),
            priority=3,
        )
    )

    manager.add(
        ContentBlock(
            name="retrieved_doc_2",
            text=(
                "ANALYST CONSENSUS (July): 68% of surveyed analysts rate the Northwind 500 "
                "as 'Hold'. Median 12-month price target: 5,800. Key risk factors: "
                "geopolitical tensions, supply chain disruptions, AI infrastructure spending. "
                "Energy sector underperformed by 8.2% YTD."
            ),
            priority=4,
        )
    )

    manager.add(
        ContentBlock(
            name="conversation_history",
            text=(
                "Previous turn: User asked about tech sector outlook. "
                "Assistant confirmed Technology is the top-performing sector this year "
                "with a +21.8% YTD return and recommended reviewing specific ETF allocations "
                "with a licensed advisor."
            ),
            priority=5,
        )
    )

    manager.add(
        ContentBlock(
            name="user_message",
            text="What is the current policy interest rate and how does it affect bond yields?",
            priority=1,
            required=True,
        )
    )

    result = manager.build()

    print("=== TOKEN UTILIZATION REPORT ===")
    print(json.dumps(result["report"], indent=2))

    print("\n=== FINAL MESSAGES ===")
    for msg in result["messages"]:
        preview = msg["content"][:400]
        print(f"\n[{msg['role'].upper()}]\n{preview}{'...' if len(msg['content']) > 400 else ''}")


if __name__ == "__main__":
    run_demo()
