# Applied AI Engineering, Volume II, Chapter 18
# Section 18.5, Testing Prompt Libraries
# Copied from the book by scripts/export_listings.py. Report errors as errata.

REGRESSION_SUITE = [
    {
        "input": "My package TRK-12345 hasn't moved in 48 hours.",
        "expected_category": "shipment_tracking",
        "expected_priority": "medium"
    },
    {
        "input": "I need to cancel my account immediately.",
        "expected_category": "account_management",
        "expected_priority": "high"
    },
]
