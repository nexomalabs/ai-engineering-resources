#!/usr/bin/env bash
# Smoke test script for AI API Service
# Run after deployment to verify the service is operational.
# Usage: ./scripts/smoke_test.sh [BASE_URL]

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

pass() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }

echo "=== AI API Service Smoke Tests ==="
echo "Target: $BASE_URL"
echo ""

# Test 1: Health check
echo "1. Health endpoint"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$STATUS" = "200" ]; then
    pass "GET /health → 200"
else
    fail "GET /health → $STATUS (expected 200)"
fi

# Test 2: Readiness check
echo "2. Readiness endpoint"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/ready")
if [ "$STATUS" = "200" ]; then
    pass "GET /ready → 200"
else
    fail "GET /ready → $STATUS (expected 200)"
fi

# Test 3: Analysis endpoint — valid request
echo "3. Analysis endpoint (valid request)"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -d '{"text": "Artificial intelligence is transforming enterprise operations.", "task": "summarize"}')
HTTP_STATUS=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)
if [ "$HTTP_STATUS" = "200" ] && echo "$BODY" | grep -q '"result"'; then
    pass "POST /api/v1/analyze → 200 with result"
else
    fail "POST /api/v1/analyze → $HTTP_STATUS (expected 200 with result)"
fi

# Test 4: Validation — empty text
echo "4. Input validation (empty text)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$BASE_URL/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -d '{"text": "", "task": "summarize"}')
if [ "$STATUS" = "422" ]; then
    pass "Empty text → 422 Unprocessable Entity"
else
    fail "Empty text → $STATUS (expected 422)"
fi

# Test 5: Validation — invalid task
echo "5. Input validation (invalid task)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$BASE_URL/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -d '{"text": "Test content", "task": "invalid_task_xyz"}')
if [ "$STATUS" = "422" ]; then
    pass "Invalid task → 422 Unprocessable Entity"
else
    fail "Invalid task → $STATUS (expected 422)"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "SMOKE TEST FAILED — DO NOT PROMOTE THIS VERSION"
    exit 1
else
    echo "SMOKE TEST PASSED — Safe to promote"
    exit 0
fi
