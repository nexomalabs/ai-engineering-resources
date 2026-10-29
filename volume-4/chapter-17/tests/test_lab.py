"""Tests for Lab 17. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    FOUNDATIONS,
    RoadmapInitiative,
    build_medicore_roadmap,
    missing_foundations,
    parse_cost,
    print_roadmap,
)


@pytest.mark.parametrize(
    ("text", "dollars"),
    [("$80K", 80_000), ("$1.2M", 1_200_000), ("~$3.95M", 3_950_000), ("$500", 500), ("TBD", 0)],
)
def test_parse_cost(text, dollars):
    assert parse_cost(text) == dollars


def test_roadmap_is_well_formed():
    roadmap = build_medicore_roadmap()
    names = {i.name for i in roadmap}
    assert len(names) == len(roadmap) == 10
    for i in roadmap:
        assert 1 <= i.quarter_start <= i.quarter_end <= 12
        assert (i.quarter_start - 1) // 4 + 1 == i.phase
        assert set(i.dependencies) <= names
        assert set(i.establishes) <= set(FOUNDATIONS)


def test_total_is_computed_from_the_estimates(capsys):
    print_roadmap(build_medicore_roadmap())
    assert "Total estimated investment: ~$4.10M over 3 years" in capsys.readouterr().out


def test_total_follows_the_data(capsys):
    extra = RoadmapInitiative("Extra", "People", 1, 1, 1, "d", "m", estimated_cost="$50K")
    print_roadmap(build_medicore_roadmap() + [extra])
    assert "~$4.15M over 3 years" in capsys.readouterr().out


def test_quarters_are_shown_within_their_year(capsys):
    print_roadmap(build_medicore_roadmap())
    out = capsys.readouterr().out
    assert "AI Platform Build                  Technology  Q1–Q3" in out
    assert "Q5" not in out


def test_the_first_draft_ships_ai_before_its_foundations_are_in_place():
    draft = [i for i in build_medicore_roadmap() if i.name != "Production Foundations"]
    missing = missing_foundations(draft)
    assert missing["Pilot: AI Clinical Documentation Assistant"] == [
        "evaluation sets",
        "cost attribution",
        "canary releases",
        "model-version logging",
    ]
    assert missing["Proprietary Clinical AI Model"] == ["canary releases", "model-version logging"]
    assert len(missing) == 4


def test_every_ai_release_in_the_roadmap_starts_with_all_the_foundations():
    assert missing_foundations(build_medicore_roadmap()) == {}


def test_a_foundation_counts_only_once_its_initiative_has_ended():
    evals = RoadmapInitiative(
        "Evals", "Process", 1, 1, 2, "d", "m", establishes=["evaluation sets"]
    )
    early = RoadmapInitiative("Early", "Process", 1, 2, 3, "d", "m", ships_ai=True)
    later = RoadmapInitiative("Later", "Process", 1, 3, 4, "d", "m", ships_ai=True)
    missing = missing_foundations([evals, early, later])
    assert "evaluation sets" in missing["Early"]
    assert "evaluation sets" not in missing["Later"]
