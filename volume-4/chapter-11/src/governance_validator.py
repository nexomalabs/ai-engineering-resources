"""Lab 11 — Governance Validator (starter).

This file RUNS as supplied, but it counts a section as present if its name appears
anywhere in the text. The system card beside it is unfinished. Complete the two TODOs.
Run from the lab folder:

    python src/governance_validator.py
"""
# Validates completeness of governance documentation against required checklists.
# A section counts only if it is a Markdown heading: a word in the body text does not.

import textwrap
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    document: str
    required_sections: list[str]
    found_sections: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    pass_rate: float = 0.0

    def compute(self) -> None:
        self.found_sections = []
        self.missing_sections = []
        content = Path(self.document).read_text(encoding="utf-8").lower()
        # TODO 1: Count a section only if it appears in a Markdown heading (a line that
        #   starts with "#"). Matching anywhere in the text lets a passing mention in
        #   a paragraph stand in for a missing section.
        for section in self.required_sections:
            if section.lower() in content:
                self.found_sections.append(section)
            else:
                self.missing_sections.append(section)
        total = len(self.required_sections)
        self.pass_rate = len(self.found_sections) / total if total > 0 else 0.0

    def report(self) -> None:
        print(f"\n=== {Path(self.document).name} ===")
        print(
            f"Pass rate: {self.pass_rate * 100:.0f}% ({len(self.found_sections)}/{len(self.required_sections)} sections)"
        )
        if self.missing_sections:
            print(f"MISSING: {', '.join(self.missing_sections)}")
        else:
            print("All required sections present.")


MODEL_CARD_SECTIONS = [
    "model details",
    "intended use",
    "out of scope",
    "performance metrics",
    "ethical considerations",
    "known limitations",
    "training data",
    "evaluation",
]

SYSTEM_CARD_SECTIONS = [
    "system overview",
    "safety evaluation",
    "safeguards",
    "usage policy",
    "monitoring",
    "known limitations",
    "escalation",
]


def validate_all(model_card_path: str, system_card_path: str) -> bool:
    """Returns True if both documents pass (pass_rate >= 0.8)."""
    mc = ValidationResult(model_card_path, MODEL_CARD_SECTIONS)
    sc = ValidationResult(system_card_path, SYSTEM_CARD_SECTIONS)
    mc.compute()
    sc.compute()
    mc.report()
    sc.report()
    all_pass = mc.pass_rate >= 0.8 and sc.pass_rate >= 0.8
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ─── The launch review from the chapter's story ──────────────────────────────

# Maya's three questions. A feature launches only when its system card answers all three:
# an owner and an out-of-hours contact in its front matter, and a Commitments section that
# says what the system may promise.
LAUNCH_QUESTIONS = [
    ("Who owns this if it goes wrong?", "owner"),
    ("What may the system promise?", "commitments"),
    ("Who is called at two in the morning?", "on_call"),
]


def read_card(path) -> tuple[dict, dict]:
    """Return a card's front-matter fields and its sections, {heading: body}."""
    text = Path(path).read_text(encoding="utf-8")
    fields, sections, heading = {}, {}, None
    lines = text.splitlines()
    if lines and lines[0] == "---":
        end = lines.index("---", 1)
        for line in lines[1:end]:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
        lines = lines[end + 1 :]
    for line in lines:
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            sections[heading] = []
        elif heading and line.strip():
            sections[heading].append(line.strip().lstrip("- "))
    return fields, {h: "; ".join(lines) for h, lines in sections.items()}


def launch_review(path) -> dict[str, str]:
    """Answer each launch question from the card; an empty answer means it has none."""
    fields, sections = read_card(path)
    return {
        question: (fields.get(source) or sections.get(source, "")).strip()
        for question, source in LAUNCH_QUESTIONS
    }


def review_launch(path) -> bool:
    answers = launch_review(path)
    print(f"\n=== Launch review: {Path(path).name} ===")
    for question, answer in answers.items():
        print(f"  {question:<38} {textwrap.shorten(answer, 72, placeholder=' ...') or 'NO ANSWER'}")
    # TODO 4: approve only if every question has an answer. As supplied, every feature
    #   launches, with or without an owner, a cap, or anyone to call at night.
    approved = True
    print(f"Launch: {'APPROVED' if approved else 'WAIT: the card does not answer every question'}")
    return approved


if __name__ == "__main__":
    here = Path(__file__).parent  # the cards sit next to this script
    validate_all(here / "model_card.md", here / "system_card.md")
    review_launch(here / "voucher_card_draft.md")
    review_launch(here / "voucher_system_card.md")
