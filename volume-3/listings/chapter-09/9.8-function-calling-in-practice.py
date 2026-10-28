# Applied AI Engineering, Volume III, Chapter 9
# Section 9.8, Function Calling in Practice
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def extract_structured_data(text: str, schema: dict, client: OpenAI) -> dict:
    """
    Use forced function calling with strict mode to extract structured data from text.
    With strict mode, the returned arguments are guaranteed to match the schema.
    """
    extraction_tool = {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": "Extract structured information from the provided text.",
            "parameters": schema,
            "strict": True,  # constrain generation to the schema (Structured Outputs)
        },
    }
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[
            {
                "role": "system",
                "content": "Extract the requested information from the user's text. "
                           "Always call the extract_data function.",
            },
            {"role": "user", "content": text},
        ],
        tools=[extraction_tool],
        tool_choice={"type": "function", "function": {"name": "extract_data"}},
    )
    tool_call = response.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)

# Example: Extract invoice data from unstructured text. A strict schema lists every
# property in "required" and sets additionalProperties to False on every object.
INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name":    {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date":   {"type": ["string", "null"], "description": "ISO 8601 date"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity":    {"type": "number"},
                    "unit_price":  {"type": "number"},
                },
                "required": ["description", "quantity", "unit_price"],
                "additionalProperties": False,
            },
        },
        "total_amount": {"type": "number"},
        "currency":     {"type": ["string", "null"]},
    },
    "required": ["vendor_name", "invoice_number", "invoice_date", "line_items",
                 "total_amount", "currency"],
    "additionalProperties": False,
}
