# Applied AI Engineering, Volume IV, Chapter 18
# Section 18.5, Volume II Integration: Prompt Engineering Framework
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# prompt_registry.py — Core data model for the Prompt Registry
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import hashlib
import json


class PromptType(str, Enum):
    INSTRUCTION = "instruction"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    STRUCTURED_OUTPUT = "structured_output"
    MULTI_TURN = "multi_turn"
    AGENT_SYSTEM = "agent_system"


class PromptStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


@dataclass
class PromptVersion:
    version_id: str
    template_id: str
    version: str            # Semantic version: "1.2.0"
    prompt_type: PromptType
    system_message: str
    user_template: str      # Jinja2 template with {variable} slots
    variables: list[str]    # Required variable names
    model_requirements: dict  # e.g., {"min_context": 4096, "reasoning": False}
    status: PromptStatus = PromptStatus.DRAFT
    quality_score: Optional[float] = None
    token_estimate: int = 0
    author: str = ""
    change_notes: str = ""

    def render(self, **kwargs) -> tuple[str, str]:
        """Render system and user messages with provided variables."""
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        user_msg = self.user_template
        for key, value in kwargs.items():
            user_msg = user_msg.replace(f"{{{key}}}", str(value))
        return self.system_message, user_msg

    def content_hash(self) -> str:
        content = self.system_message + self.user_template
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class PromptRegistry:
    def __init__(self):
        self._store: dict[str, list[PromptVersion]] = {}

    def register(self, prompt: PromptVersion):
        if prompt.template_id not in self._store:
            self._store[prompt.template_id] = []
        self._store[prompt.template_id].append(prompt)

    def get_approved(self, template_id: str) -> Optional[PromptVersion]:
        """Return the latest approved version of a template."""
        versions = self._store.get(template_id, [])
        approved = [v for v in versions if v.status == PromptStatus.APPROVED]
        return approved[-1] if approved else None

    def list_templates(self) -> list[dict]:
        result = []
        for tid, versions in self._store.items():
            latest = versions[-1]
            result.append({
                "template_id": tid,
                "versions": len(versions),
                "latest_status": latest.status.value,
                "quality_score": latest.quality_score,
            })
        return result
