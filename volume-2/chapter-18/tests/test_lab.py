"""Tests for Lab 18. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import build_legal_library, mock_llm, semver_key  # noqa: E402

CLASSIFIER = "legal/document-classification"


@pytest.fixture
def library():
    return build_legal_library()


def test_semver_orders_numerically():
    assert semver_key("1.10.0") > semver_key("1.9.0")
    assert semver_key("2.0.0") > semver_key("1.99.99")


def test_five_prompts_registered(library):
    assert len(library.list_all()) == 5


def test_duplicate_registration_is_rejected(library):
    with pytest.raises(ValueError):
        library.register(library.get(CLASSIFIER))


def test_latest_is_the_highest_version(library):
    for version in ("1.9.0", "1.10.0"):
        library.update(CLASSIFIER, version, {}, "test", "tests")
    assert library.get(CLASSIFIER).version == "1.10.0"


def test_versions_listed_in_numeric_order(library):
    for version in ("1.9.0", "1.10.0"):
        library.update(CLASSIFIER, version, {}, "test", "tests")
    versions = [v["version"] for v in library.list_versions(CLASSIFIER)]
    assert versions == ["1.2.0", "1.9.0", "1.10.0"]


def test_latest_skips_deprecated(library):
    library.update(CLASSIFIER, "1.3.0", {}, "test", "tests")
    library.deprecate(CLASSIFIER, "1.3.0", sunset_date="2027-06-01")
    assert library.get(CLASSIFIER).version == "1.2.0"


def test_deprecated_version_warns(library, capsys):
    library.deprecate(CLASSIFIER, "1.2.0", sunset_date="2027-06-01", deprecated_by="x@2")
    capsys.readouterr()
    library.get(CLASSIFIER, version="1.2.0")
    out = capsys.readouterr().out
    assert "deprecated" in out and "2027-06-01" in out


def test_search_filters_by_tag_and_task(library):
    found = library.search(tags=["domain:legal"], task_type="classification")
    assert [r["prompt_id"] for r in found] == [CLASSIFIER]


def test_search_with_unknown_tag_finds_nothing(library):
    assert library.search(tags=["domain:medical"]) == []


def test_classifier_output_matches_schema(library):
    assert library.get(CLASSIFIER).run_schema_test(llm_fn=mock_llm)["passed"]


def test_changelog_records_every_change(library):
    library.update(CLASSIFIER, "1.3.0", {}, "MINOR: test", "tests")
    library.deprecate(CLASSIFIER, "1.2.0", sunset_date="2027-06-01")
    actions = [e["action"] for e in library.changelog(CLASSIFIER)]
    assert actions == ["register", "update", "deprecate"]
