"""Tests for Lab 17. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import RoadmapInitiative, build_medicore_roadmap, parse_cost, print_roadmap  # noqa: E402


@pytest.mark.parametrize(
    ("text", "dollars"),
    [("$80K", 80_000), ("$1.2M", 1_200_000), ("~$3.95M", 3_950_000), ("$500", 500), ("TBD", 0)],
)
def test_parse_cost(text, dollars):
    assert parse_cost(text) == dollars


def test_roadmap_is_well_formed():
    roadmap = build_medicore_roadmap()
    names = {i.name for i in roadmap}
    assert len(names) == len(roadmap) == 9
    for i in roadmap:
        assert 1 <= i.quarter_start <= i.quarter_end <= 12
        assert (i.quarter_start - 1) // 4 + 1 == i.phase
        assert set(i.dependencies) <= names


def test_total_is_computed_from_the_estimates(capsys):
    print_roadmap(build_medicore_roadmap())
    assert "Total estimated investment: ~$3.95M over 3 years" in capsys.readouterr().out


def test_total_follows_the_data(capsys):
    extra = RoadmapInitiative("Extra", "People", 1, 1, 1, "d", "m", estimated_cost="$50K")
    print_roadmap(build_medicore_roadmap() + [extra])
    assert "~$4.00M over 3 years" in capsys.readouterr().out


def test_quarters_are_shown_within_their_year(capsys):
    print_roadmap(build_medicore_roadmap())
    out = capsys.readouterr().out
    assert "AI Platform Build                  Technology  Q1–Q3" in out
    assert "Q5" not in out
