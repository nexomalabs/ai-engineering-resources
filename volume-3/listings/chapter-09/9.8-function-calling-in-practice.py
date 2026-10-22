# Applied AI Engineering, Volume III, Chapter 9
# Section 9.8, Function Calling in Practice
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def extract_structured_data(text: str, schema: dict, client: OpenAI) -> dict:
    """
    Use forced function calling to extract structured data from text.
    Returns a validated dict conforming to the provided JSON schema.
    """
    extraction_tool = {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": "Extract structured information from the provided text.",
            "parameters": schema,
        },
    }
    response = client.chat.completions.create(
        model="gpt-6-luna",
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

# Example: Extract invoice data from unstructured text
INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name":    {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date":   {"type": "string", "description": "ISO 8601 date"},
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
            },
        },
        "total_amount": {"type": "number"},
        "currency":     {"type": "string"},
    },
    "required": ["vendor_name", "invoice_number", "total_amount"],
}
