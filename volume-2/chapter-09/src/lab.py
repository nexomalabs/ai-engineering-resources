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

import json
import os
from typing import Optional

from nexoma_labs import OpenAI  # records and replays responses; see shared/
from pydantic import BaseModel, ValidationError, field_validator

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# SCHEMA DEFINITION
# ============================================================


class JobPosting(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_years_experience: Optional[int] = None
    is_remote: bool
    skills: list[str]

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        if len(v) > 20:
            raise ValueError("Too many skills extracted — max 20")
        return v


# ============================================================
# TEST INPUTS
# ============================================================

JOB_POSTINGS = [
    """Senior Python Developer at TechCorp. San Francisco, CA or remote.
    $130,000–$160,000/year. 5+ years required. Must know: Python, Django, PostgreSQL,
    Docker, AWS, REST APIs, Git.""",
    """Marketing Manager position. New York office only. Salary negotiable.
    Experience with SEO, content marketing, HubSpot, Google Analytics. 2 years min.""",
    """Junior Data Analyst. Remote-first company. $55k-$70k. Recent grads welcome.
    Skills: Excel, SQL, Tableau, Python basics.""",
]

# ============================================================
# EXTRACTION WITH SCHEMA ENFORCEMENT
# ============================================================

EXTRACTION_SYSTEM = """You are a job posting data extraction specialist.

Extract all available information from job postings into the specified JSON schema.
For missing fields, use null (not "N/A" or empty string).
For salary ranges, extract as integers (dollars only, no symbols)."""


def extract_with_json_mode(posting: str) -> Optional[JobPosting]:
    """Level 4: API-level JSON mode with schema"""

    schema = {
        "type": "object",
        "properties": {
            "job_title": {"type": "string"},
            "company": {"type": "string"},
            "location": {"type": ["string", "null"]},
            "salary_min": {"type": ["integer", "null"]},
            "salary_max": {"type": ["integer", "null"]},
            "required_years_experience": {"type": ["integer", "null"]},
            "is_remote": {"type": "boolean"},
            "skills": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "job_title",
            "company",
            "location",
            "salary_min",
            "salary_max",
            "required_years_experience",
            "is_remote",
            "skills",
        ],
        "additionalProperties": False,
    }

    try:
        response = client.chat.completions.create(
            model="gpt-6-sol",
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": f"Extract from this job posting:\n\n{posting}"},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "job_posting", "schema": schema, "strict": True},
            },
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content)
        return JobPosting(**data)
    except Exception as e:
        print(f"Extraction failed: {e}")
        return None


# ============================================================
# RUN AND VALIDATE
# ============================================================

print("JOB POSTING EXTRACTION WITH SCHEMA ENFORCEMENT")
print("=" * 60)

results = []
for i, posting in enumerate(JOB_POSTINGS, 1):
    print(f"\nPosting {i}: {posting[:80]}...")
    result = extract_with_json_mode(posting)
    if result:
        print(f"  Title: {result.job_title}")
        print(f"  Company: {result.company}")
        print(f"  Location: {result.location}")
        print(f"  Salary: ${result.salary_min}–${result.salary_max}")
        print(f"  Remote: {result.is_remote}")
        print(
            f"  Skills ({len(result.skills)}): {', '.join(result.skills[:5])}{'...' if len(result.skills) > 5 else ''}"
        )
        results.append(result)
    else:
        print("  EXTRACTION FAILED")

print(
    f"\n\nSuccess rate: {len(results)}/{len(JOB_POSTINGS)} ({len(results) / len(JOB_POSTINGS) * 100:.0f}%)"
)

# ============================================================
# FORMAT COMPLIANCE BY LEVEL
# ============================================================

LEVEL_1_PROMPT = """Extract the job title, company, location, salary range,
years of experience required, whether the job is remote, and the skills from
this job posting. Return a JSON object.

{posting}"""

LEVEL_2_SYSTEM = (
    EXTRACTION_SYSTEM
    + """

Return only a JSON object with exactly these fields and types:
{"job_title": string, "company": string, "location": string or null,
 "salary_min": integer or null, "salary_max": integer or null,
 "required_years_experience": integer or null, "is_remote": boolean,
 "skills": list of strings}"""
)


USER_PROMPT = "Extract from this job posting:\n\n"


def extract_raw(messages: list[dict]) -> str:
    """Levels 1 and 2: the format is asked for in the prompt only."""
    response = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content


def check_format(raw: str) -> str:
    """Return "ok", or the first way a reply fails the JobPosting schema."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return f"not valid JSON (starts {raw.strip()[:12]!r})"
    if not isinstance(data, dict):
        return "valid JSON, but not an object"
    try:
        JobPosting(**data)
    except ValidationError as e:
        err = e.errors()[0]
        field = ".".join(str(part) for part in err["loc"])
        return f"wrong schema: {field} {err['msg'].lower()}"
    return "ok"


levels = {
    "1 — Prose instruction": lambda p: [
        {"role": "user", "content": LEVEL_1_PROMPT.format(posting=p)}
    ],
    "2 — Schema in system prompt": lambda p: [
        {"role": "system", "content": LEVEL_2_SYSTEM},
        {"role": "user", "content": USER_PROMPT + p},
    ],
}

print(f"\n\n{'=' * 60}")
print("FORMAT COMPLIANCE BY LEVEL")
print("=" * 60)

for level, build in levels.items():
    checks = [check_format(extract_raw(build(p))) for p in JOB_POSTINGS]
    passed = f"{checks.count('ok')}/{len(checks)}"
    print(f"\nLevel {level}: {passed} match the schema")
    for i, check in enumerate(checks, 1):
        if check != "ok":
            print(f"  Posting {i}: {check}")

level_4 = f"{len(results)}/{len(JOB_POSTINGS)}"
print(f"\nLevel 4 — Strict JSON schema mode: {level_4} match the schema")
