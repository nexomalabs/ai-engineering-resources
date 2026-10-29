"""Step 6: the profile from the chapter's opening story, of one reply from Wren.

To answer "Where is my parcel?", Wren looks up the shipment, retrieves the relevant policy
passages, puts the parcel's scan history into the prompt and calls the model. The "before"
version does this the way the team first built it: the shipment lookup blocks until the
tracking service answers, retrieval waits behind it, and every scan event, hundreds for a
parcel that has crossed several countries, is formatted into the prompt. The "after"
version runs the lookup and retrieval together and sends only the last few events.

The services and the model are simulated with fixed delays, so the timings are a model of
the story, not a measurement. Run it to see where the time goes:

    python solution/wren_profile.py
"""

import asyncio
import time

SPEED = 1.0  # multiply every simulated delay; the tests run it faster
RECENT_EVENTS = 5  # how much history a reply needs: where the parcel is now, and lately

SCAN_HISTORY = [
    f"{day:02d}/{hour:02d}h scanned at {site}"
    for day in range(1, 31)
    for hour, site in enumerate(
        [
            "Rotterdam hub",
            "Antwerp depot",
            "Calais port",
            "Dover port",
            "M20 corridor",
            "Maidstone depot",
            "London gateway",
            "Leeds hub",
            "Leeds depot",
            "Leeds van 14",
        ]
    )
]  # 300 events


class StageTimer:
    """Records how long each stage of one reply takes."""

    def __init__(self):
        self.stages: dict[str, float] = {}

    def record(self, stage: str, started: float) -> None:
        self.stages[stage] = time.perf_counter() - started


async def lookup_shipment(parcel_id: str) -> dict:
    await asyncio.sleep(0.5 * SPEED)  # the tracking service
    return {"parcel": parcel_id, "status": "out for delivery", "events": SCAN_HISTORY}


async def retrieve_policy(question: str) -> list[str]:
    await asyncio.sleep(0.3 * SPEED)  # the vector store
    return ["Parcels out for delivery arrive by 6 pm.", "Delays are notified by text message."]


def describe_events(events: list[str]) -> str:
    """Format scan events for the prompt; each one resolves its site code (2 ms)."""
    lines = []
    for event in events:
        time.sleep(0.002 * SPEED)
        lines.append(f"- {event}")
    return "\n".join(lines)


async def call_model(prompt: str) -> str:
    await asyncio.sleep(0.8 * SPEED)  # the model, for a short reply
    return "Your parcel is out for delivery and should arrive by 6 pm today."


async def reply_before(question: str, parcel_id: str, timer: StageTimer) -> tuple[str, str]:
    started = time.perf_counter()
    shipment = await lookup_shipment(parcel_id)
    timer.record("shipment lookup", started)
    started = time.perf_counter()
    passages = await retrieve_policy(question)
    timer.record("policy retrieval", started)
    started = time.perf_counter()
    history = describe_events(shipment["events"])
    timer.record("scan history", started)
    prompt = f"{question}\nStatus: {shipment['status']}\n{history}\n" + "\n".join(passages)
    started = time.perf_counter()
    answer = await call_model(prompt)
    timer.record("model call", started)
    return answer, prompt


async def reply_after(question: str, parcel_id: str, timer: StageTimer) -> tuple[str, str]:
    started = time.perf_counter()
    shipment, passages = await asyncio.gather(lookup_shipment(parcel_id), retrieve_policy(question))
    timer.record("shipment lookup and retrieval", started)
    started = time.perf_counter()
    history = describe_events(shipment["events"][-RECENT_EVENTS:])
    timer.record("scan history", started)
    prompt = f"{question}\nStatus: {shipment['status']}\n{history}\n" + "\n".join(passages)
    started = time.perf_counter()
    answer = await call_model(prompt)
    timer.record("model call", started)
    return answer, prompt


def profile(reply) -> tuple[StageTimer, float, str]:
    timer = StageTimer()
    started = time.perf_counter()
    answer, prompt = asyncio.run(reply("Where is my parcel?", "WF-2291", timer))
    return timer, time.perf_counter() - started, prompt


def main() -> None:
    print(f"Where is my parcel? (WF-2291, {len(SCAN_HISTORY)} scan events)\n")
    for name, reply in (("before", reply_before), ("after", reply_after)):
        timer, total, prompt = profile(reply)
        print(f"{name}: {total:.2f} s in all, a prompt of about {len(prompt) // 4} tokens")
        for stage, seconds in timer.stages.items():
            print(f"  {stage:<30} {seconds:5.2f} s  {seconds / total:4.0%}")
        print()


if __name__ == "__main__":
    main()
