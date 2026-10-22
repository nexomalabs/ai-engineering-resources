# Applied AI Engineering, Volume II, Chapter 3
# Hands-on Lab: Instruction Engineering Workshop
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ============================================================
# INSTRUCTION PAIRS: Original vs. Engineered
# ============================================================

tasks = [
    {
        "name": "Task 1: Product Review Analysis",
        "original": "Analyze this review: 'The laptop is fast but gets really hot and the battery only lasts 3 hours. The keyboard is great though. Would not buy again.'",
        "engineered": """Analyze the following product review.

For each sentence in the review:
1. Extract the product aspect being discussed (e.g., "battery life", "keyboard")
2. Classify the sentiment as: POSITIVE, NEGATIVE, or NEUTRAL
3. Extract the specific claim made

Return a Markdown table with columns: Aspect | Sentiment | Claim

After the table, write one sentence: the overall purchase recommendation implied by the review.

Review:
'The laptop is fast but gets really hot and the battery only lasts 3 hours. The keyboard is great though. Would not buy again.'

Begin analysis:"""
    },
    {
        "name": "Task 2: Email Rewrite",
        "original": "Rewrite this email to be more professional: 'Hey, just wanted to check in about that thing we talked about last week. Let me know what you think. Thanks'",
        "engineered": """Rewrite the following email message to meet professional business communication standards.

Rewriting requirements:
- Maintain the core intent of the original message
- Replace informal language with formal equivalents
- Add a professional greeting and closing appropriate for a business colleague
- Do not add specific names, dates, or details not present in the original
- Length: approximately equal to the original (expand by no more than 20%)

Original email:
'Hey, just wanted to check in about that thing we talked about last week. Let me know what you think. Thanks'

Write only the rewritten email. No explanation."""
    },
    {
        "name": "Task 3: Data Extraction",
        "original": "Get the important numbers from this: 'Revenue increased from $4.2M to $5.8M. Operating costs rose by 12%. Net margin improved to 18.3% from 15.1% last year.'",
        "engineered": """Extract all numerical metrics from the following financial statement.

For each metric:
1. Metric name (e.g., "Revenue")
2. Previous value (if stated)
3. Current value
4. Change (absolute or percentage, as stated in text)

Return a JSON array with this exact structure:
[{"metric": string, "previous": string | null, "current": string, "change": string | null}]

Return only the JSON array. No explanation.

Text: 'Revenue increased from $4.2M to $5.8M. Operating costs rose by 12%. Net margin improved to 18.3% from 15.1% last year.'"""
    }
]

# Run both versions for each task
for task in tasks:
    print(f"\n{'='*60}")
    print(f"TASK: {task['name']}")
    print(f"{'='*60}")

    # Original instruction
    print("\n--- ORIGINAL INSTRUCTION OUTPUT ---")
    r1 = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": task["original"]}],
        temperature=0.3,
        max_tokens=300
    )
    print(r1.choices[0].message.content)

    # Engineered instruction
    print("\n--- ENGINEERED INSTRUCTION OUTPUT ---")
    r2 = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": task["engineered"]}],
        temperature=0.1,
        max_tokens=300
    )
    print(r2.choices[0].message.content)

print("\n\nALL TASKS COMPLETE")
