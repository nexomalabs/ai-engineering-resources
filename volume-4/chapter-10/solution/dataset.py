"""Step 2: ten test inputs and the PII each one contains, as PERSON, EMAIL, PHONE or SSN.

The SSNs are in 987-65-4320 to 987-65-4329, a range reserved for advertising, so they
belong to no one. The phone numbers use the 555-01xx range set aside for fiction.
"""

DATASET = [
    (
        "Hi, I'm Maria Gonzalez. Please update my email to maria.gonzalez@example.com.",
        ["PERSON", "EMAIL"],
    ),
    ("My SSN is 987-65-4325 and I need a copy of my tax form.", ["SSN"]),
    ("Call me back on (415) 555-0132 after 5pm.", ["PHONE"]),
    (
        "This is David Chen; reach me at david.chen@example.org or 212-555-0187.",
        ["PERSON", "EMAIL", "PHONE"],
    ),
    ("Please verify my identity: Priya Patel, SSN 987-65-4321.", ["PERSON", "SSN"]),
    ("The invoice went to accounts@contoso.example, not to me.", ["EMAIL"]),
    ("Text 646-555-0199 when the package arrives.", ["PHONE"]),
    ("James O'Brien asked whether his account was closed.", ["PERSON"]),
    (
        "Reach Aisha Rahman at +1 312 555 0145 or aisha.r@example.net; her SSN on file is 987-65-4329.",
        ["PERSON", "PHONE", "EMAIL", "SSN"],
    ),
    ("Nothing personal here, just asking about pricing tiers.", []),
]
