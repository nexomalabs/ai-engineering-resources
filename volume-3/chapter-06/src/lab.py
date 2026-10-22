"""Lab 6 — Hybrid Retrieval System (starter).

This file RUNS as supplied, but the fusion step just puts BM25's list first, and Recall@K
divides by the wrong number. Complete the two TODOs.

    python src/lab.py
"""

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

# ── Corpus and ground-truth relevance ──────────────────────────────────────
CORPUS = [
    "Python is a high-level programming language known for readability.",  # 0
    "Machine learning enables computers to learn from data automatically.",  # 1
    "Neural networks are computational models inspired by the brain.",  # 2
    "Natural language processing helps machines understand human language.",  # 3
    "Retrieval-augmented generation combines search with text generation.",  # 4
    "Vector databases are optimized for storing and querying embeddings.",  # 5
    "BM25 is a ranking function used in information retrieval systems.",  # 6
    "Transformers use self-attention to model long-range dependencies.",  # 7
    "Fine-tuning adapts a pretrained model to a specific downstream task.",  # 8
    "Embeddings represent text as dense vectors in a continuous space.",  # 9
    "Semantic search finds documents by meaning rather than keyword overlap.",  # 10
    "Contrastive learning trains models by contrasting positive and negative.",  # 11
    "Recall measures the fraction of relevant items that were retrieved.",  # 12
    "Cross-encoders rerank candidate documents with higher accuracy.",  # 13
    "Hybrid search combines sparse and dense retrieval for better results.",  # 14
]

# Test queries with ground-truth relevant document indices
TEST_QUERIES = [
    {
        "query": "how does BM25 work for information retrieval",
        "relevant": {6, 12},
    },
    {
        "query": "semantic search using vector embeddings",
        "relevant": {5, 9, 10, 14},
    },
    {
        "query": "machine learning models trained on data",
        "relevant": {1, 2, 8, 11},
    },
    {
        "query": "language understanding NLP",
        "relevant": {3, 7},
    },
]

K = 5  # Evaluate Recall@5


# ── BM25 Retriever ──────────────────────────────────────────────────────────
def build_bm25(corpus: list[str]) -> BM25Okapi:
    tokenized = [doc.lower().split() for doc in corpus]
    return BM25Okapi(tokenized)


def bm25_retrieve(bm25: BM25Okapi, query: str, k: int) -> list[int]:
    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)
    return list(np.argsort(scores)[::-1][:k])


# ── Dense Retriever ─────────────────────────────────────────────────────────
def build_dense_index(corpus: list[str], model: SentenceTransformer):
    embeddings = model.encode(corpus, normalize_embeddings=True).astype(np.float32)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def dense_retrieve(
    query: str,
    model: SentenceTransformer,
    index: faiss.IndexFlatIP,
    k: int,
) -> list[int]:
    q_emb = model.encode([query], normalize_embeddings=True).astype(np.float32)
    _, indices = index.search(q_emb, k)
    return list(indices[0])


# ── Reciprocal Rank Fusion ──────────────────────────────────────────────────
def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    k: int = 60,
) -> list[int]:
    # TODO 1: Reciprocal rank fusion. Give each document 1 / (k + rank + 1) for every
    #   list it appears in (rank counts from 0), add up its scores, and return the
    #   documents from highest score to lowest.
    fused: list[int] = []
    for ranked in ranked_lists:
        fused += [doc_id for doc_id in ranked if doc_id not in fused]
    return fused


# ── Evaluation ──────────────────────────────────────────────────────────────
def recall_at_k(relevant: set, retrieved: list[int], k: int) -> float:
    # TODO 2: Recall is the share of the RELEVANT documents found in the top k, so
    #   divide by len(relevant), not by k. Return 0.0 if nothing is relevant.
    return len(relevant & set(retrieved[:k])) / k


def evaluate(corpus, test_queries, k=K):
    # Build indexes
    bm25 = build_bm25(corpus)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dense_index = build_dense_index(corpus, model)

    bm25_recalls, dense_recalls, hybrid_recalls = [], [], []

    print(f"\n{'Query':<45} {'BM25':>8} {'Dense':>8} {'Hybrid':>8}")
    print("-" * 73)

    for item in test_queries:
        query = item["query"]
        relevant = item["relevant"]

        bm25_results = bm25_retrieve(bm25, query, k * 2)
        dense_results = dense_retrieve(query, model, dense_index, k * 2)
        hybrid_results = reciprocal_rank_fusion([bm25_results, dense_results])

        r_bm25 = recall_at_k(relevant, bm25_results, k)
        r_dense = recall_at_k(relevant, dense_results, k)
        r_hybrid = recall_at_k(relevant, hybrid_results, k)

        bm25_recalls.append(r_bm25)
        dense_recalls.append(r_dense)
        hybrid_recalls.append(r_hybrid)

        short_query = query[:43]
        print(f"{short_query:<45} {r_bm25:>8.2f} {r_dense:>8.2f} {r_hybrid:>8.2f}")

    print("-" * 73)
    print(
        f"{'Mean Recall@' + str(k):<45} {np.mean(bm25_recalls):>8.2f} "
        f"{np.mean(dense_recalls):>8.2f} {np.mean(hybrid_recalls):>8.2f}"
    )

    # Report what the numbers show, rather than asserting a result in advance
    best_single = max(np.mean(bm25_recalls), np.mean(dense_recalls))
    hybrid = np.mean(hybrid_recalls)
    if np.isclose(hybrid, best_single):
        print("\nHybrid retrieval matches the better single method.")
    elif hybrid > best_single:
        print("\nHybrid retrieval beats both single methods.")
    else:
        print("\nHybrid retrieval trails the better single method.")


if __name__ == "__main__":
    evaluate(CORPUS, TEST_QUERIES, k=K)
