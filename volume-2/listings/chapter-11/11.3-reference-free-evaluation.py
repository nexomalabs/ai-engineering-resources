# Applied AI Engineering, Volume II, Chapter 11
# Section 11.3, Reference-Free Evaluation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json

from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment


def check_factual_consistency(claim: str, source: str) -> dict:
    """Use an LLM to check if a claim is supported by a source."""
    response = client.chat.completions.create(
        model="gpt-6.1-sol",
        messages=[{
            "role": "user",
            "content": f"""Does the following claim accurately reflect the information in the source text?

Source: {source}

Claim: {claim}

Return JSON: {{"supported": true/false, "evidence": "...", "confidence": 0.0-1.0}}"""
        }],
        response_format={"type": "json_object"},
        temperature=0
    )
    return json.loads(response.choices[0].message.content)
