# Applied AI Engineering, Volume III, Chapter 7
# Section 7.4, Abstractive Compression
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def abstractive_compress(
    context: str,
    query: str,
    target_tokens: int,
    llm_client,
) -> str:
    """Compress context using an LLM to generate a query-focused summary."""
    prompt = f"""You are a precise summarizer. Your task is to compress the following
context into approximately {target_tokens} tokens, retaining ONLY information
relevant to answering the question below.

CRITICAL RULES:
- Do NOT add information not present in the context.
- Do NOT change facts, numbers, or names.
- Preserve all information directly relevant to the question.
- Write in complete sentences.
- Aim for exactly {target_tokens} tokens.

QUESTION: {query}

CONTEXT:
{context}

COMPRESSED CONTEXT (query-focused, ~{target_tokens} tokens):"""

    return llm_client.complete(prompt)
