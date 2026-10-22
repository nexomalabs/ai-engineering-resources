# Applied AI Engineering, Volume III, Chapter 6
# Section 6.8, Cross-Encoder Reranking
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from sentence_transformers import CrossEncoder

class TwoStageRetriever:
    """Bi-encoder retrieval followed by cross-encoder reranking."""

    def __init__(
        self,
        bi_encoder_name: str = "all-MiniLM-L6-v2",
        cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.bi_encoder = SentenceTransformer(bi_encoder_name)
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        self.index = None
        self.corpus = []

    def build_index(self, corpus: list[str]) -> None:
        self.corpus = corpus
        embeddings = self.bi_encoder.encode(corpus, normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, k: int = 5, candidates: int = 50) -> list[dict]:
        """Retrieve candidates with bi-encoder, rerank with cross-encoder."""
        # Stage 1: Bi-encoder retrieval
        query_emb = self.bi_encoder.encode([query], normalize_embeddings=True).astype(np.float32)
        _, indices = self.index.search(query_emb, min(candidates, len(self.corpus)))
        candidate_docs = [self.corpus[i] for i in indices[0] if i >= 0]

        # Stage 2: Cross-encoder reranking
        pairs = [[query, doc] for doc in candidate_docs]
        cross_scores = self.cross_encoder.predict(pairs)
        ranked = sorted(
            zip(candidate_docs, cross_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            {"doc": doc, "cross_score": float(score), "rank": i + 1}
            for i, (doc, score) in enumerate(ranked[:k])
        ]
