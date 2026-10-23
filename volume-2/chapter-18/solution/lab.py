# legal_prompt_library.py

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


def semver_key(version: str) -> tuple:
    """Order versions numerically: "1.10.0" is newer than "1.9.0"."""
    return tuple(int(part) for part in version.split("."))


# ── Prompt Dataclass ─────────────────────────────────────────────────────


@dataclass
class Prompt:
    prompt_id: str
    display_name: str
    version: str
    owner: str
    description: str
    template: str
    parameters: list[dict]  # [{name, type, required, description}]
    output_schema: dict
    tags: list[str] = field(default_factory=list)
    status: str = "stable"  # stable | experimental | deprecated
    models_tested: list[str] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)
    deprecated_by: Optional[str] = None
    sunset_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    _test_cases: list[dict] = field(default_factory=list, repr=False)

    def render(self, **kwargs) -> str:
        """Render the prompt template with the provided parameters."""
        rendered = self.template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    def execute(self, llm_fn: Callable[[str], str], **kwargs) -> Any:
        """Render and execute the prompt through the provided LLM function."""
        prompt_text = self.render(**kwargs)
        raw_output = llm_fn(prompt_text)
        try:
            return json.loads(raw_output.strip())
        except json.JSONDecodeError:
            return raw_output

    def add_test_case(
        self, input_params: dict, expected_output: dict, description: str = ""
    ) -> None:
        self._test_cases.append(
            {"input": input_params, "expected": expected_output, "description": description}
        )

    def run_schema_test(self, llm_fn: Callable[[str], str], test_index: int = 0) -> dict:
        """Run a schema-level test using the specified test case."""
        if test_index >= len(self._test_cases):
            return {"passed": False, "reason": "No test cases defined"}
        tc = self._test_cases[test_index]
        result = self.execute(llm_fn, **tc["input"])
        if not isinstance(result, dict):
            return {"passed": False, "reason": f"Output is not a dict: {type(result)}"}
        required = self.output_schema.get("required", [])
        missing = [f for f in required if f not in result]
        if missing:
            return {"passed": False, "reason": f"Missing required fields: {missing}"}
        return {"passed": True, "output": result}


# ── Prompt Library ────────────────────────────────────────────────────────


class PromptLibrary:
    """
    Professional prompt library with CRUD, versioning, tagging,
    search, and governance operations.
    """

    def __init__(self, library_name: str):
        self.library_name = library_name
        # Storage: {prompt_id: {version_str: Prompt}}
        self._store: dict[str, dict[str, Prompt]] = {}
        self._changelog: list[dict] = []

    # ── CRUD ──────────────────────────────────────────────────────────────

    def register(self, prompt: Prompt) -> str:
        """Add a new prompt to the library."""
        pid = prompt.prompt_id
        if pid not in self._store:
            self._store[pid] = {}
        if prompt.version in self._store[pid]:
            raise ValueError(
                f"Prompt '{pid}@{prompt.version}' already exists. "
                f"Use update() to create a new version."
            )
        self._store[pid][prompt.version] = prompt
        self._log_change(
            "register",
            pid,
            prompt.version,
            prompt.owner,
            f"Initial registration: {prompt.display_name}",
        )
        print(f"[Library] Registered: {pid}@{prompt.version}")
        return f"{pid}@{prompt.version}"

    def get(self, prompt_id: str, version: str = "latest") -> Prompt:
        """Retrieve a prompt by ID and optional version."""
        if prompt_id not in self._store:
            raise KeyError(f"Prompt '{prompt_id}' not found.")
        versions = self._store[prompt_id]
        if version == "latest":
            # Return the highest-version non-deprecated prompt
            stable = {v: p for v, p in versions.items() if p.status != "deprecated"}
            if not stable:
                raise KeyError(f"All versions of '{prompt_id}' are deprecated.")
            version = max(stable, key=semver_key)
        elif version not in versions:
            raise KeyError(f"Version '{version}' of '{prompt_id}' not found.")
        prompt = versions[version]
        if prompt.status == "deprecated":
            print(
                f"[Library] WARNING: '{prompt_id}@{version}' is deprecated. "
                f"Sunset: {prompt.sunset_date}. "
                f"Replaced by: {prompt.deprecated_by or 'unknown'}"
            )
        return prompt

    def update(
        self,
        prompt_id: str,
        new_version: str,
        changes: dict,
        change_description: str,
        changed_by: str,
    ) -> str:
        """Create a new version of an existing prompt with the specified changes."""
        original = self.get(prompt_id)
        # Deep copy and apply changes
        new_prompt = copy.deepcopy(original)
        new_prompt.version = new_version
        new_prompt.updated_at = datetime.now(timezone.utc).isoformat()
        for key, value in changes.items():
            if hasattr(new_prompt, key):
                setattr(new_prompt, key, value)
        self._store[prompt_id][new_version] = new_prompt
        self._log_change("update", prompt_id, new_version, changed_by, change_description)
        print(f"[Library] Updated: {prompt_id}@{new_version}")
        return f"{prompt_id}@{new_version}"

    def delete(self, prompt_id: str, version: str, deleted_by: str, reason: str) -> None:
        """
        Soft-delete: marks as deprecated rather than removing.
        Hard deletion is not supported to preserve audit history.
        """
        self.deprecate(
            prompt_id,
            version,
            sunset_date=datetime.now(timezone.utc).isoformat(),
            deprecated_by=f"Deleted by {deleted_by}: {reason}",
        )

    def deprecate(
        self, prompt_id: str, version: str, sunset_date: str, deprecated_by: str = None
    ) -> None:
        """Mark a prompt version as deprecated."""
        prompt = self._store[prompt_id][version]
        prompt.status = "deprecated"
        prompt.sunset_date = sunset_date
        prompt.deprecated_by = deprecated_by
        self._log_change(
            "deprecate",
            prompt_id,
            version,
            "governance",
            f"Deprecated. Sunset: {sunset_date}. Replaced by: {deprecated_by}",
        )
        print(f"[Library] Deprecated: {prompt_id}@{version}")

    # ── Search and Discovery ──────────────────────────────────────────────

    def search(
        self,
        query: str = None,
        tags: list[str] = None,
        task_type: str = None,
        status: str = "stable",
    ) -> list[dict]:
        """Search the catalog for prompts matching criteria."""
        results = []
        for pid, versions in self._store.items():
            for ver, prompt in versions.items():
                if status and prompt.status != status:
                    continue
                if tags and not all(t in prompt.tags for t in tags):
                    continue
                if task_type and f"task:{task_type}" not in prompt.tags:
                    continue
                if query and query.lower() not in (
                    prompt.display_name.lower() + " " + prompt.description.lower()
                ):
                    continue
                results.append(
                    {
                        "prompt_id": pid,
                        "version": ver,
                        "display_name": prompt.display_name,
                        "description": prompt.description,
                        "tags": prompt.tags,
                        "owner": prompt.owner,
                    }
                )
        return results

    def list_versions(self, prompt_id: str) -> list[dict]:
        """Return all versions of a prompt with their status."""
        if prompt_id not in self._store:
            raise KeyError(f"Prompt '{prompt_id}' not found.")
        return [
            {"version": v, "status": p.status, "updated_at": p.updated_at}
            for v, p in sorted(self._store[prompt_id].items(), key=lambda item: semver_key(item[0]))
        ]

    def list_all(self) -> list[dict]:
        """Return a summary of all prompts (latest stable version only)."""
        result = []
        for pid in self._store:
            try:
                prompt = self.get(pid)
                result.append(
                    {
                        "prompt_id": pid,
                        "display_name": prompt.display_name,
                        "version": prompt.version,
                        "owner": prompt.owner,
                        "tags": prompt.tags,
                    }
                )
            except KeyError:
                pass
        return result

    # ── Internal ─────────────────────────────────────────────────────────

    def _log_change(
        self, action: str, prompt_id: str, version: str, actor: str, description: str
    ) -> None:
        self._changelog.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "prompt_id": prompt_id,
                "version": version,
                "actor": actor,
                "description": description,
            }
        )

    def changelog(self, prompt_id: str = None) -> list[dict]:
        """Return the changelog, optionally filtered to a specific prompt."""
        if prompt_id:
            return [e for e in self._changelog if e["prompt_id"] == prompt_id]
        return self._changelog


# ── Mock LLM ─────────────────────────────────────────────────────────────


def mock_llm(prompt: str) -> str:
    """Deterministic mock LLM for testing."""
    if "contract type" in prompt.lower() or "classify" in prompt.lower():
        return json.dumps(
            {
                "document_type": "service_agreement",
                "parties": ["Acme Corp", "TechVendor Ltd"],
                "governing_law": "New York",
                "confidence": 0.93,
            }
        )
    if "clause" in prompt.lower() or "extract" in prompt.lower():
        return json.dumps(
            {
                "clauses": [
                    {"type": "limitation_of_liability", "text": "...", "page": 4},
                    {"type": "indemnification", "text": "...", "page": 7},
                ]
            }
        )
    if "risk" in prompt.lower():
        return json.dumps(
            {
                "overall_risk": "medium",
                "risk_score": 0.62,
                "risk_factors": [
                    "Broad indemnification clause",
                    "Unlimited liability for IP infringement",
                ],
            }
        )
    if "summarize" in prompt.lower() or "summary" in prompt.lower():
        return json.dumps(
            {
                "summary": "A 3-year service agreement between Acme Corp and TechVendor Ltd for cloud infrastructure services.",
                "key_dates": ["Effective: 2024-01-01", "Renewal: 2026-12-31"],
                "word_count": 47,
            }
        )
    return json.dumps(
        {
            "plain_language": "This contract says TechVendor will provide cloud hosting for Acme. The agreement lasts 3 years and can be renewed."
        }
    )


# ── Populate Library with Five Prompts ───────────────────────────────────


def build_legal_library() -> PromptLibrary:
    library = PromptLibrary("LegalAI Prompt Library v1")

    # Prompt 1: Document Classification
    p1 = Prompt(
        prompt_id="legal/document-classification",
        display_name="Legal Document Type Classifier",
        version="1.2.0",
        owner="legal-ai-team",
        description="Classifies legal documents into type categories with party identification and governing law extraction.",
        template="""\
You are a legal document analyst with expertise in contract classification.

Analyze the following legal document excerpt and classify it.

DOCUMENT:
{{document_text}}

Respond with valid JSON:
{
  "document_type": "<service_agreement|nda|employment_contract|lease|other>",
  "parties": ["<party_1>", "<party_2>"],
  "governing_law": "<jurisdiction>",
  "confidence": <0.0-1.0>
}
BEGIN:""",
        parameters=[
            {
                "name": "document_text",
                "type": "string",
                "required": True,
                "description": "The legal document text to classify. Max 2000 tokens.",
            }
        ],
        output_schema={"required": ["document_type", "parties", "governing_law", "confidence"]},
        tags=["task:classification", "domain:legal", "output:json", "model:gpt-6.1-sol"],
        models_tested=["gpt-6.1-sol", "claude-sonnet-5-5"],
        known_limitations=[
            "Accuracy decreases for non-English documents.",
            "Multi-party agreements may truncate parties list.",
        ],
    )
    p1.add_test_case(
        input_params={
            "document_text": "This Service Agreement is entered into by Acme Corp and TechVendor Ltd under New York law."
        },
        expected_output={"document_type": "service_agreement"},
        description="Basic service agreement classification",
    )
    library.register(p1)

    # Prompt 2: Clause Extraction
    p2 = Prompt(
        prompt_id="legal/clause-extraction",
        display_name="Legal Clause Extractor",
        version="1.0.3",
        owner="legal-ai-team",
        description="Extracts and identifies specific clause types from contract text with page references.",
        template="""\
You are a legal clause extraction specialist.

Extract all material clauses from the following contract text.

CLAUSE TYPES TO IDENTIFY:
- limitation_of_liability
- indemnification
- termination
- intellectual_property
- confidentiality
- dispute_resolution

CONTRACT TEXT:
{{contract_text}}

Respond with valid JSON:
{
  "clauses": [
    {"type": "<clause_type>", "text": "<excerpt>", "page": <int>}
  ]
}
BEGIN:""",
        parameters=[
            {
                "name": "contract_text",
                "type": "string",
                "required": True,
                "description": "The contract section text. Max 4000 tokens.",
            }
        ],
        output_schema={"required": ["clauses"]},
        tags=["task:extraction", "domain:legal", "output:json", "model:gpt-6.1-sol"],
        models_tested=["gpt-6.1-sol"],
    )
    library.register(p2)

    # Prompt 3: Risk Scoring
    p3 = Prompt(
        prompt_id="legal/risk-scoring",
        display_name="Contract Risk Scorer",
        version="2.0.1",
        owner="risk-team",
        description="Scores legal contract risk on a 0–1 scale and identifies specific risk factors.",
        template="""\
You are a legal risk analyst specializing in commercial contract risk assessment.

Assess the risk profile of the following contract based on its clauses and terms.

CONTRACT SUMMARY:
{{contract_summary}}

EXTRACTED CLAUSES:
{{clauses_json}}

Respond with valid JSON:
{
  "overall_risk": "low|medium|high|critical",
  "risk_score": <0.0-1.0>,
  "risk_factors": ["<string>"]
}
BEGIN:""",
        parameters=[
            {
                "name": "contract_summary",
                "type": "string",
                "required": True,
                "description": "Brief summary of the contract.",
            },
            {
                "name": "clauses_json",
                "type": "string",
                "required": True,
                "description": "JSON array of extracted clauses.",
            },
        ],
        output_schema={"required": ["overall_risk", "risk_score", "risk_factors"]},
        tags=["task:scoring", "domain:legal", "domain:risk", "output:json"],
        models_tested=["gpt-6.1-sol", "claude-sonnet-5-5"],
    )
    library.register(p3)

    # Prompt 4: Document Summarization
    p4 = Prompt(
        prompt_id="legal/document-summarization",
        display_name="Legal Document Summarizer",
        version="1.1.0",
        owner="legal-ai-team",
        description="Produces a concise summary of a legal document including key dates and obligations.",
        template="""\
You are a legal document summarization specialist.

Produce a concise, accurate summary of the following legal document.

DOCUMENT:
{{document_text}}

Respond with valid JSON:
{
  "summary": "<string, max 100 words>",
  "key_dates": ["<YYYY-MM-DD: description>"],
  "word_count": <int>
}
BEGIN:""",
        parameters=[
            {
                "name": "document_text",
                "type": "string",
                "required": True,
                "description": "The legal document to summarize. Max 6000 tokens.",
            }
        ],
        output_schema={"required": ["summary", "key_dates", "word_count"]},
        tags=["task:summarization", "domain:legal", "output:json"],
        models_tested=["gpt-6.1-sol", "claude-sonnet-5-5", "gemini-4-argon"],
    )
    library.register(p4)

    # Prompt 5: Plain Language Translation
    p5 = Prompt(
        prompt_id="legal/plain-language-translation",
        display_name="Legal Plain Language Translator",
        version="1.0.0",
        owner="ux-team",
        description="Translates legal contract language into plain English for non-specialist readers.",
        template="""\
You are a legal plain language specialist. Your role is to translate legal text
into clear, accessible English that a non-lawyer can understand.

RULES:
- Do not change the meaning. Translate only the expression.
- Use active voice where possible.
- Define legal terms in parentheses on first use.
- Maximum reading level: 8th grade Flesch-Kincaid.

LEGAL TEXT:
{{legal_text}}

Respond with valid JSON:
{
  "plain_language": "<translated text>"
}
BEGIN:""",
        parameters=[
            {
                "name": "legal_text",
                "type": "string",
                "required": True,
                "description": "The legal text to translate. Max 500 tokens.",
            }
        ],
        output_schema={"required": ["plain_language"]},
        tags=["task:translation", "domain:legal", "output:json", "audience:consumer"],
        models_tested=["gpt-6.1-sol"],
        known_limitations=["May oversimplify highly technical financial terms."],
    )
    library.register(p5)

    return library


# ── Demonstration ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    library = build_legal_library()

    print("\n" + "=" * 60)
    print("ALL PROMPTS IN LIBRARY:")
    for entry in library.list_all():
        print(f"  {entry['prompt_id']}@{entry['version']} — {entry['display_name']}")

    print("\n" + "=" * 60)
    print("SEARCH: tag='domain:legal', task_type='classification'")
    results = library.search(tags=["domain:legal"], task_type="classification")
    for r in results:
        print(f"  Found: {r['prompt_id']} — {r['display_name']}")

    print("\n" + "=" * 60)
    print("EXECUTE: document-classification")
    classifier = library.get("legal/document-classification")
    result = classifier.execute(
        llm_fn=mock_llm,
        document_text="This Service Agreement is entered into by Acme Corp and TechVendor Ltd.",
    )
    print(f"  Result: {json.dumps(result, indent=2)}")

    print("\n" + "=" * 60)
    print("SCHEMA TEST: document-classification")
    test_result = classifier.run_schema_test(llm_fn=mock_llm)
    print(f"  Test passed: {test_result['passed']}")

    print("\n" + "=" * 60)
    print("VERSION LISTING: legal/document-classification")
    # Add a version update first
    library.update(
        prompt_id="legal/document-classification",
        new_version="1.3.0",
        changes={"description": "Added partnership_agreement type to classification options."},
        change_description="MINOR: Added partnership_agreement document type.",
        changed_by="legal-ai-team",
    )
    for v in library.list_versions("legal/document-classification"):
        print(f"  {v['version']} — {v['status']} (updated: {v['updated_at'][:10]})")

    print("\n" + "=" * 60)
    print("DEPRECATION: document-classification@1.2.0")
    library.deprecate(
        "legal/document-classification",
        "1.2.0",
        sunset_date="2027-06-01",
        deprecated_by="legal/document-classification@1.3.0",
    )
    print("Attempting to get deprecated version:")
    library.get("legal/document-classification", version="1.2.0")  # Should warn

    print("\n" + "=" * 60)
    print("CHANGELOG: legal/document-classification")
    for entry in library.changelog("legal/document-classification"):
        print(
            f"  [{entry['action'].upper()}] v{entry['version']} by {entry['actor']}: {entry['description']}"
        )
