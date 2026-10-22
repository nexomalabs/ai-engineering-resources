# Applied AI Engineering, Volume III, Chapter 7
# Section 7.8, Compression Evaluation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def evaluate_compression(
    original: str,
    compressed: str,
    query: str,
    answer: str,
    qa_system,
) -> dict:
    """Measure compression quality on a QA benchmark."""
    original_tokens = estimate_tokens(original)
    compressed_tokens = estimate_tokens(compressed)
    compression_ratio = 1 - (compressed_tokens / original_tokens)

    # Answer accuracy with original vs. compressed context
    answer_with_original = qa_system.answer(query, original)
    answer_with_compressed = qa_system.answer(query, compressed)

    exact_match_original = answer.lower() in answer_with_original.lower()
    exact_match_compressed = answer.lower() in answer_with_compressed.lower()

    return {
        "compression_ratio": round(compression_ratio, 3),
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "accuracy_preserved": exact_match_compressed,
        "accuracy_with_full": exact_match_original,
    }
