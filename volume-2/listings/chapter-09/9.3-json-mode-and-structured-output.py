# Applied AI Engineering, Volume II, Chapter 9
# Section 9.3, JSON Mode and Structured Output
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json

from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment

schema = {
    "type": "object",
    "properties": {
        "sentiment": {
            "type": "string",
            "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "key_phrases": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        },
        "reasoning": {"type": "string"}
    },
    "required": ["sentiment", "confidence", "key_phrases", "reasoning"],
    "additionalProperties": False
}

response = client.chat.completions.create(
    model="gpt-6-sol",
    messages=[
        {"role": "system", "content": "You are a sentiment analysis expert."},
        {"role": "user", "content": f"Analyze: 'The shipping was fast but the product quality is disappointing.'"}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "sentiment_analysis",
            "schema": schema,
            "strict": True
        }
    }
)

result = json.loads(response.choices[0].message.content)
