"""Lab 5 — Vector Index with FAISS (reference solution).

Encodes 15 passages, indexes them in an exact flat index and an approximate HNSW index,
and compares results, recall and timing. The first run downloads the all-MiniLM-L6-v2
embedding model (about 90 MB). Writes corpus.index to the folder you run it from.

    python solution/lab.py
"""

# faiss_demo.py
import time

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

CORPUS = [
    "Python list comprehensions create lists concisely using bracket notation.",
    "Decorators in Python wrap functions to extend behavior without modification.",
    "The Global Interpreter Lock (GIL) in CPython limits true parallelism for CPU-bound code.",
    "asyncio enables concurrent I/O in Python using async/await syntax.",
    "REST APIs use HTTP verbs: GET retrieves data, POST creates, PUT replaces, DELETE removes.",
    "GraphQL allows clients to request exactly the data fields they need.",
    "OAuth 2.0 delegates authorization using access tokens without exposing credentials.",
    "TLS 1.3 provides transport layer security with reduced handshake latency.",
    "Docker images are immutable; containers are running instances of images.",
    "Kubernetes orchestrates containerized workloads across a cluster of nodes.",
    "B-tree indexes in relational databases support efficient equality and range queries.",
    "Redis is an in-memory key-value store commonly used for caching and session storage.",
    "CAP theorem states a distributed system can guarantee only two of: Consistency, Availability, Partition tolerance.",
    "Vector databases store high-dimensional embeddings and support approximate nearest-neighbor search.",
    "Transformer attention allows every token to attend to every other token in the input sequence.",
]

print(f"Corpus size: {len(CORPUS)} passages")


def encode_corpus(
    corpus: list[str], model_name: str = "all-MiniLM-L6-v2"
) -> tuple[np.ndarray, SentenceTransformer]:
    """Encode corpus to L2-normalized float32 vectors; also return the model."""
    print(f"\nLoading model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"Encoding {len(corpus)} passages...")
    embeddings = model.encode(
        corpus,
        normalize_embeddings=True,  # L2 normalize → dot product == cosine sim
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    print(f"Embeddings shape: {embeddings.shape} (dtype={embeddings.dtype})")
    return embeddings.astype(np.float32), model


def build_flat_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Flat inner product index. Since embeddings are L2-normalized,
    inner product == cosine similarity.
    """
    dims = embeddings.shape[1]
    index = faiss.IndexFlatIP(dims)
    index.add(embeddings)
    print(f"\n[Flat Index] Built. Total vectors: {index.ntotal}")
    return index


def build_hnsw_index(
    embeddings: np.ndarray, M: int = 32, ef_construction: int = 200
) -> faiss.IndexHNSWFlat:
    """
    HNSW index for fast approximate search.
    M: number of connections per node (higher = better recall, more memory)
    ef_construction: search width during index build (higher = better recall)
    """
    dims = embeddings.shape[1]
    index = faiss.IndexHNSWFlat(dims, M, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = ef_construction
    index.hnsw.efSearch = 64  # Search width at query time

    print(f"\n[HNSW Index] Building (M={M}, efConstruction={ef_construction})...")
    t0 = time.perf_counter()
    index.add(embeddings)
    build_time = time.perf_counter() - t0
    print(f"[HNSW Index] Built in {build_time * 1000:.1f}ms. Total vectors: {index.ntotal}")
    return index


def search_index(
    index, query: str, model, corpus: list[str], k: int = 3, index_name: str = "Index"
) -> list[dict]:
    """Encode query and search the FAISS index."""
    query_emb = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(
        np.float32
    )

    t0 = time.perf_counter()
    scores, indices = index.search(query_emb, k)
    elapsed_us = (time.perf_counter() - t0) * 1_000_000

    print(f"\n[{index_name}] Query: '{query}'  ({elapsed_us:.1f} µs)")
    results = []
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
        if idx == -1:  # FAISS returns -1 for unfilled slots
            continue
        result = {
            "rank": rank,
            "score": round(float(score), 4),
            "passage": corpus[idx],
            "passage_id": idx,
        }
        results.append(result)
        print(f"  {rank}. [score={result['score']:.4f}] {corpus[idx][:80]}...")

    return results


def compute_recall(flat_results: list, hnsw_results: list) -> float:
    """Compute recall@K of HNSW relative to flat (exact) ground truth."""
    flat_ids = {r["passage_id"] for r in flat_results}
    hnsw_ids = {r["passage_id"] for r in hnsw_results}
    return len(flat_ids & hnsw_ids) / len(flat_ids) if flat_ids else 0.0


def run_demo():
    embeddings, model = encode_corpus(CORPUS)

    flat_index = build_flat_index(embeddings)
    hnsw_index = build_hnsw_index(embeddings, M=16, ef_construction=100)

    test_queries = [
        "How does Python handle concurrent programming?",
        "What is the difference between Docker and Kubernetes?",
        "How do vector databases support semantic search?",
        "What security protocol protects data in transit?",
    ]

    print("\n" + "=" * 70)
    print("RETRIEVAL COMPARISON: FLAT (exact) vs. HNSW (approximate)")
    print("=" * 70)

    total_recall = 0.0
    for query in test_queries:
        print(f"\n{'─' * 70}")
        flat_results = search_index(
            flat_index, query, model, CORPUS, k=3, index_name="FLAT (exact)"
        )
        hnsw_results = search_index(
            hnsw_index, query, model, CORPUS, k=3, index_name="HNSW (approx)"
        )
        recall = compute_recall(flat_results, hnsw_results)
        total_recall += recall
        print(f"  Recall@3 (HNSW vs Flat): {recall:.1%}")

    print(f"\n{'=' * 70}")
    print(
        f"Average Recall@3 across {len(test_queries)} queries: "
        f"{total_recall / len(test_queries):.1%}"
    )

    # ── Index metadata ─────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("INDEX STATISTICS")
    print(f"Flat index: {flat_index.ntotal} vectors, {embeddings.shape[1]} dims")
    print(f"HNSW index: {hnsw_index.ntotal} vectors, M=16, efSearch=64")
    flat_mem = flat_index.ntotal * embeddings.shape[1] * 4 / 1024
    print(f"Flat memory (approx): {flat_mem:.1f} KB")

    # ── Save and reload index ──────────────────────────────────────────
    print("\nSaving HNSW index to disk...")
    faiss.write_index(hnsw_index, "corpus.index")
    reloaded = faiss.read_index("corpus.index")
    print(f"Reloaded index has {reloaded.ntotal} vectors.")


if __name__ == "__main__":
    run_demo()
