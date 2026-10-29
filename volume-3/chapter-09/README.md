# Volume III · Chapter 9 — Lab: Multi-Step Function Calling Pipeline

## What You Will Build

A three-step credit assessment pipeline in which each function call depends on the ones before it: look up a customer, fetch their order history, then generate a credit report from both results. The functions have OpenAI-style schemas, and the pipeline stops cleanly when a step fails. Then the claim intake from the chapter's opening story: a strict `record_claim` schema shapes the model's output, and a Pydantic `ClaimRecord` checks the data before anything is imported, so "about two hundred pounds" goes to a person instead of stopping the import job.

## Learning Outcomes

- Chain function calls whose arguments come from earlier results.
- Describe dependencies in tool schemas, so a model calls the steps in order.
- Return complete, consistently shaped results, including for empty cases.
- Bound a computed score, so out-of-range inputs cannot produce nonsense.
- Stop a pipeline at the first failed step instead of passing bad data on.
- Write a schema that meets strict mode's rules, and validate the model's arguments with Pydantic, since valid JSON is not the same as valid data.

## Prerequisites

- Python 3.15
- Chapter 9, read through its hands-on lab
- Dependencies: `pydantic`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (the pipeline runs the calls a model would make, without a model)

## Setup

```bash
cd volume-3/chapter-09      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but step 3 passes a total order value of zero (TODO 3), so every customer shows 0% utilization and is approved. The claim intake imports every claim as parsed (TODO 4), "about two hundred pounds" included. TODO 1 and TODO 2 do not change this demo's output; the tests check them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

============================================================
CREDIT ASSESSMENT PIPELINE — Customer: C001
============================================================

[Step 1] get_customer
  args:   {'customer_id': 'C001'}
  result: {
          "customer_id": "C001",
          "name": "Acme Corp",
          "tier": "enterprise",
          "credit_limit": 50000.0
}

[Step 2] get_order_history
  args:   {'customer_id': 'C001', 'limit': 5}
  result: {
          "customer_id": "C001",
          "orders": [
                    {
                              "order_id": "ORD-1001",
                              "amount": 12500.0,
                              "status": "completed"
                    }
          ],
          "total_orders": 1,
          "total_value": 12500.0
}

[Step 3] generate_credit_report
  args:   {'customer_id': 'C001', 'customer_tier': 'enterprise', 'credit_limit': 50000.0, 'total_order_value': 12500.0}
  result: {
          "customer_id": "C001",
          "credit_limit": 50000.0,
          "utilized_amount": 12500.0,
          "utilization_pct": 25.0,
          "risk_score": 62.5,
          "recommendation": "Review",
          "tier": "enterprise"
}

── Credit Assessment Summary ──────────────────────────────
  Customer:     Acme Corp (enterprise)
  Credit Limit: $50,000.00
  Order Value:  $12,500.00
  Utilization:  25.0%
  Risk Score:   62.5/100
  Decision:     Review

============================================================
CREDIT ASSESSMENT PIPELINE — Customer: C002
============================================================

[Step 1] get_customer
  args:   {'customer_id': 'C002'}
  result: {
          "customer_id": "C002",
          "name": "Beta LLC",
          "tier": "standard",
          "credit_limit": 10000.0
}

[Step 2] get_order_history
  args:   {'customer_id': 'C002', 'limit': 5}
  result: {
          "customer_id": "C002",
          "orders": [
                    {
                              "order_id": "ORD-1002",
                              "amount": 2300.0,
                              "status": "completed"
                    }
          ],
          "total_orders": 1,
          "total_value": 2300.0
}

[Step 3] generate_credit_report
  args:   {'customer_id': 'C002', 'customer_tier': 'standard', 'credit_limit': 10000.0, 'total_order_value': 2300.0}
  result: {
          "customer_id": "C002",
          "credit_limit": 10000.0,
          "utilized_amount": 2300.0,
          "utilization_pct": 23.0,
          "risk_score": 77.0,
          "recommendation": "Approve",
          "tier": "standard"
}

── Credit Assessment Summary ──────────────────────────────
  Customer:     Beta LLC (standard)
  Credit Limit: $10,000.00
  Order Value:  $2,300.00
  Utilization:  23.0%
  Risk Score:   77.0/100
  Decision:     Approve

============================================================
CREDIT ASSESSMENT PIPELINE — Customer: C003
============================================================

[Step 1] get_customer
  args:   {'customer_id': 'C003'}
  result: {
          "customer_id": "C003",
          "name": "Gamma Inc",
          "tier": "premium",
          "credit_limit": 25000.0
}

[Step 2] get_order_history
  args:   {'customer_id': 'C003', 'limit': 5}
  result: {
          "customer_id": "C003",
          "orders": [
                    {
                              "order_id": "ORD-1003",
                              "amount": 8900.0,
                              "status": "pending"
                    }
          ],
          "total_orders": 1,
          "total_value": 8900.0
}

[Step 3] generate_credit_report
  args:   {'customer_id': 'C003', 'customer_tier': 'premium', 'credit_limit': 25000.0, 'total_order_value': 8900.0}
  result: {
          "customer_id": "C003",
          "credit_limit": 25000.0,
          "utilized_amount": 8900.0,
          "utilization_pct": 35.6,
          "risk_score": 57.3,
          "recommendation": "Review",
          "tier": "premium"
}

── Credit Assessment Summary ──────────────────────────────
  Customer:     Gamma Inc (premium)
  Credit Limit: $25,000.00
  Order Value:  $8,900.00
  Utilization:  35.6%
  Risk Score:   57.3/100
  Decision:     Review

============================================================
CREDIT ASSESSMENT PIPELINE — Customer: C999
============================================================

[Step 1] get_customer
  args:   {'customer_id': 'C999'}
  result: {
          "error": "Customer 'C999' not found."
}
  ✗ Customer not found. Aborting.

============================================================
CLAIM INTAKE — valid JSON is not the same as valid data
============================================================

[E1] arguments: {"tracking_number": "WF-2291", "damage_description": "Cracked monitor screen", "declared_value": 189.0}
  ✓ imported: {'tracking_number': 'WF-2291', 'damage_description': 'Cracked monitor screen', 'declared_value': 189.0}

[E2] arguments: {"tracking_number": "WF-3107", "damage_description": "Dented kettle", "declared_value": "about two hundred pounds"}
  ✗ sent to a person:
      declared_value: Input should be a valid number, unable to parse string as a number

[E3] arguments: {"tracking_number": "order 5531", "damage_description": "Broken lamp", "declared_value": 0}
  ✗ sent to a person:
      tracking_number: String should match pattern '^WF-[0-9]{4}$'
      declared_value: Input should be greater than 0
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. With the four TODOs left in place, five of the fourteen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `KeyError: 'total_value'` | An empty order history was returned without a total | Complete TODO 1 |
| `UnicodeEncodeError` printing `✗` or `──` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Validate `generate_credit_report`'s arguments with Pydantic, constraining tier and amounts (Lab Question 2).
- Make the pipeline return a result object, including for a failed step, instead of only printing (Lab Question 3).
- Cache `get_customer` and `get_order_history` results for five minutes (Lab Question 4).
- Add a fourth step that sends the decision by email, and require human approval before it runs (Lab Question 5).

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 4 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 14 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
