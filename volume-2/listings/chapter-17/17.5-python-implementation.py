# Applied AI Engineering, Volume II, Chapter 17
# Section 17.5, The Template Pattern
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from jinja2 import Environment, BaseLoader
from dataclasses import dataclass, field
from typing import Any
import json

@dataclass
class TemplateFramework:
    """
    Template Pattern implementation.
    Encapsulates a parametric prompt structure with a fixed output contract.
    """
    name: str
    version: str
    role_declaration: str
    universal_constraints: str
    output_schema: dict
    _env: Environment = field(default_factory=lambda: Environment(loader=BaseLoader()))

    TEMPLATE_STR = """\
{{ role_declaration }}

UNIVERSAL CONSTRAINTS:
{{ universal_constraints }}

TASK: {{ task_instruction }}

INPUT:
{{ input_data }}

OUTPUT FORMAT (respond ONLY with valid JSON matching this schema):
{{ output_schema }}

BEGIN OUTPUT:"""

    def render(self, task_instruction: str, input_data: str) -> str:
        tmpl = self._env.from_string(self.TEMPLATE_STR)
        return tmpl.render(
            role_declaration=self.role_declaration,
            universal_constraints=self.universal_constraints,
            task_instruction=task_instruction,
            input_data=input_data,
            output_schema=json.dumps(self.output_schema, indent=2),
        )

    def validate_output(self, raw_output: str) -> tuple[bool, Any]:
        """Attempt to parse and structurally validate the model output."""
        try:
            parsed = json.loads(raw_output.strip())
            required = set(self.output_schema.get("required", []))
            present = set(parsed.keys())
            missing = required - present
            if missing:
                return False, f"Missing required fields: {missing}"
            return True, parsed
        except json.JSONDecodeError as e:
            return False, f"JSON parse error: {e}"


# ---- Example: Sentiment Analysis Task ----

sentiment_framework = TemplateFramework(
    name="sentiment-analysis-v1",
    version="1.0.0",
    role_declaration=(
        "You are a professional text analyst specializing in sentiment classification "
        "for customer communications."
    ),
    universal_constraints=(
        "- Classify based on explicit textual evidence only.\n"
        "- Do not infer unstated intent.\n"
        "- Flag ambiguous texts with confidence below 0.6."
    ),
    output_schema={
        "type": "object",
        "required": ["sentiment", "confidence", "evidence", "flags"],
        "properties": {
            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral", "mixed"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "evidence": {"type": "string"},
            "flags": {"type": "array", "items": {"type": "string"}},
        },
    },
)

prompt = sentiment_framework.render(
    task_instruction="Classify the sentiment of the following customer feedback.",
    input_data="The onboarding was straightforward, but the billing portal crashed twice. "
               "Support eventually resolved it, though the wait was frustrating.",
)
print(prompt)
