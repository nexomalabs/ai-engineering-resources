# Applied AI Engineering, Volume III, Chapter 4
# Hands-on Lab: Minimal RAG System in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

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

    sources_str = ", ".join([f"[{s}]" for s in sources_in_prompt[:2]]) if sources_in_prompt else "[1]"
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

    def generate(self, query: str,
                 retrieved: List[Tuple[RAGDocument, float]]) -> dict:
        context_lines = []
        for i, (doc, score) in enumerate(retrieved, start=1):
            context_lines.append(f"[{i}] Source: {doc.source}\n{doc.text}")

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
                {"rank": i, "id": doc.doc_id, "source": doc.source,
                 "score": round(score, 4), "text": doc.text[:80] + "..."}
                for i, (doc, score) in enumerate(retrieved, start=1)
            ]
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
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print('='*60)

        retrieved = retriever.retrieve(query, top_k=3)
        result = generator.generate(query, retrieved)

        print(f"\nANSWER:\n{textwrap.fill(result['answer'], width=70)}")
        print(f"\nSOURCES:")
        for src in result["sources"]:
            print(f"  [{src['rank']}] {src['source']} (score={src['score']})")
            print(f"       {src['text']}")


if __name__ == "__main__":
    run_rag_demo()
