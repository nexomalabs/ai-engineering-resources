# Applied AI Engineering, Volume III, Chapter 6
# Section 6.4, Dense Retrieval with Embeddings
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class DenseRetriever:
    """Dense retrieval using sentence-transformers + FAISS."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.corpus = []

    def build_index(self, corpus: list[str]) -> None:
        """Encode all documents and build a FAISS flat index."""
        self.corpus = corpus
        embeddings = self.model.encode(
            corpus,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner product on normalized = cosine
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Retrieve top-k documents using dense similarity search."""
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index() first.")
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        scores, indices = self.index.search(query_embedding, k)
        return [
            {
                "doc": self.corpus[idx],
                "score": float(scores[0][rank]),
                "rank": rank + 1,
            }
            for rank, idx in enumerate(indices[0])
            if idx >= 0
        ]
