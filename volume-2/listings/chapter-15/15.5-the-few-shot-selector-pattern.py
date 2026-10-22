# Applied AI Engineering, Volume II, Chapter 15
# Section 15.5, The Few-Shot Selector Pattern
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def select_examples(query: str, example_pool: list, k: int) -> list:
    """Select k most semantically similar examples from pool."""
    # Embed query
    # Embed all examples
    # Return k nearest neighbors by cosine similarity
    ...

def build_prompt(query: str, selected_examples: list) -> str:
    example_section = "\n\n".join([
        f"Input: {ex['input']}\nOutput: {ex['output']}"
        for ex in selected_examples
    ])
    return f"{example_section}\n\nInput: {query}\nOutput:"
