# Applied AI Engineering, Volume III, Chapter 6
# Section 6.7, Metadata Filtering
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class FilteredRetriever:
    """Dense retrieval with metadata pre-filtering."""

    def __init__(self, corpus: list[dict], model_name: str = "all-MiniLM-L6-v2"):
        """
        corpus: list of dicts with 'text' and 'metadata' keys
        e.g. [{"text": "...", "metadata": {"version": "2.0", "lang": "en"}}]
        """
        self.corpus = corpus
        self.model = SentenceTransformer(model_name)
        texts = [d["text"] for d in corpus]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True).astype(np.float32)

    def search(self, query: str, filters: dict, k: int = 5) -> list[dict]:
        """Apply the metadata filters first, then rank only the documents that pass."""
        allowed = [
            i for i, doc in enumerate(self.corpus)
            if all(doc.get("metadata", {}).get(key) == val for key, val in filters.items())
        ]
        if not allowed:
            return []
        query_emb = self.model.encode([query], normalize_embeddings=True).astype(np.float32)[0]
        scores = self.embeddings[allowed] @ query_emb  # Normalized vectors: dot product = cosine
        top = np.argsort(scores)[::-1][:k]
        return [
            {
                "text": self.corpus[allowed[j]]["text"],
                "metadata": self.corpus[allowed[j]].get("metadata", {}),
                "score": float(scores[j]),
            }
            for j in top
        ]
