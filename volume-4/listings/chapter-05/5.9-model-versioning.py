# Applied AI Engineering, Volume IV, Chapter 5
# Section 5.9, Model Versioning
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class ModelVersionRecord:
    version_id: str           # e.g., "v1.4.2"
    model_identifier: str     # e.g., "gpt-6.1-sol"
    prompt_version: str       # e.g., "analysis-v2.4.1"
    deployed_at: datetime
    deployed_by: str
    status: str               # "staging" | "canary" | "active" | "retired"
    traffic_percentage: float # 0.0 to 1.0
    metrics_baseline: Optional[dict] = None  # Metrics at deployment time
    retired_at: Optional[datetime] = None
    retirement_reason: Optional[str] = None

class ModelVersionRegistry:
    def __init__(self):
        self._versions: dict[str, ModelVersionRecord] = {}

    def register(self, record: ModelVersionRecord) -> None:
        self._versions[record.version_id] = record

    def get_active(self) -> list[ModelVersionRecord]:
        return [v for v in self._versions.values()
                if v.status in ("active", "canary")]

    def retire(self, version_id: str, reason: str) -> None:
        if version_id in self._versions:
            self._versions[version_id].status = "retired"
            self._versions[version_id].retired_at = datetime.now(timezone.utc)
            self._versions[version_id].retirement_reason = reason

    def get_current_prompt_version(self) -> str:
        active = [v for v in self._versions.values() if v.status == "active"]
        if not active:
            raise RuntimeError("No active model version found")
        return active[-1].prompt_version
