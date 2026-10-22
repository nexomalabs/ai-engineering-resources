# Applied AI Engineering, Volume II, Chapter 14
# Section 14.3, Contrastive Prompting
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# BASELINE (failing prompt)
prompt_a = """You are a professional email writer.
Write a response to the following customer complaint.
Keep it professional and include a resolution timeline.

Complaint: {complaint}"""

# CONTRASTIVE (changed one element: added explicit format)
prompt_b = """You are a professional email writer.
Write a response to the following customer complaint.
Keep it professional and include a resolution timeline.

Response structure (required):
1. Opening: Acknowledgment (1 sentence)
2. Body: Specific apology + explanation (2-3 sentences)
3. Resolution: Timeline and next steps (2-3 sentences)
4. Closing: Contact information (1 sentence)

Complaint: {complaint}"""
