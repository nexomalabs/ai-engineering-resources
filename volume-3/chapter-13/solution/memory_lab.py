"""Lab 13 — Agent Memory System with SQLite (reference solution).

Runs the lab's six parts against AgentMemoryStore: schema, episodic records over three
backdated sessions, semantic facts, a procedure, hybrid retrieval at two recency weights,
and forgetting. Run from the lab folder; it writes memory_lab.db there:

    python solution/memory_lab.py
"""

from datetime import datetime, timedelta
from pathlib import Path

from agent_memory_store import AgentMemoryStore, utcnow

AGENT = "agent-lab"
DB_PATH = Path("memory_lab.db")

# (session, days ago, event type, content, importance)
EPISODES = [
    ("sess-1", 14, "observation", "Bob asked how async programming works in Python.", 0.6),
    (
        "sess-1",
        14,
        "action",
        "Explained Python's async and await keywords with an asyncio example.",
        0.5,
    ),
    ("sess-1", 14, "observation", "Bob confirmed the async explanation was helpful.", 0.8),
    ("sess-2", 7, "action", "Surfaced Session 1: Bob is learning async Python.", 0.4),
    ("sess-2", 7, "observation", "Bob asked how to write async endpoints in FastAPI.", 0.7),
    ("sess-3", 0.04, "observation", "Bob asked for a code review of his endpoint.", 0.6),
    (
        "sess-3",
        0.04,
        "action",
        "Reviewed the endpoint: a blocking database call stalls the event loop.",
        0.9,
    ),
]


def part1_setup(path: Path = DB_PATH) -> AgentMemoryStore:
    print("Part 1 — Schema")
    path.unlink(missing_ok=True)  # start fresh, so reruns do not duplicate records
    store = AgentMemoryStore(str(path))
    tables = [
        r[0]
        for r in store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
    ]
    print(f"  tables: {tables}")
    return store


def part2_episodes(store: AgentMemoryStore, now: datetime) -> list[int]:
    print("\nPart 2 — Episodic records")
    ids = []
    for i, (session, days_ago, event_type, content, importance) in enumerate(EPISODES):
        # Records within a session are a minute apart, in order
        when = now - timedelta(days=days_ago) + timedelta(minutes=i)
        ids.append(
            store.write_episode(
                session, AGENT, event_type, content, importance=importance, timestamp=when
            )
        )
    for session in ("sess-1", "sess-2", "sess-3"):
        count = store.conn.execute(
            "SELECT COUNT(*) FROM episodic WHERE session_id = ?", (session,)
        ).fetchone()[0]
        print(f"  {session}: {count} records")
    return ids


def part3_facts(store: AgentMemoryStore) -> None:
    print("\nPart 3 — Semantic facts")
    store.write_fact("user:bob", "prefers_language", "Python", source="sess-1")
    store.write_fact("user:bob", "project_type", "REST API built with FastAPI", source="sess-2")
    store.write_fact("user:bob", "experience_level", "learning async programming", source="sess-1")
    store.write_fact(
        "user:bob", "prefers_explanations", "short, with a code example", source="sess-1"
    )
    store.write_fact(
        "tool:code_review", "capability", "flags blocking calls in async code", source="sess-3"
    )
    for subject in ("user:bob", "tool:code_review"):
        for f in store.get_facts_about(subject):
            print(f"  {f['subject']} {f['predicate']} = {f['object_']}")


def part4_procedure(store: AgentMemoryStore) -> list[str]:
    print("\nPart 4 — Procedural memory")
    store.write_procedure(
        "code_review",
        "1. Read the code. 2. Check for blocking calls in async functions. "
        "3. Check error handling. 4. Suggest improvements with examples.",
        "Use when asked to review Python code.",
    )
    proc = store.get_procedure("code_review")
    context = [f"PROCEDURE (code_review): {proc['procedure']}"]
    context += [
        f"MEMORY: {r['content']}" for r in store.retrieve_relevant(AGENT, "code review", n=2)
    ]
    for line in context:
        print(f"  {line}")
    return context


def part5_retrieval(store: AgentMemoryStore) -> tuple[list[int], list[int]]:
    print("\nPart 5 — Hybrid retrieval: 'async Python FastAPI'")
    picks = {}
    for weight in (0.3, 0.8):
        rows = store.retrieve_relevant(AGENT, "async Python FastAPI", n=3, recency_weight=weight)
        picks[weight] = [r["id"] for r in rows]
        print(f"  recency_weight={weight}:")
        for r in rows:
            print(f"    [{r['session_id']}] {r['content']}")
    print(
        "  At 0.3, keyword relevance dominates, so the older sessions about async Python and\n"
        "  FastAPI surface. At 0.8, recency dominates, so the recent code review surfaces\n"
        "  although it shares no keywords with the query."
    )
    return picks[0.3], picks[0.8]


def part6_forgetting(store: AgentMemoryStore, ids: list[int]) -> int:
    print("\nPart 6 — Forgetting")
    for episode_id in ids[:3]:  # the three oldest records
        store.conn.execute("UPDATE episodic SET importance = 0.3 WHERE id = ?", (episode_id,))
    store.conn.commit()
    deleted = store.forget_old_episodes(days=3, min_importance=0.7)
    print(f"  deleted {deleted} record(s) older than 3 days with importance below 0.7")
    for r in store.conn.execute("SELECT session_id, importance, content FROM episodic ORDER BY id"):
        print(f"  kept [{r['session_id']}] importance {r['importance']}: {r['content']}")
    return deleted


def main() -> None:
    store = part1_setup()
    now = utcnow()
    ids = part2_episodes(store, now)
    part3_facts(store)
    part4_procedure(store)
    part5_retrieval(store)
    part6_forgetting(store, ids)
    store.close()
    print(f"\nDatabase written to {DB_PATH}")


if __name__ == "__main__":
    main()
