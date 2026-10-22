# Applied AI Engineering, Volume II, Chapter 9
# Hands-on Lab: Output Control: Schema Enforcement and Validation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
import json
from pydantic import BaseModel, ValidationError, field_validator
from typing import Optional
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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
    Skills: Excel, SQL, Tableau, Python basics."""
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
            "skills": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["job_title", "company", "location", "salary_min", "salary_max",
                     "required_years_experience", "is_remote", "skills"],
        "additionalProperties": False
    }

    try:
        response = client.chat.completions.create(
            model="gpt-6.1-sol",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": f"Extract from this job posting:\n\n{posting}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "job_posting", "schema": schema, "strict": True}
            },
            temperature=0
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
print("="*60)

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
        print(f"  Skills ({len(result.skills)}): {', '.join(result.skills[:5])}{'...' if len(result.skills) > 5 else ''}")
        results.append(result)
    else:
        print("  EXTRACTION FAILED")

print(f"\n\nSuccess rate: {len(results)}/{len(JOB_POSTINGS)} ({len(results)/len(JOB_POSTINGS)*100:.0f}%)")
