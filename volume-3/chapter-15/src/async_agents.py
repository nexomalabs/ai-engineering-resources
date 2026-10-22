"""Lab 15 — Async Agent Communication System (starter).

This file RUNS as supplied. Agents process expired messages, run a resent task again
instead of returning the result they already produced, and the heartbeat monitor reports
the same failure over and over. Complete the three TODOs.

    python src/async_agents.py
"""

import asyncio
import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

RESULT_TIMEOUT = 1.0  # seconds to wait for a result before resending (lab text: 5)
MAX_RETRIES = 3
HEARTBEAT_INTERVAL = 0.2
HEARTBEAT_TIMEOUT = 0.8

# ─── Part 1: message infrastructure (Sections 15.3 and 15.6) ──────────────────


@dataclass
class MessageEnvelope:
    """Standard message envelope for all inter-agent communication."""

    # Routing
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""  # "" = broadcast
    reply_to: Optional[str] = None  # Queue/channel for replies

    # Classification
    message_type: str = ""  # task | result | query | response | error | heartbeat
    schema_version: str = "1.0"

    # Content
    payload: dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None  # Groups related messages
    priority: int = 5  # 1 = highest, 10 = lowest
    ttl_seconds: int = 300  # 0 = no expiry

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str) -> "MessageEnvelope":
        return cls(**json.loads(data))

    def is_expired(self) -> bool:
        if self.ttl_seconds == 0:
            return False
        sent_at = datetime.fromisoformat(self.timestamp)
        age = (datetime.now(timezone.utc) - sent_at).total_seconds()
        return age > self.ttl_seconds


class MessageLog:
    def __init__(self):
        self._log: list[MessageEnvelope] = []

    def record(self, msg: MessageEnvelope) -> None:
        self._log.append(msg)

    def get_by_correlation(self, correlation_id: str) -> list[MessageEnvelope]:
        return [m for m in self._log if m.correlation_id == correlation_id]

    def summary(self) -> str:
        lines = []
        for m in self._log:
            lines.append(
                f"{m.sender_id} → {m.recipient_id} | {m.message_type} | "
                f"corr={(m.correlation_id or '-')[:8]}"
            )
        return "\n".join(lines)


class AgentBus:
    """Point-to-point bus over asyncio queues, with optional simulated message loss."""

    def __init__(
        self,
        drop_rate: float = 0.0,
        rng: Optional[random.Random] = None,
        log: Optional[MessageLog] = None,
    ):
        self._queues: dict[str, asyncio.Queue] = {}
        self.drop_rate = drop_rate
        self.rng = rng or random.Random()
        self.log = log or MessageLog()

    def register(self, agent_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[agent_id] = q
        return q

    def inbox(self, agent_id: str) -> asyncio.Queue:
        """The queue a registered agent reads its messages from."""
        return self._queues[agent_id]

    async def send(self, msg: MessageEnvelope) -> None:
        """Point-to-point send. Heartbeats are never dropped, so loss tests stay readable."""
        if msg.recipient_id not in self._queues:
            raise KeyError(f"Unknown recipient: {msg.recipient_id}")
        if msg.message_type != "heartbeat" and self.rng.random() < self.drop_rate:
            print(
                f"  [SIMULATED DROP] {msg.message_type} {msg.sender_id} → {msg.recipient_id} "
                f"corr={msg.correlation_id}"
            )
            return
        if msg.message_type != "heartbeat":
            self.log.record(msg)
        await self._queues[msg.recipient_id].put(msg)


# ─── Mock tools, as in Chapter 11 ─────────────────────────────────────────────

SEARCH_RESULTS = {
    "python creator": "Python was created by Guido van Rossum, first released in 1991.",
    "eiffel tower height": "The Eiffel Tower is 330 meters tall including the broadcast antenna.",
}


def web_search(query: str) -> str:
    key = query.lower().strip()
    for k, v in SEARCH_RESULTS.items():
        if k in key or key in k:
            return v
    return f"No results found for: {query}"


def calculator(expression: str) -> str:
    if not expression or not all(c in "0123456789+-*/(). " for c in expression):
        return "Error: expression contains invalid characters."
    return str(eval(expression, {"__builtins__": {}}, {}))


def perform(args: dict) -> str:
    """Any agent can run either tool, so a task can be reassigned to another agent."""
    if "query" in args:
        return web_search(args["query"])
    if "expression" in args:
        return calculator(args["expression"])
    return " | ".join(args["inputs"])


# ─── Part 2: the agents ───────────────────────────────────────────────────────


async def run_agent(
    agent_id: str,
    role: str,
    bus: AgentBus,
    crash_after: Optional[int] = None,
    done: Optional[set] = None,
) -> None:
    """Process tasks from the agent's inbox, and send a heartbeat every interval."""
    inbox = bus.inbox(agent_id)
    processed = 0
    seen: dict[str, str] = done if done is not None else {}
    while True:
        await bus.send(
            MessageEnvelope(sender_id=agent_id, recipient_id="monitor", message_type="heartbeat")
        )
        try:
            msg = await asyncio.wait_for(inbox.get(), timeout=HEARTBEAT_INTERVAL)
        except asyncio.TimeoutError:
            continue
        # TODO 1: Skip a message whose TTL has expired (msg.is_expired()), printing
        #   "<agent>: skipped expired <corr>". Acting on a stale task wastes work and
        #   can return an answer nobody is waiting for.
        print(f"  {agent_id} ({role}) received task {msg.correlation_id}")
        # TODO 2: Make resends idempotent: run perform() only the first time a
        #   correlation id is seen, and return the stored result after that. A result
        #   that was lost in transit makes the orchestrator resend the same task.
        seen[msg.correlation_id] = perform(msg.payload["args"])
        await bus.send(
            MessageEnvelope(
                sender_id=agent_id,
                recipient_id=msg.reply_to,
                message_type="result",
                correlation_id=msg.correlation_id,
                payload={"result": seen[msg.correlation_id]},
            )
        )
        processed += 1
        if crash_after is not None and processed >= crash_after:
            raise RuntimeError(f"{agent_id} crashed")


# ─── Part 5: heartbeat monitor (Section 15.9) ─────────────────────────────────


async def heartbeat_monitor(
    bus: AgentBus, agent_ids: list[str], failed: asyncio.Queue, timeout: float = HEARTBEAT_TIMEOUT
) -> None:
    """Track heartbeats sent to "monitor"; report each agent that falls silent once."""
    inbox = bus.inbox("monitor")
    loop = asyncio.get_running_loop()
    last_seen = {aid: loop.time() for aid in agent_ids}
    reported: set[str] = set()
    while True:
        try:
            msg = await asyncio.wait_for(inbox.get(), timeout=HEARTBEAT_INTERVAL)
            if msg.message_type == "heartbeat":
                last_seen[msg.sender_id] = loop.time()
        except asyncio.TimeoutError:
            pass
        now = loop.time()
        for agent_id in agent_ids:
            # TODO 3: Report each failed agent once: skip agents already in `reported`,
            #   and add each one you report.
            if now - last_seen[agent_id] > timeout:
                print(f"  [MONITOR] {agent_id} appears to have failed")
                await failed.put(agent_id)


# ─── Parts 3 and 4: the orchestrator ──────────────────────────────────────────


class Orchestrator:
    def __init__(self, bus: AgentBus, fallback: dict[str, str]):
        self.bus = bus
        self.replies = bus.register("orchestrator")
        self.results: dict[str, str] = {}
        self.waiters: dict[str, asyncio.Future] = {}
        self.down: set[str] = set()
        self.fallback = fallback  # agent -> agent that takes over its tasks
        self.retries = 0
        self.reassigned: list[str] = []

    async def collect(self) -> None:
        """Route each result to whoever is waiting for its correlation id."""
        while True:
            msg = await self.replies.get()
            future = self.waiters.get(msg.correlation_id)
            if future and not future.done():
                future.set_result(msg.payload["result"])

    async def watch(self, failed: asyncio.Queue) -> None:
        while True:
            self.down.add(await failed.get())

    async def request(self, agent: str, description: str, args: dict, corr: str) -> str:
        """Send a task and wait for its result, resending on timeout and rerouting on failure."""
        future = asyncio.get_running_loop().create_future()
        self.waiters[corr] = future
        for attempt in range(MAX_RETRIES + 1):
            if agent in self.down:
                new_agent = self.fallback[agent]
                print(f"  orchestrator: {agent} is down; reassigning {corr} to {new_agent}")
                self.reassigned.append(corr)
                agent = new_agent
            if attempt:
                self.retries += 1
                print(
                    f"  orchestrator: no result for {corr}; resending to {agent} "
                    f"(retry {attempt}/{MAX_RETRIES})"
                )
            await self.bus.send(
                MessageEnvelope(
                    sender_id="orchestrator",
                    recipient_id=agent,
                    reply_to="orchestrator",
                    message_type="task",
                    correlation_id=corr,
                    payload={"description": description, "args": args},
                )
            )
            try:
                result = await asyncio.wait_for(asyncio.shield(future), RESULT_TIMEOUT)
                self.results[corr] = result
                return result
            except asyncio.TimeoutError:
                continue
        raise TimeoutError(f"no result for {corr} after {MAX_RETRIES} retries")

    async def run(self) -> str:
        print("Parts 3-4: research and calculation in parallel, then synthesis")
        research, calc = await asyncio.gather(
            self.request("alpha", "Find who created Python", {"query": "python creator"}, "A"),
            self.request("beta", "Compute years since 1991", {"expression": "2024 - 1991"}, "B"),
        )
        summary = await self.request(
            "gamma",
            "Combine the findings",
            {"inputs": [research, f"Years since release: {calc}"]},
            "S",
        )
        print(f"\nSynthesis: {summary}\n")

        print("Part 5: alpha has crashed; its next task must go elsewhere")
        await asyncio.sleep(HEARTBEAT_TIMEOUT * 2)  # long enough for the monitor to notice
        follow_up = await self.request(
            "alpha", "Find the Eiffel Tower's height", {"query": "eiffel tower height"}, "C"
        )
        print(f"\nFollow-up result: {follow_up}")
        return summary


# ─── Run everything ───────────────────────────────────────────────────────────


async def main(seed: int = 8, drop_rate: float = 0.20) -> Orchestrator:
    bus = AgentBus(drop_rate=drop_rate, rng=random.Random(seed))
    for agent_id in ("alpha", "beta", "gamma", "monitor"):
        bus.register(agent_id)
    orch = Orchestrator(bus, fallback={"alpha": "beta", "beta": "alpha", "gamma": "beta"})
    failed: asyncio.Queue = asyncio.Queue()
    background = [
        asyncio.create_task(run_agent("alpha", "researcher", bus, crash_after=1)),
        asyncio.create_task(run_agent("beta", "analyst", bus)),
        asyncio.create_task(run_agent("gamma", "synthesizer", bus)),
        asyncio.create_task(heartbeat_monitor(bus, ["alpha", "beta", "gamma"], failed)),
        asyncio.create_task(orch.collect()),
        asyncio.create_task(orch.watch(failed)),
    ]
    try:
        await orch.run()
    finally:
        for task in background:
            task.cancel()
        await asyncio.gather(*background, return_exceptions=True)
    print(f"\nRetries: {orch.retries}; reassigned: {orch.reassigned}")
    print("\n=== MESSAGE LOG (delivered messages) ===")
    print(bus.log.summary())
    return orch


if __name__ == "__main__":
    asyncio.run(main())
