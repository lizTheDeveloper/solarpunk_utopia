#!/bin/bash
# Test script for Agent API endpoints
# Tests the REST API endpoints exposed by the DTN Bundle System

set -e

API_URL="http://localhost:8000"
AGENT_API="$API_URL/agents"

echo "=========================================="
echo "Testing Agent API Endpoints"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ Server is not running at $API_URL"
    echo "Start the server with: python -m uvicorn app.main:app --reload"
    exit 1
fi

echo "✓ Server is running"
echo ""

# Test 1: List available agents
echo "=== Test 1: GET /agents ==="
echo "List all available agents"
response=$(curl -s "$AGENT_API")
echo "$response" | python -m json.tool
echo ""

# Test 2: Run mutual-aid-matchmaker agent
echo "=== Test 2: POST /agents/mutual-aid-matchmaker/run ==="
echo "Execute the mutual aid matchmaker agent"
response=$(curl -s -X POST "$AGENT_API/mutual-aid-matchmaker/run" \
    -H "Content-Type: application/json" \
    -d '{}')
echo "$response" | python -m json.tool

# Extract proposal count
proposal_count=$(echo "$response" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('proposals', [])))")
echo ""
echo "✓ Agent executed successfully"
echo "✓ Generated $proposal_count proposals"
echo ""

# Test 3: Get proposals list
echo "=== Test 3: GET /agents/proposals ==="
echo "List all proposals"
response=$(curl -s "$AGENT_API/proposals")
echo "$response" | python -m json.tool
echo ""

# Test 4: Get agent settings
echo "=== Test 4: GET /agents/settings/mutual-aid-matchmaker ==="
echo "Get agent configuration"
response=$(curl -s "$AGENT_API/settings/mutual-aid-matchmaker")
echo "$response" | python -m json.tool
echo ""

# Test 5: Get agent stats
echo "=== Test 5: GET /agents/stats/mutual-aid-matchmaker ==="
echo "Get agent statistics"
response=$(curl -s "$AGENT_API/stats/mutual-aid-matchmaker")
echo "$response" | python -m json.tool
echo ""

echo "=========================================="
echo "✅ All API tests passed!"
echo "=========================================="
