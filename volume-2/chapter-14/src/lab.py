import sys
from pathlib import Path

# Find the volume's shared/ folder, which holds the recording client.
sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in Path(__file__).resolve().parents
            if (p / "shared" / "nexoma_labs").is_dir()
        )
    ),
)

import hashlib
import json
import os
import time
from datetime import datetime

from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# PART 1: FAILING PROMPT AND ABLATION STUDY
# ============================================================

# This prompt has multiple issues — we'll find them through ablation
FAILING_PROMPT_SYSTEM = """You are a data extraction assistant.
Extract information from customer messages.
Return JSON with: name, email, issue_type, priority.
Priority should be: low, medium, high, or critical."""

FAILING_TEST_CASES = [
    "Hi, I'm Sarah Johnson (sarah@company.com). My account login is broken and I can't access production systems. This is urgent!",
    "My name is tom (tom.smith@example.org) - quick question about billing",
    "ATTN: Alex Chen, alex.chen@corp.net - Server completely down, losing $10k/hour!!!",
]


def run_extraction(system: str, message: str) -> dict:
    """Run extraction and attempt to parse JSON."""
    try:
        r = client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Extract from: {message}"},
            ],
            temperature=0,
            max_completion_tokens=200,
        )
        output = r.choices[0].message.content.strip()
        # Try to extract JSON from output
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        return {"success": True, "data": json.loads(output), "raw": r.choices[0].message.content}
    except json.JSONDecodeError:
        return {"success": False, "error": "JSON parse failed", "raw": r.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e), "raw": ""}


# Ablation study: test with and without key components
print("ABLATION STUDY: JSON FORMAT FAILURE")
print("=" * 60)

ablation_variants = {
    "Original (failing)": FAILING_PROMPT_SYSTEM,
    "Add prefill hint": FAILING_PROMPT_SYSTEM
    + "\n\nAlways start your response with '{' and end with '}'. Return ONLY the JSON object, no other text.",
    "Add schema": FAILING_PROMPT_SYSTEM
    + '\n\nExact schema:\n{"name": "string", "email": "string", "issue_type": "string", "priority": "low|medium|high|critical"}',
    "Add output trigger": FAILING_PROMPT_SYSTEM
    + "\n\nRespond with only valid JSON. Begin your response with: {",
}

test_msg = FAILING_TEST_CASES[0]
print(f"Test input: {test_msg[:80]}...\n")

for variant_name, system_prompt in ablation_variants.items():
    result = run_extraction(system_prompt, test_msg)
    status = "✓ PASS" if result["success"] else "✗ FAIL"
    print(f"{status} | {variant_name}")
    if result["success"]:
        data = result["data"]
        print(f"       → name={data.get('name')}, priority={data.get('priority')}")
    else:
        print(f"       → {result['error']}: {result['raw'][:60]}...")

# ============================================================
# PART 2: STRUCTURED LOGGING
# ============================================================


def execute_with_logging(system: str, user_input: str, prompt_id: str, version: str) -> dict:
    """Execute a prompt with structured logging."""
    start_time = time.time()
    log = {
        "log_id": hashlib.md5(f"{prompt_id}{user_input}{start_time}".encode()).hexdigest()[:12],
        "timestamp": datetime.now().isoformat(),
        "prompt_id": prompt_id,
        "prompt_version": version,
        "input_hash": hashlib.sha256(user_input.encode()).hexdigest()[:16],
        "input_length_chars": len(user_input),
    }

    try:
        r = client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_input},
            ],
            temperature=0,
            max_completion_tokens=200,
        )
        output = r.choices[0].message.content
        log.update(
            {
                "output_raw": output,
                "latency_ms": int((time.time() - start_time) * 1000),
                "input_tokens": r.usage.prompt_tokens,
                "output_tokens": r.usage.completion_tokens,
            }
        )

        # Validate JSON
        try:
            json.loads(output.strip().lstrip("```json").rstrip("```").strip())
            log.update({"parse_success": True, "validation_success": True, "error_type": None})
        except json.JSONDecodeError:
            log.update(
                {
                    "parse_success": False,
                    "validation_success": False,
                    "error_type": "json_parse_error",
                }
            )

    except Exception as e:
        log.update(
            {
                "error_type": "api_error",
                "error_detail": str(e),
                "latency_ms": int((time.time() - start_time) * 1000),
            }
        )

    return log


print("\n\nSTRUCTURED LOGGING DEMO")
print("=" * 60)

logs = []
for msg in FAILING_TEST_CASES:
    log = execute_with_logging(FAILING_PROMPT_SYSTEM, msg, "extraction-v1", "1.0.0")
    logs.append(log)
    print(
        f"[{log['log_id']}] parse={log.get('parse_success', '?')} | {log.get('latency_ms')}ms | error={log.get('error_type', 'none')}"
    )

# Failure analysis
failures = [entry for entry in logs if not entry.get("parse_success", True)]
print(f"\nFailure rate: {len(failures)}/{len(logs)} ({len(failures) / len(logs) * 100:.0f}%)")
