# Applied AI Engineering, Volume IV, Chapter 10
# Hands-on Lab: PII Detection and Redaction Pipeline
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def safe_llm_call(user_input: str, client) -> dict:
    # Redact input
    redacted_input, input_entities = redact_pii(user_input)
    # LLM call with redacted input
    resp = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": redacted_input}],
        max_tokens=150,
    )
    raw_output = resp.choices[0].message.content or ""
    # Redact output
    redacted_output, output_entities = redact_pii(raw_output)
    return {
        "redacted_input": redacted_input,
        "input_entities": input_entities,
        "raw_output": raw_output,
        "redacted_output": redacted_output,
        "output_entities": output_entities,
    }
