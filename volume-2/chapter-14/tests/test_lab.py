"""Runs the lab's solution and checks it. In fixture mode, the default, the recorded model
responses replay with no API key and the output must match expected/output.txt exactly.
In live mode the model answers afresh, so only a clean run is checked.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
# Values that change on every run even when the model's answers replay exactly.
VOLATILE = ["\\[[0-9a-f]{12}\\]", "\\| \\d+ms \\|"]


def normalise(text: str) -> str:
    for pattern in VOLATILE:
        text = re.sub(pattern, "<volatile>", text)
    return text


def test_solution_reproduces_expected_output():
    mode = os.environ.get("NEXOMA_LAB_MODE", "fixture")
    result = subprocess.run(
        [sys.executable, "solution/lab.py"],
        cwd=LAB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "NEXOMA_LAB_MODE": mode, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if mode == "fixture":
        expected = (LAB / "expected" / "output.txt").read_text(encoding="utf-8")
        assert normalise(result.stdout) == normalise(expected)
