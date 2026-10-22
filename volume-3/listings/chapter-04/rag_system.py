# Applied AI Engineering, Volume III, Chapter 4
# Hands-on Lab: Minimal RAG System in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# rag_system.py
import numpy as np
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass, field
from typing import List, Tuple
import textwrap


# ── Knowledge base: 12 technical passages ──────────────────────────────────
KNOWLEDGE_BASE = [
    {"id": "kb001", "source": "Python Docs", "text":
     "Python uses indentation to define code blocks. A block starts with a colon "
     "and all statements in the block must be indented by the same amount. "
     "The standard is four spaces per level of indentation."},
    {"id": "kb002", "source": "Python Docs", "text":
     "List comprehensions provide a concise way to create lists. The syntax is "
     "[expression for item in iterable if condition]. They are more readable and "
     "often faster than equivalent for-loop constructions."},
    {"id": "kb003", "source": "REST API Guide", "text":
     "HTTP GET requests retrieve data without modifying server state. They should "
     "be idempotent: calling GET multiple times should produce the same result. "
     "Query parameters are appended after the URL as ?key=value pairs."},
    {"id": "kb004", "source": "REST API Guide", "text":
     "HTTP POST requests send data to a server to create a new resource. The "
     "request body typically contains JSON or form data. Successful creation "
     "returns HTTP status 201 Created with a Location header."},
    {"id": "kb005", "source": "Security Guide", "text":
     "JWT (JSON Web Token) consists of three base64url-encoded parts: header, "
     "payload, and signature. The header specifies the algorithm (e.g., HS256). "
     "The payload contains claims. The signature verifies the token's integrity."},
    {"id": "kb006", "source": "Security Guide", "text":
     "Access tokens should be short-lived (15–60 minutes). Refresh tokens are "
     "long-lived (days to weeks) and used to obtain new access tokens. Store "
     "refresh tokens in httpOnly cookies to prevent JavaScript access."},
    {"id": "kb007", "source": "Database Guide", "text":
     "An index in a relational database is a data structure that improves the "
     "speed of data retrieval. B-tree indexes are the default in PostgreSQL and "
     "MySQL. They support equality and range queries efficiently."},
    {"id": "kb008", "source": "Database Guide", "text":
     "A database transaction groups multiple operations into a single atomic unit. "
     "ACID properties ensure Atomicity, Consistency, Isolation, and Durability. "
     "Use BEGIN TRANSACTION ... COMMIT to wrap related operations."},
    {"id": "kb009", "source": "Docker Guide", "text":
     "A Docker image is a read-only template containing an application and its "
     "dependencies. Images are built from a Dockerfile using `docker build`. "
     "Each instruction in the Dockerfile creates a new image layer."},
    {"id": "kb010", "source": "Docker Guide", "text":
     "Docker volumes persist data outside container lifecycles. Use "
     "`docker run -v /host/path:/container/path` to mount a host directory. "
     "Named volumes are managed by Docker and preferred for production."},
    {"id": "kb011", "source": "Git Guide", "text":
     "Git rebase moves or combines commits onto a new base commit. Unlike merge, "
     "rebase rewrites commit history producing a linear project history. "
     "Use `git rebase main` from a feature branch to incorporate upstream changes."},
    {"id": "kb012", "source": "Git Guide", "text":
     "Git stash temporarily shelves changes not yet ready to commit. "
     "Use `git stash push -m 'description'` to save and `git stash pop` to restore. "
     "Stashes are stored as a stack; `git stash list` shows all saved stashes."},
]


@dataclass
class RAGDocument:
    doc_id: str
    source: str
    text: str
    embedding: np.ndarray = field(repr=False, default=None)
