# rag_system.py
import textwrap
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# ── Knowledge base: 12 technical passages ──────────────────────────────────
KNOWLEDGE_BASE = [
    {
        "id": "kb001",
        "source": "Python Docs",
        "text": "Python uses indentation to define code blocks. A block starts with a colon "
        "and all statements in the block must be indented by the same amount. "
        "The standard is four spaces per level of indentation.",
    },
    {
        "id": "kb002",
        "source": "Python Docs",
        "text": "List comprehensions provide a concise way to create lists. The syntax is "
        "[expression for item in iterable if condition]. They are more readable and "
        "often faster than equivalent for-loop constructions.",
    },
    {
        "id": "kb003",
        "source": "REST API Guide",
        "text": "HTTP GET requests retrieve data without modifying server state. They should "
        "be idempotent: calling GET multiple times should produce the same result. "
        "Query parameters are appended after the URL as ?key=value pairs.",
    },
    {
        "id": "kb004",
        "source": "REST API Guide",
        "text": "HTTP POST requests send data to a server to create a new resource. The "
        "request body typically contains JSON or form data. Successful creation "
        "returns HTTP status 201 Created with a Location header.",
    },
    {
        "id": "kb005",
        "source": "Security Guide",
        "text": "JWT (JSON Web Token) consists of three base64url-encoded parts: header, "
        "payload, and signature. The header specifies the algorithm (e.g., HS256). "
        "The payload contains claims. The signature verifies the token's integrity.",
    },
    {
        "id": "kb006",
        "source": "Security Guide",
        "text": "Access tokens should be short-lived (15–60 minutes). Refresh tokens are "
        "long-lived (days to weeks) and used to obtain new access tokens. Store "
        "refresh tokens in httpOnly cookies to prevent JavaScript access.",
    },
    {
        "id": "kb007",
        "source": "Database Guide",
        "text": "An index in a relational database is a data structure that improves the "
        "speed of data retrieval. B-tree indexes are the default in PostgreSQL and "
        "MySQL. They support equality and range queries efficiently.",
    },
    {
        "id": "kb008",
        "source": "Database Guide",
        "text": "A database transaction groups multiple operations into a single atomic unit. "
        "ACID properties ensure Atomicity, Consistency, Isolation, and Durability. "
        "Use BEGIN TRANSACTION ... COMMIT to wrap related operations.",
    },
    {
        "id": "kb009",
        "source": "Docker Guide",
        "text": "A Docker image is a read-only template containing an application and its "
        "dependencies. Images are built from a Dockerfile using `docker build`. "
        "Each instruction in the Dockerfile creates a new image layer.",
    },
    {
        "id": "kb010",
        "source": "Docker Guide",
        "text": "Docker volumes persist data outside container lifecycles. Use "
        "`docker run -v /host/path:/container/path` to mount a host directory. "
        "Named volumes are managed by Docker and preferred for production.",
    },
    {
        "id": "kb011",
        "source": "Git Guide",
        "text": "Git rebase moves or combines commits onto a new base commit. Unlike merge, "
        "rebase rewrites commit history producing a linear project history. "
        "Use `git rebase main` from a feature branch to incorporate upstream changes.",
    },
    {
        "id": "kb012",
        "source": "Git Guide",
        "text": "Git stash temporarily shelves changes not yet ready to commit. "
        "Use `git stash push -m 'description'` to save and `git stash pop` to restore. "
        "Stashes are stored as a stack; `git stash list` shows all saved stashes.",
    },
]


@dataclass
class RAGDocument:
    doc_id: str
    source: str
    text: str
    embedding: np.ndarray = field(repr=False, default=None)


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
                doc_id=item["id"], source=item["source"], text=item["text"], embedding=emb
            )
            self.documents.append(doc)
        print(f"Indexed {len(self.documents)} documents.")

    def get_embeddings_matrix(self) -> np.ndarray:
        return np.stack([d.embedding for d in self.documents])


class RAGRetriever:
    """Retrieves relevant documents using cosine similarity."""

    def __init__(self, indexer: RAGIndexer):
        self.indexer = indexer
        self.doc_matrix = indexer.get_embeddings_matrix()

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[RAGDocument, float]]:
        query_emb = self.indexer.model.encode([query], normalize_embeddings=True)[0]

        # TODO 1: score every document against the query and keep the top_k.
        # The embeddings are normalized, so the dot product is the cosine similarity.
        #
        #   scores = self.doc_matrix @ query_emb
        #   top_indices = np.argsort(scores)[::-1][:top_k]
        scores = np.zeros(len(self.indexer.documents))
        top_indices = list(range(top_k))

        results = []
        for idx in top_indices:
            doc = self.indexer.documents[idx]
            score = float(scores[idx])
            results.append((doc, score))

        return results


def mock_llm_call(prompt: str) -> str:
    """
    Mock LLM call that returns a plausible answer based on the prompt content.
    In production, replace with: openai.chat.completions.create(...)
    """
    # Extract the question from the prompt
    if "USER QUESTION" in prompt:
        question_start = prompt.find("USER QUESTION\n") + len("USER QUESTION\n")
        question = prompt[question_start:].strip().split("\n")[0]
    else:
        question = "the question"

    # Extract source citations for the mock response
    sources_in_prompt = []
    for i, line in enumerate(prompt.split("\n")):
        if line.startswith("[") and "]" in line[:5]:
            source_part = line.split("]")[0].replace("[", "")
            sources_in_prompt.append(source_part)

    sources_str = (
        ", ".join([f"[{s}]" for s in sources_in_prompt[:2]]) if sources_in_prompt else "[1]"
    )
    return (
        f"Based on the retrieved context, {question.lower().rstrip('?')} "
        f"is addressed in the knowledge base as follows: "
        f"The relevant technical details are provided in {sources_str}. "
        f"[Mock response — replace mock_llm_call() with a real LLM API call for production.]"
    )


class RAGGenerator:
    """Assembles context and generates an answer."""

    SYSTEM_PROMPT = (
        "You are a precise technical assistant. Answer the user's question based "
        "solely on the provided retrieved context. Cite sources by their reference "
        "numbers [1], [2], etc. If the answer is not in the context, say: "
        "'I don't have that information in my knowledge base.'"
    )

    def generate(self, query: str, retrieved: List[Tuple[RAGDocument, float]]) -> dict:
        context_lines = []
        # TODO 2: number each retrieved passage so the model can cite it:
        #   f"[{i}] Source: {doc.source}\n{doc.text}" for i = 1, 2, 3, ...
        for doc, score in retrieved:
            context_lines.append(doc.text)

        context_block = "\n\n".join(context_lines)

        prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"## RETRIEVED CONTEXT\n\n{context_block}\n\n"
            f"## USER QUESTION\n{query}"
        )

        answer = mock_llm_call(prompt)

        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "rank": i,
                    "id": doc.doc_id,
                    "source": doc.source,
                    "score": round(score, 4),
                    "text": doc.text[:80] + "...",
                }
                for i, (doc, score) in enumerate(retrieved, start=1)
            ],
        }


def run_rag_demo():
    # ── Index the knowledge base ──────────────────────────────────────────
    indexer = RAGIndexer(model_name="all-MiniLM-L6-v2")
    indexer.index(KNOWLEDGE_BASE)

    retriever = RAGRetriever(indexer)
    generator = RAGGenerator()

    # ── Run queries ──────────────────────────────────────────────────────
    test_queries = [
        "How does JWT token authentication work?",
        "What is the difference between GET and POST requests?",
        "How do I persist data in Docker containers?",
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print("=" * 60)

        retrieved = retriever.retrieve(query, top_k=3)
        result = generator.generate(query, retrieved)

        print(f"\nANSWER:\n{textwrap.fill(result['answer'], width=70)}")
        print("\nSOURCES:")
        for src in result["sources"]:
            print(f"  [{src['rank']}] {src['source']} (score={src['score']})")
            print(f"       {src['text']}")


if __name__ == "__main__":
    run_rag_demo()
