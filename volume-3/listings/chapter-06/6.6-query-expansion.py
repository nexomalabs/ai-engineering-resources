# Applied AI Engineering, Volume III, Chapter 6
# Section 6.6, Query Expansion
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def expand_query_with_llm(query: str, llm_client) -> list[str]:
    """
    Generate query expansions using an LLM.
    Returns the original query plus 3-5 alternative formulations.
    """
    prompt = f"""Given the search query: "{query}"

Generate 4 alternative phrasings that capture the same intent but use
different terminology. Return one per line, no numbering.

Original query intent: {query}
Alternative phrasings:"""

    response = llm_client.complete(prompt)
    expansions = [line.strip() for line in response.split('\n') if line.strip()]
    return [query] + expansions[:4]

def expanded_search(query: str, retriever, llm_client, k: int = 10) -> list[dict]:
    """Search with query expansion and merge results."""
    queries = expand_query_with_llm(query, llm_client)
    all_results = {}
    for q in queries:
        for result in retriever.search(q, k=k):
            doc_key = result["doc"]
            if doc_key not in all_results or result["score"] > all_results[doc_key]["score"]:
                all_results[doc_key] = result
    return sorted(all_results.values(), key=lambda x: x["score"], reverse=True)[:k]
