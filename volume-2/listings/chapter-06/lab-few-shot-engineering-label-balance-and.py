# Applied AI Engineering, Volume II, Chapter 6
# Hands-on Lab: Few-Shot Engineering: Label Balance and Selection
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ============================================================
# PART 1: Label Balance Demonstration
# ============================================================

IMBALANCED_EXAMPLES = """
Ticket: "I've been waiting 6 weeks for a refund. This is outrageous."
Sentiment: NEGATIVE

Ticket: "Your team resolved my issue in under an hour. Impressive!"
Sentiment: POSITIVE

Ticket: "Another amazing experience. Your support team is the best!"
Sentiment: POSITIVE

Ticket: "Five stars! Couldn't ask for better service."
Sentiment: POSITIVE
"""

BALANCED_EXAMPLES = """
Ticket: "I've been waiting 6 weeks for a refund. This is outrageous."
Sentiment: NEGATIVE

Ticket: "Your team resolved my issue in under an hour. Impressive!"
Sentiment: POSITIVE

Ticket: "Package arrived. No damage. Took the expected 5 days."
Sentiment: NEUTRAL

Ticket: "This is the third time I've had to call about the same problem."
Sentiment: NEGATIVE

Ticket: "Everything was fine. Nothing outstanding, just standard service."
Sentiment: NEUTRAL

Ticket: "The technician arrived early and fixed everything on the first visit."
Sentiment: POSITIVE
"""

test_tickets = [
    "My order arrived on time and matches the description.",  # NEUTRAL
    "I can't believe how bad this experience has been.",       # NEGATIVE
    "Really happy with the quick response from your team.",   # POSITIVE
]

def classify_sentiment(examples: str, ticket: str, label: str) -> str:
    prompt = f"{examples}\nTicket: \"{ticket}\"\nSentiment:"
    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {"role": "system", "content": "You are a sentiment classifier. Respond with only: POSITIVE, NEGATIVE, or NEUTRAL"},
            {"role": "user", "content": prompt}
        ],
        temperature=0, max_tokens=10
    )
    result = response.choices[0].message.content.strip()
    return result

print("LABEL BALANCE EXPERIMENT")
print("="*60)
for ticket in test_tickets:
    imb = classify_sentiment(IMBALANCED_EXAMPLES, ticket, "imbalanced")
    bal = classify_sentiment(BALANCED_EXAMPLES, ticket, "balanced")
    print(f"\nTicket: '{ticket}'")
    print(f"  Imbalanced examples → {imb}")
    print(f"  Balanced examples   → {bal}")

# ============================================================
# PART 2: Dynamic Few-Shot Selection
# ============================================================

EXAMPLE_LIBRARY = [
    {"input": "Product broke after two uses", "label": "NEGATIVE"},
    {"input": "Delivery was faster than expected", "label": "POSITIVE"},
    {"input": "Item is exactly as pictured", "label": "NEUTRAL"},
    {"input": "Worst customer service I've ever experienced", "label": "NEGATIVE"},
    {"input": "Best purchase I've made this year", "label": "POSITIVE"},
    {"input": "Functional but nothing special", "label": "NEUTRAL"},
    {"input": "Stopped working after a week", "label": "NEGATIVE"},
    {"input": "Great quality for the price", "label": "POSITIVE"},
    {"input": "Arrived on time, no issues", "label": "NEUTRAL"},
]

def get_embedding(text: str) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def select_dynamic_examples(test_input: str, library: list, k: int = 3) -> list:
    test_emb = np.array(get_embedding(test_input)).reshape(1, -1)
    lib_embs = np.array([get_embedding(ex["input"]) for ex in library])
    scores = cosine_similarity(test_emb, lib_embs)[0]
    top_k_indices = np.argsort(scores)[-k:][::-1]
    return [library[i] for i in top_k_indices]

test_input = "The product quality is terrible, but the customer service was very helpful"
print(f"\n\nDYNAMIC FEW-SHOT SELECTION")
print(f"Test input: '{test_input}'")
selected = select_dynamic_examples(test_input, EXAMPLE_LIBRARY, k=3)
print(f"\nDynamically selected examples:")
for ex in selected:
    print(f"  Input: '{ex['input']}' → {ex['label']}")
