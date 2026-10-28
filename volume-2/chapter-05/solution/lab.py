import sys
from pathlib import Path

# Find the volume's shared/ folder, which holds the recording client.
sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in Path(__file__).resolve().parents
            if (p / "shared" / "nexoma_labs").is_dir()
        )
    ),
)

import os
import re

from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

TASK = """Analyze the following drug interaction scenario and provide your assessment:

A 67-year-old patient with atrial fibrillation is taking warfarin (INR 2.4, stable).
Their primary care physician wants to add ibuprofen 400mg TID for knee osteoarthritis pain.

Question: What are the key considerations for this drug combination?"""

# Three role levels
roles = [
    {"label": "LEVEL 1 — Generic", "system": "You are a helpful AI assistant."},
    {
        "label": "LEVEL 2 — Specialized Expert",
        "system": """You are a clinical pharmacist with specialization in anticoagulation therapy
and drug interaction management at a hospital outpatient clinic.""",
    },
    {
        "label": "LEVEL 3 — Full Persona",
        "system": """You are Dr. Patricia Okonkwo, PharmD, BCPS, a board-certified pharmacotherapy
specialist with 18 years of experience in anticoagulation clinic management at a major
academic medical center.

Your communication style:
- Precise and evidence-based; you cite specific mechanisms and clinical evidence
- Organized: you structure responses as (1) mechanism of interaction, (2) clinical risk
  assessment, (3) management options, (4) monitoring recommendations
- You quantify risk when evidence exists rather than using vague qualitative descriptors
- You explicitly acknowledge when evidence is limited or extrapolated from analogous cases
- You always close with a specific recommended action or decision point

Uncertainty rule: If you are uncertain about a specific detail, state:
"I would recommend verifying this in current prescribing information or consulting
[specific resource] before acting." Never omit this if applicable.""",
    },
]


def run_role(role: dict, task: str) -> str:
    print(f"\n{'=' * 60}")
    print(f"ROLE: {role['label']}")
    print(f"{'=' * 60}")
    response = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=[{"role": "system", "content": role["system"]}, {"role": "user", "content": task}],
        temperature=0.2,
        max_completion_tokens=500,
    )
    output = response.choices[0].message.content
    print(output)
    return output


outputs = {}
for role in roles:
    outputs[role["label"]] = run_role(role, TASK)

# Basic vocabulary analysis
print(f"\n\n{'=' * 60}")
print("VOCABULARY ANALYSIS")
print(f"{'=' * 60}")

medical_terms = [
    "INR",
    "warfarin",
    "NSAID",
    "anticoagulant",
    "platelet",
    "bleeding",
    "GI",
    "COX",
    "thrombin",
    "fibrin",
    "prostaglandin",
    "pharmacodynamic",
    "pharmacokinetic",
    "cytochrome",
    "CYP2C9",
]

for label, output in outputs.items():
    found = [term for term in medical_terms if term.lower() in output.lower()]
    print(f"\n{label}")
    print(f"  Medical terms used ({len(found)}): {', '.join(found)}")
    print(f"  Word count: {len(output.split())}")
    print(
        f"  Has uncertainty language: {'uncertain' in output.lower() or 'verify' in output.lower() or 'consult' in output.lower()}"
    )

# Persona drift check: does each output keep the Level 3 persona's rules?
print(f"\n\n{'=' * 60}")
print("PERSONA DRIFT CHECK (rules from the Level 3 persona)")
print(f"{'=' * 60}")

PERSONA_SECTIONS = ["mechanism", "risk assessment", "management", "monitoring"]
HEADING = r"^\s*(?:#+|\*\*|\d+[.)])\s*(.+)$"
QUANTIFIED = r"\d+(?:\.\d+)?\s*%|\b(?:\d+-|two|three|four|five|ten)fold\b"
CLOSING = r"recommend|decision|action"
VERIFY_SENTENCE = "verifying this in current prescribing information"


def check_persona_drift(output: str) -> list[str]:
    """Return the persona rules an output breaks (empty: no drift)."""
    text = output.lower()
    headings = " ".join(re.findall(HEADING, output, flags=re.M)).lower()
    positions = [headings.find(section) for section in PERSONA_SECTIONS]
    last_line = output.strip().splitlines()[-1].lower()
    drift = []
    if -1 in positions or positions != sorted(positions):
        drift.append("structure: sections missing or out of order")
    if not re.search(QUANTIFIED, text):
        drift.append("risk: no quantified risk estimate")
    if not re.search(CLOSING, last_line):
        drift.append("closing: no explicit recommendation or decision")
    if VERIFY_SENTENCE not in text:
        drift.append("uncertainty: verification sentence missing")
    return drift


for label, output in outputs.items():
    drift = check_persona_drift(output)
    print(f"\n{label}: {len(drift)} of 4 persona rules broken")
    for item in drift:
        print(f"  - {item}")
