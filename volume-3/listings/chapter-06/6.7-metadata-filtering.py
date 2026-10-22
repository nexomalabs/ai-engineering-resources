# Applied AI Engineering, Volume III, Chapter 6
# Section 6.7, Metadata Filtering
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class FilteredRetriever:
    """Dense retrieval with metadata filtering."""

    def __init__(self, corpus: list[dict], model_name: str = "all-MiniLM-L6-v2"):
        """
        corpus: list of dicts with 'text' and 'metadata' keys
        e.g. [{"text": "...", "metadata": {"version": "2.0", "lang": "en"}}]
        """
        self.corpus = corpus
        self.model = SentenceTransformer(model_name)
        texts = [d["text"] for d in corpus]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, filters: dict, k: int = 5) -> list[dict]:
        """Retrieve and apply metadata filters."""
        query_emb = self.model.encode([query], normalize_embeddings=True).astype(np.float32)
        # Over-retrieve to account for filter removal
        scores, indices = self.index.search(query_emb, k * 4)
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            doc = self.corpus[idx]
            meta = doc.get("metadata", {})
            # Apply all filter constraints
            if all(meta.get(key) == val for key, val in filters.items()):
                results.append({
                    "text": doc["text"],
                    "metadata": meta,
                    "score": float(scores[0][rank]),
                })
            if len(results) >= k:
                break
        return results
