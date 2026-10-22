# Applied AI Engineering, Volume II, Chapter 11
# Section 11.5, LLM-as-Judge
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json

from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment

JUDGE_SYSTEM = """You are an expert evaluator of customer service communication quality.

You will evaluate responses on four dimensions, each scored 1–5:
- Relevance (1=off-topic, 5=directly addresses all aspects)
- Accuracy (1=factual errors, 5=fully accurate)
- Tone (1=inappropriate, 5=perfectly calibrated)
- Actionability (1=no guidance, 5=clear specific next steps)

Return JSON: {
  "scores": {"relevance": int, "accuracy": int, "tone": int, "actionability": int},
  "reasoning": {"relevance": str, "accuracy": str, "tone": str, "actionability": str},
  "overall": int
}"""

def llm_judge(customer_query: str, response: str, context: str = "") -> dict:
    r = client.chat.completions.create(
        model="gpt-6.1-sol",
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": f"""Evaluate this response:

Customer query: {customer_query}
{f"Context: {context}" if context else ""}
Response to evaluate: {response}

Provide your evaluation in the required JSON format."""}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    return json.loads(r.choices[0].message.content)
