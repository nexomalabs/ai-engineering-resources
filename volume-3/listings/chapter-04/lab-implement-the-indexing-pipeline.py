# Applied AI Engineering, Volume III, Chapter 4
# Hands-on Lab: Minimal RAG System in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class RAGIndexer:
    """Encodes documents and builds the in-memory vector index."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.documents: List[RAGDocument] = []

    def index(self, knowledge_base: list) -> None:
        texts = [item["text"] for item in knowledge_base]
        print(f"Encoding {len(texts)} documents...")
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

        for item, emb in zip(knowledge_base, embeddings):
            doc = RAGDocument(
                doc_id=item["id"],
                source=item["source"],
                text=item["text"],
                embedding=emb
            )
            self.documents.append(doc)
        print(f"Indexed {len(self.documents)} documents.")

    def get_embeddings_matrix(self) -> np.ndarray:
        return np.stack([d.embedding for d in self.documents])
