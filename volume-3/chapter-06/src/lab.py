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
    # Wrenfield's route service bulletins, from the chapter's opening story
    "Route R-471 service bulletin: road repairs are causing delivery delays of up to two "
    "days until the works finish.",  # 15
    "Route R-417 service bulletin: the Harbour Street stop moves to the north entrance.",  # 16
    "Route R-147 service bulletin: the evening collection moves to 18:00.",  # 17
    "Route R-714 service bulletin: Saturday deliveries resume next week.",  # 18
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
    {
        "query": "is route R-417 delayed",  # the customer's question in the story
        "relevant": {16},
    },
    {
        "query": "when do route R-471 repairs finish",
        "relevant": {15},
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
def mrr(relevant: set, retrieved: list[int]) -> float:
    """Reciprocal rank of the first relevant document: 1.0 if it comes first."""
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(relevant: set, retrieved: list[int], k: int) -> float:
    # TODO 2: Recall is the share of the RELEVANT documents found in the top k, so
    #   divide by len(relevant), not by k. Return 0.0 if nothing is relevant.
    return len(relevant & set(retrieved[:k])) / k


def verdict(metric: str, scores: dict[str, list[float]]) -> str:
    """Say what the numbers show, rather than asserting a result in advance."""
    best_single = max(np.mean(scores["BM25"]), np.mean(scores["Dense"]))
    hybrid = np.mean(scores["Hybrid"])
    if np.isclose(hybrid, best_single):
        return f"By {metric}, hybrid retrieval matches the better single method."
    if hybrid > best_single:
        return f"By {metric}, hybrid retrieval beats both single methods."
    return f"By {metric}, hybrid retrieval trails the better single method."


def evaluate(corpus, test_queries, k=K):
    # Build indexes
    bm25 = build_bm25(corpus)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dense_index = build_dense_index(corpus, model)

    methods = ("BM25", "Dense", "Hybrid")
    recalls = {m: [] for m in methods}
    mrrs = {m: [] for m in methods}

    def row(label: str, first: list[float], second: list[float]) -> str:
        cells = (
            " ".join(f"{v:>6.2f}" for v in first) + "   " + " ".join(f"{v:>6.2f}" for v in second)
        )
        return f"{label:<34} {cells}"

    names = " ".join(f"{m:>6}" for m in methods)
    print()
    print(f"{'':<34} {'Recall@' + str(k):^20}   {'MRR':^20}")
    print(f"{'Query':<34} {names}   {names}")
    print("-" * 78)

    for item in test_queries:
        query = item["query"]
        relevant = item["relevant"]

        bm25_results = bm25_retrieve(bm25, query, k * 2)
        dense_results = dense_retrieve(query, model, dense_index, k * 2)
        hybrid_results = reciprocal_rank_fusion([bm25_results, dense_results])
        ranked = {"BM25": bm25_results, "Dense": dense_results, "Hybrid": hybrid_results}

        for m in methods:
            recalls[m].append(recall_at_k(relevant, ranked[m], k))
            mrrs[m].append(mrr(relevant, ranked[m]))
        print(row(query[:34], [recalls[m][-1] for m in methods], [mrrs[m][-1] for m in methods]))

    print("-" * 78)
    print(row("Mean", [np.mean(recalls[m]) for m in methods], [np.mean(mrrs[m]) for m in methods]))
    print()
    print(verdict(f"Recall@{k}", recalls))
    print(verdict("MRR", mrrs))


if __name__ == "__main__":
    evaluate(CORPUS, TEST_QUERIES, k=K)
