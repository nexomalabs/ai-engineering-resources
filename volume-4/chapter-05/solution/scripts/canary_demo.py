"""Replay the chapter's canary: five percent of traffic to a new model version.

The new version (played by the stand-in) gives good answers that are much longer, so it
costs more per conversation. The service's canary rule rolls it back once it passes 1.5
times the stable version's cost per request. Runs the service in-process, with no server:

    uv run --project .. python scripts/canary_demo.py      (from src/ or solution/)
"""

import os
import sys
from pathlib import Path

os.environ.update(
    NEXOMA_LAB_MODE="fixture",
    CANARY_MODEL="wren-model-next",
    CANARY_PERCENT="5",
    CANARY_SEED="11",
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402

QUESTION = "Where is my parcel? It left the Leeds depot on Monday and nothing has changed since."

with TestClient(main.app) as client:
    rolled_back_at = None
    for n in range(1, 1001):
        client.post("/api/v1/analyze", json={"text": QUESTION})
        if rolled_back_at is None and client.get("/canary").json()["rolled_back"]:
            rolled_back_at = n
    status = client.get("/canary").json()

stable, canary = status["stable"], status["canary"]
print(f"Canary {status['canary_model']} started on 5% of traffic; 1,000 requests sent.")
print(f"  stable: {stable['requests']:4d} requests, ${stable['cost_per_request_usd']:.6f} each")
print(f"  canary: {canary['requests']:4d} requests, ${canary['cost_per_request_usd']:.6f} each")
if status["rolled_back"]:
    print(f"Rolled back at request {rolled_back_at}: {status['rollback_reason']}.")
    print(f"Canary traffic now: {status['canary_percent']}%")
else:
    print("The canary was never rolled back, and still receives 5% of traffic.")
