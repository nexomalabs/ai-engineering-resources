# Applied AI Engineering, Volume III, Chapter 7
# Section 7.3, Extractive Compression
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from sentence_transformers import SentenceTransformer
import numpy as np
import re

def sentence_tokenize(text: str) -> list[str]:
    """Simple sentence segmentation using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def estimate_tokens(text: str) -> int:
    """Approximate token count: ~0.75 tokens per word."""
    return max(1, int(len(text.split()) * 1.33))

class ExtractiveSentenceCompressor:
    """
    Compresses a long context by selecting the most query-relevant sentences.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def compress(
        self,
        context: str,
        query: str,
        token_budget: int = 800,
        min_similarity: float = 0.2,
    ) -> dict:
        """
        Compress context to fit within token_budget tokens.
        Returns compressed text and compression statistics.
        """
        sentences = sentence_tokenize(context)
        if not sentences:
            return {"compressed": context, "ratio": 1.0, "sentences_kept": 0}

        # Encode query and all sentences
        all_texts = [query] + sentences
        embeddings = self.model.encode(all_texts, normalize_embeddings=True)
        query_emb = embeddings[0]
        sent_embs = embeddings[1:]

        # Compute cosine similarities
        similarities = (sent_embs @ query_emb).tolist()

        # Score each sentence with its index for order preservation
        scored = sorted(
            enumerate(zip(sentences, similarities)),
            key=lambda x: x[1][1],
            reverse=True,
        )

        # Greedily select sentences up to token budget
        selected_indices = []
        tokens_used = 0
        for orig_idx, (sent, sim) in scored:
            if sim < min_similarity:
                continue
            sent_tokens = estimate_tokens(sent)
            if tokens_used + sent_tokens <= token_budget:
                selected_indices.append(orig_idx)
                tokens_used += sent_tokens

        # Reassemble in original document order
        selected_indices.sort()
        compressed_sentences = [sentences[i] for i in selected_indices]
        compressed_text = " ".join(compressed_sentences)

        original_tokens = estimate_tokens(context)
        return {
            "compressed": compressed_text,
            "original_tokens": original_tokens,
            "compressed_tokens": tokens_used,
            "ratio": tokens_used / original_tokens if original_tokens > 0 else 1.0,
            "sentences_kept": len(selected_indices),
            "sentences_total": len(sentences),
        }
