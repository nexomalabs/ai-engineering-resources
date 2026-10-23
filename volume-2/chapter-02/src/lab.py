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

from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# PART 1: Anatomy-Structured Prompt Construction
# ============================================================

# SYSTEM PROMPT COMPONENT
system_prompt = """You are a senior financial analyst specializing in equity research.

Rules:
1. Base all analysis on the data provided. Do not speculate beyond it.
2. Flag any data that appears anomalous with [FLAG].
3. Never recommend buy/sell decisions — provide analysis only.
4. Use precise financial terminology appropriate for CFA-level readers.

Output format:
Return a structured analysis with exactly these sections:
- Revenue Trend (2-3 sentences)
- Margin Analysis (2-3 sentences)
- Key Risks (bullet list, 3-5 items)
- Summary (1 sentence)"""

# CONTEXT BLOCK COMPONENT
context_block = """<financial_data>
Company: Meridian Technologies Inc.
Period: Q1–Q4 2024

Revenue (millions USD):
Q1: $142.3
Q2: $158.7
Q3: $171.2
Q4: $165.4

Gross Margin:
Q1: 34.2%
Q2: 35.8%
Q3: 36.1%
Q4: 33.9%

Operating Expenses (millions USD):
Q1: $38.4
Q2: $41.2
Q3: $48.7
Q4: $52.3

Sector: Enterprise SaaS
Headcount: 1,240 (Q4, up from 890 in Q1)
</financial_data>"""

# USER PROMPT COMPONENT
user_prompt = f"""Task: Analyze the financial performance of Meridian Technologies for FY2024.

{context_block}

Provide the structured financial analysis now:"""

# FEW-SHOT EXAMPLE (prepended to illustrate format)
few_shot_example = """Here is an example analysis from a comparable company:

Example Input: Similar quarterly revenue and margin data.
Example Output:
**Revenue Trend**
Revenue grew steadily from Q1 to Q3 (+20.3%) before experiencing a modest Q4 decline (-3.4%),
suggesting possible seasonal softness or market saturation in core segments. Full-year growth
of 16.2% indicates healthy demand for the company's offerings.

**Margin Analysis**
Gross margins showed gradual improvement through Q3, peaking at 36.1%, before compressing
in Q4 [FLAG — Q4 margin compression requires investigation; coincides with rapid headcount growth].
The 2.2-point sequential decline warrants monitoring in upcoming quarters.

**Key Risks**
- Rapid headcount expansion outpacing revenue growth may compress future margins
- Q4 revenue deceleration if sustained could indicate demand slowdown
- Operating expense growth (+36.2% YoY) significantly outpaces revenue growth (+16.2%)

**Summary**
FY2024 showed strong top-line growth with margin pressure emerging in Q4 driven by
aggressive headcount expansion that may challenge profitability in 2025.

---
Now analyze the actual data provided:"""

# ============================================================
# PART 2: Run the fully-structured prompt
# ============================================================

full_messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": few_shot_example + "\n\n" + user_prompt},
]

print("RUNNING FULL ANATOMY-STRUCTURED PROMPT")
print("=" * 60)
response = client.chat.completions.create(
    model="gpt-6-sol",
    reasoning_effort="none",
    messages=full_messages,
    temperature=0.2,
    max_completion_tokens=600,
)
full_output = response.choices[0].message.content
print(full_output)

# ============================================================
# PART 3: Ablation — Remove system prompt
# ============================================================

print("\n\nABLATION TEST: No System Prompt")
print("=" * 60)
ablation_messages = [{"role": "user", "content": user_prompt}]
response2 = client.chat.completions.create(
    model="gpt-6-sol",
    reasoning_effort="none",
    messages=ablation_messages,
    temperature=0.2,
    max_completion_tokens=600,
)
print(response2.choices[0].message.content)

print("\n\nCOMPARISON COMPLETE")
print("Note structural differences, tone differences, and rule adherence differences above.")
