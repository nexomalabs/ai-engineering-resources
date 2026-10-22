# Applied AI Engineering, Volume III, Chapter 6
# Section 6.10, Evaluation Metrics
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def recall_at_k(relevant: set, retrieved: list, k: int) -> float:
    retrieved_k = set(retrieved[:k])
    if not relevant:
        return 0.0
    return len(relevant & retrieved_k) / len(relevant)

def mrr(relevant: set, retrieved: list) -> float:
    for rank, doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0

def ndcg_at_k(relevant: dict, retrieved: list, k: int) -> float:
    """
    relevant: dict mapping doc_id -> relevance_grade (e.g. 0, 1, 2)
    retrieved: list of doc_ids in ranked order
    """
    def dcg(ranked_docs):
        return sum(
            (2 ** relevant.get(doc, 0) - 1) / np.log2(i + 2)
            for i, doc in enumerate(ranked_docs[:k])
        )
    ideal = sorted(relevant.values(), reverse=True)[:k]
    ideal_dcg = sum((2 ** r - 1) / np.log2(i + 2) for i, r in enumerate(ideal))
    return dcg(retrieved) / ideal_dcg if ideal_dcg > 0 else 0.0
