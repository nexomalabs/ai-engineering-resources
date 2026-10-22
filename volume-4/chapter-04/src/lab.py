"""Lab 4 — Event-Driven Document Automation Pipeline (starter).

This file RUNS as supplied. A file whose classification fails once is dropped without a
trace, and a low-confidence classification is routed as if it were certain. Complete the
three TODOs.

    python src/lab.py
"""

import asyncio
import logging
import random
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

# ─── Event Bus ────────────────────────────────────────────────────────────────


class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, handler):
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, event_type, payload):
        for handler in self._subscribers.get(event_type, []):
            asyncio.create_task(self._safe_call(handler, payload))

    async def _safe_call(self, handler, payload):
        try:
            await handler(payload)
        except Exception as exc:
            logger.error("Handler %s failed: %s", handler.__name__, exc)


bus = EventBus()

# ─── Action Log ───────────────────────────────────────────────────────────────

action_log = []


def log_action(file_id, action, details):
    entry = {
        "action_id": str(uuid.uuid4()),
        "file_id": file_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    action_log.append(entry)
    logger.info("[AUDIT] %s | %s | %s", file_id[:8], action, details)


# ─── Simulated LLM Classifier ─────────────────────────────────────────────────

DOCUMENT_TYPES = ["contract", "invoice", "report", "correspondence", "unknown"]

# Stand-in for the model: keyword cues for each type. A real classifier would send
# the text to an LLM, with these types listed in the prompt.
TYPE_CUES = {
    "contract": ["agreement", "contract", "between", "terms"],
    "invoice": ["invoice", "vendor", "amount due", "$"],
    "report": ["report", "revenue", "quarter", "q1", "q2", "q3", "q4"],
    "correspondence": ["hi team", "dear", "following up", "regards"],
}


async def classify_document(text: str, fail_probability: float = 0.2) -> dict:
    """Simulate LLM classification with occasional transient failures."""
    await asyncio.sleep(random.uniform(0.1, 0.4))  # Simulate latency
    if random.random() < fail_probability:
        raise ConnectionError("Simulated LLM API transient failure")
    lowered = text.lower()
    hits = {t: sum(cue in lowered for cue in cues) for t, cues in TYPE_CUES.items()}
    doc_type = max(hits, key=hits.get)
    if hits[doc_type] == 0:
        return {"type": "unknown", "confidence": 0.5}
    return {"type": doc_type, "confidence": round(min(0.99, 0.6 + 0.15 * hits[doc_type]), 2)}


# ─── Handlers by Document Type ───────────────────────────────────────────────


async def handle_contract(file_id: str, filepath: Path, classification: dict):
    await asyncio.sleep(0.2)
    log_action(
        file_id,
        "contract_processed",
        f"Extracted terms. Confidence: {classification['confidence']}",
    )


async def handle_invoice(file_id: str, filepath: Path, classification: dict):
    await asyncio.sleep(0.1)
    log_action(
        file_id,
        "invoice_processed",
        f"Created payment record. Confidence: {classification['confidence']}",
    )


async def handle_report(file_id: str, filepath: Path, classification: dict):
    await asyncio.sleep(0.15)
    log_action(
        file_id,
        "report_archived",
        f"Archived to reports store. Confidence: {classification['confidence']}",
    )


async def handle_unknown(file_id: str, filepath: Path, classification: dict):
    log_action(
        file_id,
        "routed_to_review",
        f"Low confidence or unknown type: {classification['confidence']}",
    )


HANDLERS = {
    "contract": handle_contract,
    "invoice": handle_invoice,
    "report": handle_report,
    "correspondence": handle_unknown,
    "unknown": handle_unknown,
}

# ─── Pipeline Stages ──────────────────────────────────────────────────────────


async def on_file_uploaded(payload: dict):
    file_id = payload["file_id"]
    filepath = Path(payload["filepath"])
    log_action(file_id, "file_received", filepath.name)
    await bus.publish("classify_document", {"file_id": file_id, "filepath": str(filepath)})


async def on_classify_document(payload: dict):
    file_id = payload["file_id"]
    filepath = Path(payload["filepath"])
    text = filepath.read_text(encoding="utf-8", errors="replace")

    # TODO 1: Retry a ConnectionError up to 3 attempts in all, waiting 2 ** attempt
    #   seconds between attempts (2 s, then 4 s) and logging a warning each time.
    # TODO 2: When the last attempt fails, log a "classification_failed" action and
    #   publish "routing_failed" with the file_id and the reason, so the file reaches
    #   the dead-letter handler instead of disappearing.
    try:
        classification = await classify_document(text)
    except ConnectionError as exc:
        logger.warning("%s classification failed: %s", file_id[:8], exc)
        return
    log_action(
        file_id,
        "classified",
        f"type={classification['type']} confidence={classification['confidence']}",
    )
    await bus.publish(
        "route_document",
        {"file_id": file_id, "filepath": str(filepath), "classification": classification},
    )


CONFIDENCE_THRESHOLD = 0.75  # below this, a person checks the classification


async def on_route_document(payload: dict):
    file_id = payload["file_id"]
    filepath = Path(payload["filepath"])
    classification = payload["classification"]
    doc_type = classification["type"]
    # TODO 3: Send a classification below CONFIDENCE_THRESHOLD to handle_unknown
    #   (human review), whatever its type.
    handler = HANDLERS.get(doc_type, handle_unknown)
    log_action(file_id, "routed", f"→ {doc_type} handler")
    await handler(file_id, filepath, classification)
    log_action(file_id, "pipeline_complete", f"type={doc_type}")


async def on_routing_failed(payload: dict):
    log_action(payload["file_id"], "dead_letter", payload["reason"])


# ─── Wire up event bus ────────────────────────────────────────────────────────

bus.subscribe("file_uploaded", on_file_uploaded)
bus.subscribe("classify_document", on_classify_document)
bus.subscribe("route_document", on_route_document)
bus.subscribe("routing_failed", on_routing_failed)

# ─── File Watcher ────────────────────────────────────────────────────────────


async def watch_directory(watch_dir: Path, run_for_seconds: float = 5.0):
    """Simulate file arrivals and watch the directory."""
    seen = set()
    stop_at = asyncio.get_event_loop().time() + run_for_seconds

    while asyncio.get_event_loop().time() < stop_at:
        for filepath in watch_dir.iterdir():
            if str(filepath) not in seen and filepath.suffix in (".txt", ".pdf", ".docx"):
                seen.add(str(filepath))
                file_id = str(uuid.uuid4())
                logger.info("New file detected: %s", filepath.name)
                await bus.publish(
                    "file_uploaded",
                    {
                        "file_id": file_id,
                        "filepath": str(filepath),
                    },
                )
        await asyncio.sleep(0.5)


# ─── Demo ─────────────────────────────────────────────────────────────────────


async def demo():
    random.seed(42)  # reproducible latencies and failures
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_path = Path(tmpdir)
        documents = [
            ("agreement_2024.txt", "This Software License Agreement is between..."),
            ("invoice_00123.txt", "Invoice #00123 — Vendor: TechSupply LLC — $4,500"),
            ("q3_report.txt", "Q3 Operations Report — Revenue up 12% YoY..."),
            ("email_thread.txt", "Hi team, following up on the open action items..."),
            ("unknown_doc.txt", "XYZ 9182 beta gamma delta epsilon zeta theta"),
        ]

        # Simulate files arriving in the directory
        async def drop_files():
            for name, content in documents:
                await asyncio.sleep(0.3)
                (watch_path / name).write_text(content, encoding="utf-8")

        await asyncio.gather(
            watch_directory(watch_path, run_for_seconds=5),
            drop_files(),
        )

        # Wait until every file has finished or been dead-lettered (at most 15 s);
        # a fixed sleep would cut off a file that is still retrying
        for _ in range(150):
            finished = {
                e["file_id"]
                for e in action_log
                if e["action"] in ("pipeline_complete", "dead_letter")
            }
            if len(finished) == len(documents):
                break
            await asyncio.sleep(0.1)

    print("\n=== ACTION LOG ===")
    for entry in action_log:
        print(
            f"  {entry['timestamp'][11:19]} | {entry['file_id'][:8]} | "
            f"{entry['action']:30s} | {entry['details']}"
        )
    print(f"\nTotal actions logged: {len(action_log)}")


if __name__ == "__main__":
    asyncio.run(demo())
