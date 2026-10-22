"""Lab 14 — Two-Agent Research Pipeline (starter).

This file RUNS as supplied. The Writer ignores its sources, and a worker whose task
raises dies without telling anyone. Complete the two TODOs.

    python src/multi_agent_pipeline.py
"""

import itertools
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# ─── Part 1: messages, queue and result store (Sections 14.6 and 14.7) ────────


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""  # "" means broadcast
    message_type: str = ""  # "task", "result", "query", "response", "error", "status"
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # Links responses to requests
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    priority: int = 5  # 1 (highest) to 10 (lowest)
    ttl: int = 300  # Time-to-live in seconds; 0 = no expiry


class TaskQueue:
    """Thread-safe task distribution queue."""

    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._in_flight: dict[str, AgentMessage] = {}
        self._lock = threading.Lock()
        # Tie-breaker: two messages with the same priority and timestamp would
        # otherwise make the queue compare AgentMessage objects, which raises TypeError
        self._seq = itertools.count()

    def enqueue(self, msg: AgentMessage) -> None:
        self._queue.put((msg.priority, msg.timestamp, next(self._seq), msg))

    def dequeue(self, timeout: float = 1.0) -> Optional[AgentMessage]:
        try:
            *_, msg = self._queue.get(timeout=timeout)
            with self._lock:
                self._in_flight[msg.message_id] = msg
            return msg
        except queue.Empty:
            return None

    def acknowledge(self, message_id: str) -> None:
        with self._lock:
            self._in_flight.pop(message_id, None)

    def requeue_in_flight(self) -> int:
        """Requeue all in-flight messages (e.g., after a worker crash)."""
        with self._lock:
            count = len(self._in_flight)
            for msg in self._in_flight.values():
                self._queue.put((msg.priority, msg.timestamp, next(self._seq), msg))
            self._in_flight.clear()
        return count

    def size(self) -> int:
        return self._queue.qsize()


class ResultStore:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._lock = threading.Lock()

    def write(self, key: str, value: str) -> None:
        with self._lock:
            self._store[key] = value

    def read(self, key: str) -> str | None:
        with self._lock:
            return self._store.get(key)


# ─── Mock search, as in Chapter 11 ────────────────────────────────────────────

SEARCH_RESULTS = {
    "eu ai act": "The EU AI Act, the first comprehensive AI law, entered into force on "
    "1 August 2024.",
    "nobel physics 2024": "The 2024 Nobel Prize in Physics went to John Hopfield and Geoffrey "
    "Hinton for foundational work that enables machine learning with artificial neural "
    "networks.",
    "nobel chemistry 2024": "The 2024 Nobel Prize in Chemistry went to David Baker for "
    "computational protein design, and to Demis Hassabis and John Jumper for protein "
    "structure prediction.",
}


def web_search(query: str) -> str:
    key = query.lower().strip()
    for k, v in SEARCH_RESULTS.items():
        if k in key or key in k:
            return v
    return f"No results found for: {query}"


# ─── Parts 2 and 3: the worker agents ─────────────────────────────────────────


class WorkerAgent(threading.Thread):
    """Pulls tasks addressed to it from the shared queue and reports to the orchestrator."""

    def __init__(self, agent_id: str, tasks: TaskQueue, inbox: TaskQueue, store: ResultStore):
        super().__init__(daemon=True, name=agent_id)
        self.agent_id = agent_id
        self.tasks, self.inbox, self.store = tasks, inbox, store
        self.stopped = threading.Event()

    def run(self) -> None:
        while not self.stopped.is_set():
            msg = self.tasks.dequeue(timeout=0.1)
            if msg is None:
                continue
            self.tasks.acknowledge(msg.message_id)
            if msg.recipient_id not in ("", self.agent_id):
                # Not ours: put it back for the agent it is addressed to
                self.tasks.enqueue(msg)
                time.sleep(0.01)
                continue
            # TODO 2: If handle() raises, reply with message_type "error" and
            #   payload {"error": <message>} instead, so the orchestrator learns of the
            #   failure at once rather than waiting for a reply that never comes.
            output = self.handle(msg)
            self.store.write(msg.message_id, output)
            reply = AgentMessage(
                sender_id=self.agent_id,
                recipient_id="orchestrator",
                message_type="result",
                correlation_id=msg.message_id,
                payload={"key": msg.message_id},
            )
            self.inbox.enqueue(reply)

    def handle(self, msg: AgentMessage) -> str:
        raise NotImplementedError


class ResearcherAgent(WorkerAgent):
    def handle(self, msg: AgentMessage) -> str:
        return web_search(msg.payload["query"])


class WriterAgent(WorkerAgent):
    def handle(self, msg: AgentMessage) -> str:
        # TODO 1: Read each research result named in msg.payload["sources"] from the
        #   result store, and list them as "- <finding>" lines.
        bullets = ""
        return f"{msg.payload['title']}\n\n{bullets}"


# ─── Part 4: the orchestrator ─────────────────────────────────────────────────


class Orchestrator:
    def __init__(self, tasks: TaskQueue, inbox: TaskQueue, store: ResultStore):
        self.tasks, self.inbox, self.store = tasks, inbox, store
        self.log: list[str] = []
        self.sent: list[AgentMessage] = []

    def say(self, line: str) -> None:
        self.log.append(line)
        print(line)

    def send(self, recipient: str, payload: dict, shown: str = "") -> AgentMessage:
        msg = AgentMessage(
            sender_id="orchestrator", recipient_id=recipient, message_type="task", payload=payload
        )
        self.sent.append(msg)
        self.tasks.enqueue(msg)
        self.say(f"orchestrator -> {recipient}: task {len(self.sent)} {shown or payload}")
        return msg

    def number(self, message_id: str) -> int:
        """The task's position in send order, for readable logs."""
        return next(i for i, m in enumerate(self.sent, 1) if m.message_id == message_id)

    def wait_for(self, sent: list[AgentMessage], timeout: float = 10.0) -> dict[str, AgentMessage]:
        """Collect the reply to each sent task, matched by correlation_id."""
        pending = {m.message_id for m in sent}
        replies: dict[str, AgentMessage] = {}
        deadline = time.monotonic() + timeout
        while pending and time.monotonic() < deadline:
            reply = self.inbox.dequeue(timeout=0.1)
            if reply is None:
                continue
            self.inbox.acknowledge(reply.message_id)
            if reply.correlation_id in pending:
                pending.discard(reply.correlation_id)
                replies[reply.correlation_id] = reply
                self.say(
                    f"{reply.sender_id} -> orchestrator: {reply.message_type} "
                    f"for task {self.number(reply.correlation_id)}"
                )
        if pending:
            raise TimeoutError(f"{len(pending)} task(s) did not reply in {timeout} s")
        return replies

    def run(self, goal: str, queries: list[str]) -> str:
        self.say(f"Goal: {goal}\n")
        research = [self.send("researcher", {"query": q}) for q in queries]
        replies = self.wait_for(research)
        failed = [r for r in replies.values() if r.message_type == "error"]
        if failed:
            raise RuntimeError(f"research failed: {failed[0].payload['error']}")
        writing = self.send(
            "writer",
            {"title": "AI advances in 2024", "sources": [m.message_id for m in research]},
            shown=f"write 'AI advances in 2024' from the results of tasks 1-{len(research)}",
        )
        self.wait_for([writing])
        report = self.store.read(writing.message_id)
        self.say(f"\n=== REPORT ===\n{report}")
        return report


# ─── Part 5: run the pipeline ─────────────────────────────────────────────────


def run_pipeline() -> str:
    tasks, inbox, store = TaskQueue(), TaskQueue(), ResultStore()
    workers = [
        ResearcherAgent("researcher", tasks, inbox, store),
        WriterAgent("writer", tasks, inbox, store),
    ]
    for w in workers:
        w.start()
    try:
        return Orchestrator(tasks, inbox, store).run(
            "Write a brief report on AI advances in 2024.",
            ["EU AI Act", "Nobel physics 2024", "Nobel chemistry 2024"],
        )
    finally:
        for w in workers:
            w.stopped.set()
            w.join(timeout=1)


if __name__ == "__main__":
    run_pipeline()
