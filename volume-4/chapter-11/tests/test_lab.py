"""Tests for Lab 11. Run against solution/ in CI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from governance_validator import (  # noqa: E402
    MODEL_CARD_SECTIONS,
    SYSTEM_CARD_SECTIONS,
    ValidationResult,
    validate_all,
)

SOLUTION = ROOT / "solution"


def check(tmp_path, text, sections):
    doc = tmp_path / "card.md"
    doc.write_text(text, encoding="utf-8")
    result = ValidationResult(str(doc), sections)
    result.compute()
    return result


def test_reference_cards_pass_completely(capsys):
    assert validate_all(SOLUTION / "model_card.md", SOLUTION / "system_card.md")
    out = capsys.readouterr().out
    assert "Pass rate: 100% (8/8 sections)" in out
    assert "Pass rate: 100% (7/7 sections)" in out
    assert "Overall: PASS" in out


def test_headings_count():
    result = check_text("# Card\n\n## Model Details\n\n## Intended Use\n")
    assert result.found_sections == ["model details", "intended use"]


def check_text(text):
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        return check(Path(tmp), text, ["model details", "intended use"])


def test_a_mention_in_a_paragraph_does_not_count():
    result = check_text("## Model Details\n\nThis card covers the intended use of the model.\n")
    assert result.missing_sections == ["intended use"]
    assert result.pass_rate == 0.5


def test_heading_match_ignores_case_and_extra_words():
    result = check_text("## MODEL DETAILS\n\n### Intended Use and Users\n")
    assert result.pass_rate == 1.0


def test_front_matter_is_not_a_heading():
    result = check_text("---\nmodel_details: yes\n---\n\n## Intended Use\n")
    assert result.missing_sections == ["model details"]


def test_threshold_is_80_percent(tmp_path, capsys):
    mc = tmp_path / "model_card.md"
    sc = tmp_path / "system_card.md"
    mc.write_text("\n".join(f"## {s}" for s in MODEL_CARD_SECTIONS[:6]), encoding="utf-8")
    sc.write_text("\n".join(f"## {s}" for s in SYSTEM_CARD_SECTIONS), encoding="utf-8")
    assert not validate_all(mc, sc)  # 6/8 = 75%
    mc.write_text("\n".join(f"## {s}" for s in MODEL_CARD_SECTIONS[:7]), encoding="utf-8")
    assert validate_all(mc, sc)  # 7/8 = 87.5%


def test_report_lists_missing_sections(tmp_path, capsys):
    result = check(tmp_path, "## Safeguards\n", SYSTEM_CARD_SECTIONS)
    result.report()
    out = capsys.readouterr().out
    assert "=== card.md ===" in out
    assert "MISSING: system overview, safety evaluation" in out
