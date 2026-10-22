"""Lab 7 — Extractive Context Compression (reference solution).

Compresses a context to a token budget by keeping the sentences most similar to the query.
The first run downloads the all-MiniLM-L6-v2 embedding model (about 90 MB).

    python solution/lab.py
"""

import re

from sentence_transformers import SentenceTransformer

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_NAME = "all-MiniLM-L6-v2"
TOKEN_BUDGET = 400
QUERY = "What are the main evaluation metrics for information retrieval systems?"

# ── Sample long context (about 800 tokens) ──────────────────────────────────
LONG_CONTEXT = """
Information retrieval (IR) is the science of searching for documents, information
within documents, and metadata about documents, as well as searching relational
databases and the World Wide Web. IR systems handle large collections of primarily
unstructured text documents.

The history of information retrieval dates to the 1950s, when early systems
classified documents manually. Gerard Salton developed the SMART system in the
1960s, first at Harvard and then at Cornell, and with it the vector space model
that, combined with TF-IDF term weighting, underpins modern search engines.

Evaluation is central to IR research. The Cranfield experiments in the 1960s
established the use of test collections and systematic evaluation. TREC (Text
Retrieval Conference), organized by NIST since 1992, provides standardized
benchmarks and evaluation tracks.

Precision measures the fraction of retrieved documents that are relevant.
Formally, Precision@K = |Relevant ∩ Retrieved@K| / K. High precision means few
irrelevant documents appear in the results. A search engine that returns only
highly relevant results has high precision.

Recall measures the fraction of all relevant documents that were retrieved.
Formally, Recall@K = |Relevant ∩ Retrieved@K| / |Relevant|. High recall means
few relevant documents are missed. Systems optimized for recall retrieve more
broadly at the cost of including irrelevant results.

There is an inherent tension between precision and recall. The F1 score combines
both into a single metric: F1 = 2 × (Precision × Recall) / (Precision + Recall).

Mean Reciprocal Rank (MRR) measures how highly the first relevant document is
ranked. MRR = (1/|Q|) × Σ (1/rank_q) where rank_q is the rank of the first
relevant document for query q. An MRR of 1.0 means the first result is always
relevant. MRR of 0.5 means the first relevant result is on average at position 2.

Normalized Discounted Cumulative Gain (NDCG) handles graded relevance judgments
where documents may be highly relevant, partially relevant, or irrelevant. DCG@K
sums graded relevance discounted by log position: DCG@K = Σ (2^r_i - 1) / log2(i+1).
NDCG normalizes DCG by the ideal ranking.

The document retrieval process begins with an offline indexing phase. Documents are
tokenized, stop words removed, and terms stemmed. An inverted index maps each term
to a posting list of documents containing that term. Modern indexes use compression
schemes to reduce storage requirements.

Query processing involves parsing the user's query, applying the same normalization
steps used during indexing, and executing the retrieval function. In BM25, each
query term is scored independently and scores are summed.

Modern neural retrieval methods use transformer-based models to encode queries and
documents into dense vectors. The dot product between query and document vectors
measures their semantic relevance. These models are trained on large datasets of
query-document pairs using contrastive learning objectives.

Hybrid retrieval systems combine sparse (BM25) and dense retrieval. Reciprocal
Rank Fusion (RRF) merges ranked lists from multiple retrievers without requiring
score normalization. On many benchmarks, hybrid systems outperform either
individual method.

Reranking is a second-stage process that applies a more expensive but accurate
cross-encoder model to rerank the top candidates from first-stage retrieval.
Cross-encoders see both query and document simultaneously, enabling fine-grained
relevance judgments.

Query expansion adds related terms to the original query to improve recall. Methods
include pseudo-relevance feedback, thesaurus expansion, and LLM-based expansion.
Hypothetical Document Embeddings (HyDE) ask an LLM to generate a hypothetical
answer document and use its embedding as the query vector.

Other important IR topics include faceted search, which allows filtering by
attributes; learning to rank (LTR), which uses machine learning to optimize the
ranking function; and diversity in ranking, which ensures results cover different
aspects of the query.

Evaluation campaigns like TREC, BEIR, and MS MARCO provide standardized datasets
for comparing retrieval systems. The BEIR benchmark covers 18 datasets across
nine task types, in domains including scientific, financial, and medical text.
""".strip()


# ── Utility functions ────────────────────────────────────────────────────────
def sentence_tokenize(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Join each sentence onto one line, and drop fragments too short to carry meaning
    return [" ".join(s.split()) for s in sentences if len(s.strip()) > 15]


def count_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.33))


# ── Extractive Compressor ────────────────────────────────────────────────────
class ExtractiveSentenceCompressor:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def compress(self, context: str, query: str, token_budget: int) -> dict:
        sentences = sentence_tokenize(context)
        all_embs = self.model.encode([query] + sentences, normalize_embeddings=True)
        query_emb = all_embs[0]
        sent_embs = all_embs[1:]
        scores = sent_embs @ query_emb  # cosine similarity

        ranked = sorted(
            enumerate(zip(sentences, scores.tolist())),
            key=lambda x: x[1][1],
            reverse=True,
        )

        selected_idx = []
        tokens_used = 0
        for orig_idx, (sent, sim) in ranked:
            t = count_tokens(sent)
            if tokens_used + t <= token_budget:
                selected_idx.append((orig_idx, sim))
                tokens_used += t

        selected_idx.sort(key=lambda x: x[0])
        compressed = " ".join(sentences[i] for i, _ in selected_idx)

        return {
            "text": compressed,
            "original_tokens": count_tokens(context),
            "compressed_tokens": tokens_used,
            "sentences_kept": len(selected_idx),
            "sentences_total": len(sentences),
            "compression_ratio": 1 - tokens_used / count_tokens(context),
            # The three highest-scoring kept sentences, best first
            "top_sentences": [
                (sentences[i], round(s, 3))
                for i, s in sorted(selected_idx, key=lambda x: x[1], reverse=True)[:3]
            ],
        }


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    compressor = ExtractiveSentenceCompressor()

    print("=" * 70)
    print("CONTEXT COMPRESSION LAB")
    print("=" * 70)
    print(f"\nQuery: {QUERY}")
    print(f"Target token budget: {TOKEN_BUDGET}")
    print(f"Original context tokens: ~{count_tokens(LONG_CONTEXT)}")
    print("\nCompressing...")

    result = compressor.compress(LONG_CONTEXT, QUERY, TOKEN_BUDGET)

    print("\n── Results ──────────────────────────────────────────────────────")
    print(f"Original tokens:    {result['original_tokens']}")
    print(f"Compressed tokens:  {result['compressed_tokens']}")
    print(f"Compression ratio:  {result['compression_ratio']:.1%}")
    print(f"Sentences kept:     {result['sentences_kept']} / {result['sentences_total']}")

    print("\n── Top 3 Most Relevant Sentences (score) ────────────────────────")
    for sent, score in result["top_sentences"]:
        print(f"  [{score:.3f}] {sent[:80]}...")

    print("\n── Compressed Context ───────────────────────────────────────────")
    print(result["text"])

    # Verify key metrics appear in the compressed context
    key_terms = ["precision", "recall", "MRR", "NDCG", "F1"]
    found = [t for t in key_terms if t.lower() in result["text"].lower()]
    print("\n── Key Metric Terms Preserved ───────────────────────────────────")
    print(f"  Found: {found}")
    print(f"  Missing: {[t for t in key_terms if t not in found]}")


if __name__ == "__main__":
    main()
