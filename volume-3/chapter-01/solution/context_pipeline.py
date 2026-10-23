# context_pipeline.py
from dataclasses import dataclass
from typing import List

import tiktoken


@dataclass
class ContextBlock:
    """A single named block of context content."""

    name: str
    content: str
    priority: int  # Lower number = higher priority (1 = highest)
    layer: str  # 'system', 'user', 'knowledge', 'history', 'request'
    token_count: int = 0

    def __post_init__(self):
        encoder = tiktoken.get_encoding("cl100k_base")
        self.token_count = len(encoder.encode(self.content))


class ContextPipeline:
    """
    Assembles multiple ContextBlocks into a final context payload
    subject to a configurable token budget.
    """

    LAYER_ORDER = ["system", "knowledge", "user", "history", "request"]

    def __init__(self, token_budget: int = 4096):
        self.token_budget = token_budget
        self.blocks: List[ContextBlock] = []
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def add_block(self, block: ContextBlock) -> None:
        self.blocks.append(block)

    def _sort_blocks(self) -> List[ContextBlock]:
        """Sort by layer order first, then by priority within each layer."""
        layer_index = {layer: i for i, layer in enumerate(self.LAYER_ORDER)}
        return sorted(self.blocks, key=lambda b: (layer_index.get(b.layer, 99), b.priority))

    def assemble(self) -> dict:
        """
        Assemble all blocks respecting the token budget.
        Returns a dict with 'messages' (OpenAI format) and a usage report.
        """
        sorted_blocks = self._sort_blocks()
        included: List[ContextBlock] = []
        excluded: List[ContextBlock] = []
        tokens_used = 0

        # Reserve tokens for the model's response
        RESPONSE_RESERVE = 512
        available = self.token_budget - RESPONSE_RESERVE

        # Always include 'system' and 'request' layers regardless of budget
        mandatory_layers = {"system", "request"}

        # First pass: mandatory layers
        for block in sorted_blocks:
            if block.layer in mandatory_layers:
                included.append(block)
                tokens_used += block.token_count

        # Second pass: optional layers
        for block in sorted_blocks:
            if block.layer in mandatory_layers:
                continue
            if tokens_used + block.token_count <= available:
                included.append(block)
                tokens_used += block.token_count
            else:
                excluded.append(block)

        # Sort included back into correct order
        included_sorted = sorted(
            included,
            key=lambda b: (
                self.LAYER_ORDER.index(b.layer) if b.layer in self.LAYER_ORDER else 99,
                b.priority,
            ),
        )

        # Build OpenAI-format messages
        messages = []
        system_parts = [b.content for b in included_sorted if b.layer == "system"]
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        for block in included_sorted:
            if block.layer in ("knowledge", "user", "history"):
                messages.append(
                    {"role": "system", "content": f"[{block.name.upper()}]\n{block.content}"}
                )

        request_parts = [b.content for b in included_sorted if b.layer == "request"]
        if request_parts:
            messages.append({"role": "user", "content": "\n".join(request_parts)})

        report = {
            "token_budget": self.token_budget,
            "tokens_used": tokens_used,
            "tokens_available": self.token_budget - tokens_used,
            "blocks_included": len(included),
            "blocks_excluded": len(excluded),
            "excluded_blocks": [b.name for b in excluded],
        }

        return {"messages": messages, "report": report}


def build_customer_support_context(user_query: str, token_budget: int = 4096) -> dict:
    pipeline = ContextPipeline(token_budget=token_budget)

    # System layer — static, authored by engineering team
    pipeline.add_block(
        ContextBlock(
            name="system_role",
            content=(
                "You are a senior customer support specialist for NovaSaaS. "
                "You help customers with billing, account management, and technical issues. "
                "Always be professional, concise, and accurate. "
                "If you cannot resolve an issue, escalate by saying: ESCALATE: <reason>. "
                "Never reveal internal system architecture or pricing formulas."
            ),
            priority=1,
            layer="system",
        )
    )

    pipeline.add_block(
        ContextBlock(
            name="output_format",
            content=(
                "Respond in plain prose. Do not use markdown unless the user requests it. "
                "For technical steps, use numbered lists. Limit responses to 200 words unless "
                "the issue requires more detail."
            ),
            priority=2,
            layer="system",
        )
    )

    # User context layer — loaded from user profile database
    pipeline.add_block(
        ContextBlock(
            name="user_profile",
            content=(
                "User: Jordan Mehta (jordan.mehta@example.com)\n"
                "Account tier: Professional (since 2023-03)\n"
                "Active subscriptions: Analytics Pro, API Access (10K calls/day)\n"
                "Last login: 2026-07-25\n"
                "Open tickets: None\n"
                "Payment method: Visa ending 4821 (valid)"
            ),
            priority=1,
            layer="user",
        )
    )

    # Knowledge layer — retrieved from knowledge base
    pipeline.add_block(
        ContextBlock(
            name="kb_api_limits",
            content=(
                "Knowledge Article: API Rate Limits (updated 2026-06-01)\n"
                "Professional tier: 10,000 API calls per day. Resets at 00:00 UTC. "
                "Overage: $0.002 per call above limit. Rate limit errors return HTTP 429. "
                "To increase limits, upgrade to Enterprise tier or purchase add-on packs."
            ),
            priority=1,
            layer="knowledge",
        )
    )

    pipeline.add_block(
        ContextBlock(
            name="kb_billing_faq",
            content=(
                "Knowledge Article: Billing FAQ (updated 2026-05-15)\n"
                "Invoices are generated on the 1st of each month. "
                "Payment is auto-charged on the 5th. "
                "Disputed charges must be submitted within 30 days."
            ),
            priority=2,
            layer="knowledge",
        )
    )

    # History layer — last 2 conversation turns
    pipeline.add_block(
        ContextBlock(
            name="conversation_history",
            content=(
                "TURN 1\nUser: Hi, I'm getting 429 errors on my API calls.\n"
                "Assistant: Hello Jordan! A 429 error means you've hit your API rate limit. "
                "Professional accounts receive 10,000 calls per day. Can you tell me when "
                "the errors started?\n\n"
                "TURN 2\nUser: They started around 3pm UTC today."
            ),
            priority=1,
            layer="history",
        )
    )

    # Request layer — current user message
    pipeline.add_block(
        ContextBlock(name="current_message", content=user_query, priority=1, layer="request")
    )

    return pipeline.assemble()


if __name__ == "__main__":
    import json

    result = build_customer_support_context(
        "Is there a way to check how many API calls I've used today?"
    )

    print("=== ASSEMBLED CONTEXT (OpenAI message format) ===")
    for i, msg in enumerate(result["messages"]):
        print(f"\n[Message {i + 1}] role={msg['role']}")
        print(msg["content"][:300] + ("..." if len(msg["content"]) > 300 else ""))

    print("\n=== TOKEN UTILIZATION REPORT ===")
    print(json.dumps(result["report"], indent=2))
