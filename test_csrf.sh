#!/bin/bash

# Test CSRF Protection (GAP-56)

echo "=== Testing CSRF Protection ==="
echo ""

# 1. Get CSRF token
echo "1. Getting CSRF token..."
RESPONSE=$(curl -s -c /tmp/csrf_cookies.txt -X POST http://localhost:8000/auth/csrf-token)
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['csrf_token'])")
echo "   Token: ${TOKEN:0:20}..."
echo ""

# 2. Test protected endpoint WITHOUT token (should fail)
echo "2. Testing POST without CSRF token (should fail with 403)..."
curl -s -X POST http://localhost:8000/agents/mutual-aid-matchmaker/run \
  -H "Content-Type: application/json" \
  -d '{}' \
  -o /dev/null \
  -w "   Status: %{http_code}\n"
echo ""

# 3. Test protected endpoint WITH token (should succeed)
echo "3. Testing POST with CSRF token (should succeed)..."
curl -s -b /tmp/csrf_cookies.txt \
  -X POST http://localhost:8000/agents/mutual-aid-matchmaker/run \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{}' \
  -o /dev/null \
  -w "   Status: %{http_code}\n"
echo ""

# 4. Test exempt endpoint (should always work)
echo "4. Testing exempt endpoint /health (should always work)..."
curl -s -X GET http://localhost:8000/health \
  -o /dev/null \
  -w "   Status: %{http_code}\n"
echo ""

# Cleanup
rm -f /tmp/csrf_cookies.txt

echo "=== CSRF Tests Complete ==="
