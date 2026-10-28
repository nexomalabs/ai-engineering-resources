# Applied AI Engineering, Volume III, Chapter 2
# Section 2.3, Token Counting
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import tiktoken

def count_chat_tokens(messages: list[dict], model: str = "gpt-6.1-sol") -> int:
    """
    Count total tokens for an OpenAI chat completion request.
    Matches the formula from the OpenAI cookbook.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:  # e.g. GPT-6 models, which tiktoken does not map
        encoding = tiktoken.get_encoding("o200k_base")

    # Token overhead varies by model
    tokens_per_message = 3  # every message adds: <|start|>{role}\n{content}<|end|>
    tokens_per_name = 1     # if there is a name field

    total = 0
    for message in messages:
        total += tokens_per_message
        for key, value in message.items():
            total += len(encoding.encode(value))
            if key == "name":
                total += tokens_per_name
    total += 3  # reply primer: <|start|>assistant<|message|>
    return total


# Example usage
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
]
print(f"Total tokens: {count_chat_tokens(messages)}")  # 24 tokens
