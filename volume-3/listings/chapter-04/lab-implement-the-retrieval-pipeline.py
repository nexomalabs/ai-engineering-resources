# Applied AI Engineering, Volume III, Chapter 4
# Hands-on Lab: Minimal RAG System in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class RAGRetriever:
    """Retrieves relevant documents using cosine similarity."""

    def __init__(self, indexer: RAGIndexer):
        self.indexer = indexer
        self.doc_matrix = indexer.get_embeddings_matrix()

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[RAGDocument, float]]:
        query_emb = self.indexer.model.encode(
            [query], normalize_embeddings=True
        )[0]

        # Cosine similarity: since vectors are normalized, dot product == cosine similarity
        scores = self.doc_matrix @ query_emb

        # Get top-K indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            doc = self.indexer.documents[idx]
            score = float(scores[idx])
            results.append((doc, score))

        return results
