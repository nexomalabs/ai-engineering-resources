# Applied AI Engineering, Volume III, Chapter 1
# Hands-on Lab: Build a Context Pipeline in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

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
        return sorted(
            self.blocks,
            key=lambda b: (layer_index.get(b.layer, 99), b.priority)
        )

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
            key=lambda b: (self.LAYER_ORDER.index(b.layer)
                           if b.layer in self.LAYER_ORDER else 99, b.priority)
        )

        # Build OpenAI-format messages
        messages = []
        system_parts = [b.content for b in included_sorted if b.layer == "system"]
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        for block in included_sorted:
            if block.layer in ("knowledge", "user", "history"):
                messages.append({
                    "role": "system",
                    "content": f"[{block.name.upper()}]\n{block.content}"
                })

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
