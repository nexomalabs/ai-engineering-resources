# Applied AI Engineering, Volume II, Chapter 14
# Section 14.3, Contrastive Prompting
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Failing: model invents product features not in the context
prompt_hallucinating = """Answer this customer question about our product.

Question: {question}"""

# Contrastive v1: Added context anchor
prompt_anchored = """Answer this customer question about our product.
Base your answer ONLY on the product information provided below.
If the answer is not in the provided information, say "I don't have that information."

Product information:
{product_info}

Question: {question}"""

# Contrastive v2: Added citation requirement
prompt_cited = """Answer this customer question about our product.
Every claim must be directly supported by the product information below.
Quote the specific section that supports each claim.

Product information:
{product_info}

Question: {question}"""
