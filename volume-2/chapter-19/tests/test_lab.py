"""Tests for Lab 19. Run against solution/ in CI, in fixture mode (no API key)."""

import os
import sys
from pathlib import Path

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    ARTIFACT,
    FIXTURES,
    PLANTED_DEFECTS,
    found_lines,
    run_board,
    run_critique_board,
    synthesize,
)


def ranked():
    return synthesize(run_board(ARTIFACT))


def test_runs_without_an_api_key():
    assert "OPENAI_API_KEY" not in os.environ or os.environ["NEXOMA_LAB_MODE"] == "fixture"
    assert set(run_board(ARTIFACT)) == {"engineer", "security", "red_team"}


def test_findings_on_the_same_line_are_merged():
    lines = [f.line for f in ranked()]
    assert len(lines) == len(set(lines))


def test_every_severity_is_kept():
    line6 = next(f for f in ranked() if f.line == 6)
    assert line6.severities == {"engineer": "major", "red_team": "minor"}
    assert line6.severity == "major"


def test_ranked_by_severity_then_agreement():
    assert [f.line for f in ranked()] == [2, 6, 3, 9]


def test_single_reviewer_findings_are_not_dropped():
    singles = {f.line for f in ranked() if len(f.reviewers) == 1}
    assert singles == {3, 9}


def test_board_finds_all_planted_defects():
    assert set(PLANTED_DEFECTS) <= found_lines(ranked())


def test_single_prompt_fixture_misses_a_defect():
    assert set(PLANTED_DEFECTS) - found_lines(FIXTURES["single_prompt"]["findings"])


def test_critique_board_takes_no_vote(capsys):
    run_critique_board()
    out = capsys.readouterr().out
    assert "no majority vote" in out
    assert "DO NOT BUILD (risk_manager)" in out
