# rag_system.py
import textwrap
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# ── Knowledge base: 12 technical passages and two versions of a shipping policy ──
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
    # The two battery policies from the chapter's opening story. The 2023 policy was
    # superseded, but it is still in the index next to its replacement.
    {
        "id": "kb013",
        "source": "Wrenfield Shipping Policy (2023)",
        "text": "Laptops with lithium batteries may be shipped by air, provided the battery "
        "is installed in the laptop and the parcel carries a lithium battery label.",
        "effective_from": "2023-03-01",
        "superseded_on": "2025-04-01",
    },
    {
        "id": "kb014",
        "source": "Wrenfield Shipping Policy (2025)",
        "text": "Devices containing lithium batteries, including laptops, travel by road "
        "only and are no longer accepted for air shipment. Label every such parcel "
        "with a lithium battery mark.",
        "effective_from": "2025-04-01",
    },
]


@dataclass
class RAGDocument:
    doc_id: str
    source: str
    text: str
    embedding: np.ndarray = field(repr=False, default=None)
    effective_from: Optional[str] = None  # ISO date the document took effect
    superseded_on: Optional[str] = None  # ISO date a newer version replaced it


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
                embedding=emb,
                effective_from=item.get("effective_from"),
                superseded_on=item.get("superseded_on"),
            )
            self.documents.append(doc)
        print(f"Indexed {len(self.documents)} documents.")

    def get_embeddings_matrix(self) -> np.ndarray:
        return np.stack([d.embedding for d in self.documents])


def in_force(doc: RAGDocument, as_of: date) -> bool:
    """True if the document had taken effect by as_of and had not yet been superseded."""
    # TODO 3: return False if the document takes effect after as_of (effective_from) or
    #   was superseded on or before it (superseded_on). Both are ISO date strings or None;
    #   parse them with date.fromisoformat(). As supplied, superseded policies stay
    #   searchable, which is how the 2023 battery policy reached the customer.
    return True


class RAGRetriever:
    """Retrieves relevant documents using cosine similarity."""

    def __init__(self, indexer: RAGIndexer):
        self.indexer = indexer
        self.doc_matrix = indexer.get_embeddings_matrix()

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        as_of: Optional[date] = None,
        in_force_only: bool = True,
    ) -> List[Tuple[RAGDocument, float]]:
        query_emb = self.indexer.model.encode([query], normalize_embeddings=True)[0]

        # TODO 1: score every document against the query.
        # The embeddings are normalized, so the dot product is the cosine similarity.
        #
        #   scores = self.doc_matrix @ query_emb
        scores = np.zeros(len(self.indexer.documents))

        # Filter before ranking: a superseded document is never a candidate at all
        as_of = as_of or date.today()
        candidates = [
            i
            for i, doc in enumerate(self.indexer.documents)
            if not in_force_only or in_force(doc, as_of)
        ]

        # Get top-K indices among the candidates
        top_indices = sorted(candidates, key=lambda i: scores[i], reverse=True)[:top_k]

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


def show(result: dict) -> None:
    print(f"\nANSWER:\n{textwrap.fill(result['answer'], width=70)}")
    print("\nSOURCES:")
    for src in result["sources"]:
        print(f"  [{src['rank']}] {src['source']} (score={src['score']})")
        print(f"       {src['text']}")


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
        show(generator.generate(query, retrieved))

    # ── The story's question, without and with the in-force filter ─────────
    query = "Can I ship a laptop with a lithium battery by air?"
    for in_force_only in (False, True):
        label = "only documents in force today" if in_force_only else "every indexed document"
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print(f"SEARCHING: {label}")
        print("=" * 60)
        retrieved = retriever.retrieve(query, top_k=2, in_force_only=in_force_only)
        show(generator.generate(query, retrieved))


if __name__ == "__main__":
    run_rag_demo()
