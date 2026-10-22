# Applied AI Engineering, Volume III, Chapter 6
# Section 6.3, BM25 and Keyword Search
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from rank_bm25 import BM25Okapi
import numpy as np

def build_bm25_index(corpus: list[str]) -> BM25Okapi:
    """Build a BM25 index from a list of documents."""
    tokenized = [doc.lower().split() for doc in corpus]
    return BM25Okapi(tokenized)

def bm25_search(bm25: BM25Okapi, query: str, corpus: list[str], k: int = 5) -> list[dict]:
    """Retrieve top-k documents using BM25."""
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:k]
    return [
        {"doc": corpus[i], "score": float(scores[i]), "rank": rank + 1}
        for rank, i in enumerate(top_indices)
        if scores[i] > 0
    ]

# Example usage
corpus = [
    "Machine learning algorithms improve with more training data.",
    "Deep neural networks require significant computational resources.",
    "Natural language processing enables machines to understand text.",
    "Retrieval-augmented generation combines search with language models.",
    "Vector databases store high-dimensional embeddings for fast search.",
    "BM25 is a probabilistic ranking function for information retrieval.",
    "Transformer architectures use self-attention mechanisms.",
    "Fine-tuning adapts pretrained models to specific domains.",
]

bm25 = build_bm25_index(corpus)
results = bm25_search(bm25, "language model retrieval search", corpus, k=3)
for r in results:
    print(f"Rank {r['rank']} (score={r['score']:.3f}): {r['doc'][:60]}...")
