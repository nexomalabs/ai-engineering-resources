# review_board_lab.py
"""
Volume II, Chapter 19 Lab: Review Board vs. Single-Prompt Review.

Runs in two modes:
  NEXOMA_LAB_MODE=fixture  (default) replays the example responses below; no API key.
  NEXOMA_LAB_MODE=live     calls the model; needs OPENAI_API_KEY.

The fixture responses are illustrative examples written for this lab, not
measurements. Run in live mode to see what your own model actually finds.
"""

import json
import os
from dataclasses import dataclass, field

MODE = os.environ.get("NEXOMA_LAB_MODE", "fixture")
MODEL = "gpt-6-luna"

# ---------------------------------------------------------------------------
# 1. The artifact under review: a short module with three planted defects.
# ---------------------------------------------------------------------------

ARTIFACT = """\
1  def get_customer_orders(db, customer_email):
2      query = f"SELECT * FROM orders WHERE email = '{customer_email}'"
3      return db.execute(query).fetchall()
4
5  def average_order_value(orders):
6      return sum(o["total"] for o in orders) / len(orders)
7
8  def apply_discount(total, percent):
9      return total - total * percent / 100
"""

PLANTED_DEFECTS = {
    2: ("critical", "SQL injection: email is interpolated into the query"),
    6: ("major", "ZeroDivisionError for a customer with no orders"),
    9: ("minor", "no bounds check: percent > 100 gives a negative total"),
}

# ---------------------------------------------------------------------------
# 2. Reviewer charters. Each reviewer runs in its own, separate context.
# ---------------------------------------------------------------------------

OUTPUT_CONTRACT = """Return JSON only:
{"findings": [{"line": int, "severity": "critical"|"major"|"minor",
               "issue": str, "evidence": str, "confidence": float}]}
Report only problems you can point to on a specific line. If you find none,
return {"findings": []}."""

REVIEWERS = {
    "engineer": (
        "You are the Engineer on a review board. Question: is the "
        "implementation correct for every input it can receive? "
        "Ignore style. " + OUTPUT_CONTRACT
    ),
    "security": (
        "You are the Security Reviewer on a review board. Question: what can "
        "an attacker or a malformed input make this code do? " + OUTPUT_CONTRACT
    ),
    "red_team": (
        "You are the Red-Team Critic on a review board. Question: what is the "
        "strongest case that this code will fail in production? " + OUTPUT_CONTRACT
    ),
}

SINGLE_PROMPT = (
    "Act as a panel of three experts (an engineer, a security reviewer, and a "
    "red-team critic) and give the panel's consensus review of this code. " + OUTPUT_CONTRACT
)

# Illustrative example responses for fixture mode.
FIXTURES = {
    "engineer": {
        "findings": [
            {
                "line": 6,
                "severity": "major",
                "issue": "Division by zero when orders is empty",
                "evidence": "len(orders) is 0 for a new customer",
                "confidence": 0.9,
            },
            {
                "line": 9,
                "severity": "minor",
                "issue": "percent is not validated",
                "evidence": "apply_discount(100, 150) returns -50.0",
                "confidence": 0.8,
            },
        ]
    },
    "security": {
        "findings": [
            {
                "line": 2,
                "severity": "critical",
                "issue": "SQL injection through customer_email",
                "evidence": "email \"x' OR '1'='1\" returns every order",
                "confidence": 0.95,
            },
        ]
    },
    "red_team": {
        "findings": [
            {
                "line": 2,
                "severity": "critical",
                "issue": "Untrusted input reaches SQL unescaped",
                "evidence": "string formatting builds the query",
                "confidence": 0.85,
            },
            {
                "line": 6,
                "severity": "minor",
                "issue": "Crashes for customers with no orders",
                "evidence": "no guard before the division",
                "confidence": 0.6,
            },
            {
                "line": 3,
                "severity": "minor",
                "issue": "SELECT * returns every column, including any added later",
                "evidence": "schema changes silently change the result",
                "confidence": 0.4,
            },
        ]
    },
    "single_prompt": {
        "findings": [
            {
                "line": 2,
                "severity": "critical",
                "issue": "Possible SQL injection",
                "evidence": "query built with an f-string",
                "confidence": 0.8,
            },
            {
                "line": 6,
                "severity": "major",
                "issue": "Empty list causes division by zero",
                "evidence": "len(orders) may be 0",
                "confidence": 0.7,
            },
        ]
    },
}


def ask(name: str, system: str, user: str) -> dict:
    """One model call in a fresh context. Fixture mode replays the example."""
    if MODE == "fixture":
        return FIXTURES[name]
    from openai import OpenAI  # imported here so fixture mode needs no package

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(r.choices[0].message.content)


# ---------------------------------------------------------------------------
# 3. Run the board: every reviewer independently, then synthesize.
# ---------------------------------------------------------------------------

SEVERITY_RANK = {"critical": 3, "major": 2, "minor": 1}


@dataclass
class Finding:
    line: int
    severity: str
    reviewers: list = field(default_factory=list)
    severities: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)


def run_board(artifact: str) -> dict:
    reports = {}
    for name, charter in REVIEWERS.items():
        reports[name] = ask(name, charter, f"Review this code:\n\n{artifact}")
    return reports


def synthesize(reports: dict) -> list:
    """Merge by line, keep every reviewer's severity, rank by worst severity
    then by how many reviewers raised it. Nothing is averaged away."""
    # TODO 1: Merge findings that point at the same line into one Finding. Keep
    # every reviewer's severity in `severities`, set `severity` to the worst one,
    # and sort by worst severity, then by number of reviewers, then by line.
    # Until then, every finding is listed separately and unsorted.
    findings = []
    for reviewer, report in reports.items():
        for f in report["findings"]:
            findings.append(
                Finding(
                    f["line"], f["severity"], [reviewer], {reviewer: f["severity"]}, [f["issue"]]
                )
            )
    return findings


def found_lines(findings) -> set:
    return {f.line if isinstance(f, Finding) else f["line"] for f in findings}


def print_ranked(findings: list) -> None:
    for i, f in enumerate(findings, 1):
        votes = ", ".join(f"{r}={s}" for r, s in f.severities.items())
        disagreement = len(set(f.severities.values())) > 1
        flag = "  <- severity disputed" if disagreement else ""
        single = "  <- one reviewer only" if len(f.reviewers) == 1 else ""
        print(f"  {i}. line {f.line} [{f.severity}] {f.issues[0]}")
        print(f"     raised by: {votes}{flag}{single}")


def score(name: str, lines: set) -> None:
    hits = sorted(lines & PLANTED_DEFECTS.keys())
    missed = sorted(PLANTED_DEFECTS.keys() - lines)
    extra = sorted(lines - PLANTED_DEFECTS.keys())
    print(
        f"  {name:<14} found {len(hits)}/3 planted defects"
        f"  missed lines: {missed or '-'}  unplanted findings on lines: {extra or '-'}"
    )


# ---------------------------------------------------------------------------
# 4. The Critique Board: should this feature exist at all?
# ---------------------------------------------------------------------------

PROPOSAL = (
    "Proposal: let the support chatbot issue discount codes of up to 50% "
    "automatically to customers it judges to be unhappy, using apply_discount()."
)

VERDICT_CONTRACT = """Return JSON only:
{"verdict": "BUILD"|"BUILD WITH CONDITIONS"|"PIVOT"|"DO NOT BUILD",
 "conditions": [str], "evidence": [str], "assumptions": [str]}
List as evidence only what the proposal or the code shows. Everything else
you rely on is an assumption."""

CRITIQUE_ROLES = {
    "customer_representative": (
        "You are the Customer Representative on a critique board. Question: "
        "would a customer want this, and would they trust it? " + VERDICT_CONTRACT
    ),
    "financial_analyst": (
        "You are the Financial Analyst on a critique board. Question: what does "
        "this cost, and what is the opportunity cost of building it? " + VERDICT_CONTRACT
    ),
    "risk_manager": (
        "You are the Risk Manager on a critique board. Question: what is the "
        "downside scenario, and how bad is it? " + VERDICT_CONTRACT
    ),
}

FIXTURES.update(
    {
        "customer_representative": {
            "verdict": "BUILD WITH CONDITIONS",
            "conditions": ["The customer sees and accepts the offer; nothing is applied silently"],
            "evidence": [],
            "assumptions": ["Unhappy customers value an instant discount"],
        },
        "financial_analyst": {
            "verdict": "BUILD WITH CONDITIONS",
            "conditions": ["Cap discounts at 15%", "Set a daily budget per customer"],
            "evidence": ["apply_discount() has no upper bound (line 9)"],
            "assumptions": ["A discount costs less than losing the customer"],
        },
        "risk_manager": {
            "verdict": "DO NOT BUILD",
            "conditions": [],
            "evidence": ["The chatbot decides who is unhappy from text the customer writes"],
            "assumptions": ["Customers will learn to sound unhappy once word spreads"],
        },
    }
)


def run_critique_board() -> None:
    print("\n=== CRITIQUE BOARD: should the discount feature exist? ===")
    votes = {}
    for role, charter in CRITIQUE_ROLES.items():
        report = ask(role, charter, f"{PROPOSAL}\n\nRelevant code:\n\n{ARTIFACT}")
        votes[role] = report["verdict"]
        print(f"  {role:<24} {report['verdict']}")
        for c in report["conditions"]:
            print(f"      condition:  {c}")
        for e in report["evidence"]:
            print(f"      evidence:   {e}")
        for a in report["assumptions"]:
            print(f"      assumption: {a}")
    # TODO 2: A Critique Board takes no vote. Replace the majority decision below
    # with a record that lists every distinct verdict and the roles that gave it,
    # so the dissent stays visible.
    majority = max(set(votes.values()), key=list(votes.values()).count)
    print(f"  Board decision (majority): {majority}")


if __name__ == "__main__":
    print(f"Mode: {MODE}\n")
    reports = run_board(ARTIFACT)
    ranked = synthesize(reports)
    print("=== REVIEW BOARD: ranked findings ===")
    print_ranked(ranked)

    single = ask("single_prompt", SINGLE_PROMPT, f"Review this code:\n\n{ARTIFACT}")

    print("\n=== Recall against the planted defects ===")
    for name, report in reports.items():
        score(name, found_lines(report["findings"]))
    score("board (all 3)", found_lines(ranked))
    score("single prompt", found_lines(single["findings"]))
    print(
        f"\n  Model calls: review board = {len(REVIEWERS)}, single prompt = 1, "
        f"critique board = {len(CRITIQUE_ROLES)}"
    )

    run_critique_board()
