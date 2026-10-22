"""AgentMemoryStore from Section 13.10: SQLite-backed episodic, semantic and procedural memory."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentMemoryStore:
    """SQLite-backed agent memory with episodic, semantic, and procedural storage."""

    def __init__(self, db_path: str = "agent_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS episodic (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                session_id  TEXT NOT NULL,
                agent_id    TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                content     TEXT NOT NULL,
                importance  REAL DEFAULT 0.5,
                tags        TEXT DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS semantic (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                subject       TEXT NOT NULL,
                predicate     TEXT NOT NULL,
                object_       TEXT NOT NULL,
                confidence    REAL DEFAULT 1.0,
                source        TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                last_verified TEXT,
                expiry        TEXT,
                UNIQUE(subject, predicate)
            );

            CREATE TABLE IF NOT EXISTS procedural (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type    TEXT NOT NULL UNIQUE,
                procedure    TEXT NOT NULL,
                success_rate REAL DEFAULT 1.0,
                usage_count  INTEGER DEFAULT 0,
                last_used    TEXT NOT NULL,
                conditions   TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic(session_id);
            CREATE INDEX IF NOT EXISTS idx_episodic_time ON episodic(timestamp);
            CREATE INDEX IF NOT EXISTS idx_semantic_subject ON semantic(subject);
        """)
        self.conn.commit()

    # ─── Episodic write ───────────────────────────────────────────────────────

    def write_episode(
        self,
        session_id: str,
        agent_id: str,
        event_type: str,
        content: str,
        importance: float = 0.5,
        tags: list[str] | None = None,
        timestamp: datetime | None = None,
    ) -> int:
        """Record an event. Pass `timestamp` (timezone-aware) to import past events."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO episodic
               (timestamp, session_id, agent_id, event_type, content, importance, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                # TODO 1: Use `timestamp` when one is given, so past events keep their
                #   real time; otherwise use utcnow().
                utcnow().isoformat(),
                session_id,
                agent_id,
                event_type,
                content,
                importance,
                json.dumps(tags or []),
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    # ─── Episodic read ────────────────────────────────────────────────────────

    def get_recent_episodes(self, agent_id: str, n: int = 10) -> list[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM episodic
               WHERE agent_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, n),
        )
        return cursor.fetchall()

    def search_episodes(self, agent_id: str, keyword: str, n: int = 10) -> list[sqlite3.Row]:
        """Keyword search across episode content."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM episodic
               WHERE agent_id = ? AND content LIKE ?
               ORDER BY importance DESC, timestamp DESC LIMIT ?""",
            (agent_id, f"%{keyword}%", n),
        )
        return cursor.fetchall()

    # ─── Semantic write ───────────────────────────────────────────────────────

    def write_fact(
        self,
        subject: str,
        predicate: str,
        object_: str,
        confidence: float = 1.0,
        source: str = "agent",
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO semantic
               (subject, predicate, object_, confidence, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(subject, predicate) DO UPDATE SET
                   object_ = excluded.object_,
                   confidence = excluded.confidence,
                   source = excluded.source,
                   last_verified = excluded.created_at""",
            (subject, predicate, object_, confidence, source, utcnow().isoformat()),
        )
        self.conn.commit()

    def get_facts_about(self, subject: str) -> list[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM semantic WHERE subject = ?", (subject,))
        return cursor.fetchall()

    # ─── Procedural write/read ────────────────────────────────────────────────

    def write_procedure(self, task_type: str, procedure: str, conditions: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO procedural
               (task_type, procedure, usage_count, last_used, conditions)
               VALUES (?, ?, 0, ?, ?)
               ON CONFLICT(task_type) DO UPDATE SET
                   procedure = excluded.procedure,
                   conditions = excluded.conditions""",
            (task_type, procedure, utcnow().isoformat(), conditions),
        )
        self.conn.commit()

    def get_procedure(self, task_type: str) -> Optional[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM procedural WHERE task_type = ?", (task_type,))
        row = cursor.fetchone()
        if row:
            # Update usage statistics
            cursor.execute(
                """UPDATE procedural SET usage_count = usage_count + 1,
                   last_used = ? WHERE task_type = ?""",
                (utcnow().isoformat(), task_type),
            )
            self.conn.commit()
        return row

    # ─── Forgetting ───────────────────────────────────────────────────────────

    def forget_old_episodes(self, days: int = 90, min_importance: float = 0.7) -> int:
        """Delete episodes older than `days` days unless importance >= min_importance."""
        cutoff = (utcnow() - timedelta(days=days)).isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            """DELETE FROM episodic
               WHERE timestamp < ?""",
            # TODO 3: Delete only records that are old AND below min_importance;
            #   an important memory must survive however old it is.
            (cutoff,),
        )
        self.conn.commit()
        return cursor.rowcount

    # ─── Hybrid retrieval ─────────────────────────────────────────────────────

    def retrieve_relevant(
        self, agent_id: str, query: str, n: int = 5, recency_weight: float = 0.3
    ) -> list[dict]:
        """
        Hybrid retrieval: combines keyword relevance with recency scoring.
        In production, replace keyword matching with embedding similarity.
        """
        keywords = [w.lower() for w in query.split() if len(w) > 3]
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM episodic WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 100",
            (agent_id,),
        )
        rows = cursor.fetchall()

        scored: list[tuple[float, dict]] = []
        now = utcnow()

        for row in rows:
            content_lower = row["content"].lower()
            keyword_hits = sum(1 for kw in keywords if kw in content_lower)
            relevance = keyword_hits / max(len(keywords), 1)

            ts = datetime.fromisoformat(row["timestamp"])
            age_hours = (now - ts).total_seconds() / 3600
            recency = 1.0 / (1.0 + age_hours / 24)  # Decay over days

            # TODO 2: Blend the two signals: recency_weight x recency plus
            #   (1 - recency_weight) x relevance.
            score = relevance
            scored.append((score, dict(row)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:n]]

    def close(self) -> None:
        self.conn.close()


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store = AgentMemoryStore(":memory:")  # In-memory DB for demo

    # Write some episodes
    store.write_episode(
        "sess-001",
        "agent-1",
        "observation",
        "User Alice prefers Python over JavaScript.",
        importance=0.9,
    )
    store.write_episode(
        "sess-001",
        "agent-1",
        "action",
        "Sent code example using Python dataclasses.",
        importance=0.6,
    )
    store.write_episode(
        "sess-002",
        "agent-1",
        "observation",
        "Alice's project uses FastAPI and PostgreSQL.",
        importance=0.85,
    )

    # Write semantic facts
    store.write_fact("user:alice", "prefers_language", "Python", source="sess-001")
    store.write_fact("project:alice-api", "uses_framework", "FastAPI", source="sess-002")

    # Write a procedure
    store.write_procedure(
        "code_review",
        "1. Read the code. 2. Identify style issues. 3. Check logic. 4. Suggest improvements.",
        "Use when asked to review Python code.",
    )

    # Retrieve relevant episodes
    results = store.retrieve_relevant("agent-1", "Python FastAPI project")
    print("Relevant memories:")
    for r in results:
        print(f"  [{r['event_type']}] {r['content']}")

    # Get facts about Alice
    facts = store.get_facts_about("user:alice")
    print("\nFacts about Alice:")
    for f in facts:
        print(f"  {f['subject']} {f['predicate']} {f['object_']}")

    store.close()
