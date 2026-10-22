# Applied AI Engineering, Volume II, Chapter 17
# Section 17.9, Building a Framework Library
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import hashlib
from datetime import datetime, timezone

class FrameworkLibrary:
    """
    Central registry for managing reusable prompt frameworks.
    """

    def __init__(self):
        self._registry: dict[str, dict] = {}  # framework_id -> {version, framework, metadata}

    def register(self, framework_obj, owner: str, tags: list[str] = None) -> str:
        """Register a framework and return its registry key."""
        fid = framework_obj.name if hasattr(framework_obj, "name") else framework_obj.framework_id
        version = framework_obj.version
        key = f"{fid}@{version}"
        self._registry[key] = {
            "framework": framework_obj,
            "owner": owner,
            "tags": tags or [],
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "usage_count": 0,
        }
        return key

    def get(self, framework_id: str, version: str = "latest"):
        """Retrieve a framework by ID and optional version."""
        if version == "latest":
            # Find the highest version for this ID
            candidates = [
                (k, v) for k, v in self._registry.items()
                if k.startswith(f"{framework_id}@")
            ]
            if not candidates:
                raise KeyError(f"Framework '{framework_id}' not found in library.")
            key, entry = sorted(candidates, key=lambda x: x[0])[-1]
        else:
            key = f"{framework_id}@{version}"
            if key not in self._registry:
                raise KeyError(f"Framework '{key}' not found in library.")
            entry = self._registry[key]

        entry["usage_count"] += 1
        return entry["framework"]

    def search_by_tag(self, tag: str) -> list[str]:
        """Return all framework keys that match a given tag."""
        return [k for k, v in self._registry.items() if tag in v["tags"]]

    def list_all(self) -> list[dict]:
        """Return summary of all registered frameworks."""
        return [
            {
                "key": k,
                "owner": v["owner"],
                "tags": v["tags"],
                "usage_count": v["usage_count"],
            }
            for k, v in self._registry.items()
        ]
