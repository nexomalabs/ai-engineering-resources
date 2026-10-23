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

TASK_INPUT = """
User story: As a mobile banking app user, I want to receive real-time
notifications when transactions occur on my account so that I can
immediately detect unauthorized activity.
"""

# ============================================================
# PATTERN 1: TEMPLATE PATTERN
# ============================================================

TEMPLATE_PATTERN = (
    """Analyze the following user story using exactly this template.
Replace all [bracketed content]. Do not change any other text.

USER STORY ANALYSIS
==================
Story: [exact user story text]

Acceptance Criteria:
1. [Specific, testable criterion]
2. [Specific, testable criterion]
3. [Specific, testable criterion]

Edge Cases to Consider:
- [Edge case 1]
- [Edge case 2]
- [Edge case 3]

Technical Considerations:
- [Technical consideration 1]
- [Technical consideration 2]

Story Points Estimate: [1/2/3/5/8/13] — Rationale: [brief explanation]

User story:
"""
    + TASK_INPUT
)

# ============================================================
# PATTERN 2: COGNITIVE VERIFIER PATTERN
# ============================================================

COGNITIVE_VERIFIER = (
    """When analyzing a user story, first generate 4 sub-questions
that must be answered to fully understand the requirements, then answer each,
then synthesize into a complete analysis.

Format:
SUB-QUESTIONS:
1. [Question]
2. [Question]
3. [Question]
4. [Question]

SUB-ANSWERS:
1. [Answer]
2. [Answer]
3. [Answer]
4. [Answer]

SYNTHESIS:
[Complete analysis based on sub-answers]

User story to analyze:
"""
    + TASK_INPUT
)

# ============================================================
# PATTERN 3: PERSONA + EXPERT REVIEWER COMBINATION
# ============================================================

PERSONA_REVIEWER = (
    """You are Maya Chen, a senior product manager with 12 years of experience
in fintech product development. You specialize in writing precise, developer-friendly
user stories with comprehensive acceptance criteria.

PHASE 1 — GENERATE:
Write a complete analysis of this user story.

PHASE 2 — REVIEW:
Review your analysis against these criteria:
- COMPLETENESS: Does it cover all edge cases for financial transactions?
- TECHNICAL ACCURACY: Are the technical considerations feasible?
- TESTABILITY: Can each acceptance criterion be verified by QA?
- SECURITY: Does it address security and compliance considerations?

For each: rate PASS / IMPROVE. Briefly explain.

PHASE 3 — REVISE:
Produce a revised analysis addressing all IMPROVE items.

User story:
"""
    + TASK_INPUT
)


def run_pattern(prompt: str, pattern_name: str):
    print(f"\n{'=' * 60}")
    print(f"PATTERN: {pattern_name}")
    print(f"{'=' * 60}")
    r = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_completion_tokens=800,
    )
    print(r.choices[0].message.content)


run_pattern(TEMPLATE_PATTERN, "Template Pattern")
run_pattern(COGNITIVE_VERIFIER, "Cognitive Verifier Pattern")
run_pattern(PERSONA_REVIEWER, "Persona + Expert Reviewer Combination")
