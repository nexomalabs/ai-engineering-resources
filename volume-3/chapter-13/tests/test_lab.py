"""Tests for Lab 13. Run against solution/ in CI."""

import sys
from datetime import timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import memory_lab  # noqa: E402
from agent_memory_store import AgentMemoryStore, utcnow  # noqa: E402


@pytest.fixture
def store():
    s = AgentMemoryStore(":memory:")
    yield s
    s.close()


def test_schema_has_the_three_tables(tmp_path):
    s = memory_lab.part1_setup(tmp_path / "m.db")
    names = {r[0] for r in s.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"episodic", "semantic", "procedural"} <= names
    s.close()


def test_backdated_timestamp_is_kept(store):
    when = utcnow() - timedelta(days=10)
    eid = store.write_episode("s", "a", "observation", "old event", timestamp=when)
    row = store.conn.execute("SELECT timestamp FROM episodic WHERE id = ?", (eid,)).fetchone()
    assert row[0] == when.isoformat()


def test_fact_upsert_updates_instead_of_duplicating(store):
    store.write_fact("user:bob", "prefers_language", "JavaScript")
    store.write_fact("user:bob", "prefers_language", "Python")
    facts = store.get_facts_about("user:bob")
    assert [f["object_"] for f in facts] == ["Python"]


def test_procedure_use_is_counted(store):
    store.write_procedure("code_review", "steps", "when asked")
    store.get_procedure("code_review")
    store.get_procedure("code_review")
    row = store.conn.execute("SELECT usage_count FROM procedural").fetchone()
    assert row[0] == 2


def populated():
    s = AgentMemoryStore(":memory:")
    ids = memory_lab.part2_episodes(s, utcnow())
    return s, ids


def test_recency_weight_changes_what_surfaces(capsys):
    s, _ = populated()
    low, high = memory_lab.part5_retrieval(s)
    assert {
        r["session_id"]
        for r in s.conn.execute(
            f"SELECT session_id FROM episodic WHERE id IN ({','.join(map(str, low))})"
        )
    } <= {"sess-1", "sess-2"}
    assert high[:2] == [7, 6]  # the two recent code-review records
    s.close()


def test_relevance_wins_when_recency_is_equal(store):
    now = utcnow()
    store.write_episode("s", "a", "observation", "nothing related", timestamp=now)
    store.write_episode("s", "a", "observation", "async python fastapi notes", timestamp=now)
    top = store.retrieve_relevant("a", "async Python FastAPI", n=1, recency_weight=0.3)[0]
    assert top["content"] == "async python fastapi notes"


def test_forgetting_keeps_important_and_recent_records(capsys):
    s, ids = populated()
    deleted = memory_lab.part6_forgetting(s, ids)
    kept = [r[0] for r in s.conn.execute("SELECT id FROM episodic ORDER BY id")]
    assert deleted == 4
    assert kept == [5, 6, 7]
    s.close()


def test_main_writes_the_database(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    memory_lab.main()
    assert (tmp_path / "memory_lab.db").exists()
    assert "Part 6" in capsys.readouterr().out
