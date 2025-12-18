#!/bin/bash
# DTN Bundle System API Integration Test
set -e

BASE_URL="http://localhost:8000"

echo "============================================"
echo "DTN Bundle System API Integration Test"
echo "============================================"
echo ""

# Test 1: Health check
echo "Test 1: Health check"
curl -sf "$BASE_URL/health" > /dev/null && echo "✓ Health check passed" || (echo "✗ Health check failed" && exit 1)
echo ""

# Test 2: Node info
echo "Test 2: Node info"
NODE_INFO=$(curl -sf "$BASE_URL/node/info")
NODE_ID=$(echo "$NODE_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['node_id'])")
echo "✓ Node ID: $NODE_ID"
echo ""

# Test 3: Create emergency bundle
echo "Test 3: Create emergency bundle"
EMERGENCY_BUNDLE=$(curl -sf -X POST "$BASE_URL/bundles" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"message": "Emergency: Fire in garden"},
    "payloadType": "alert:Emergency",
    "priority": "emergency",
    "audience": "public",
    "topic": "coordination",
    "tags": ["emergency", "fire"]
  }')
BUNDLE_ID=$(echo "$EMERGENCY_BUNDLE" | python3 -c "import sys, json; print(json.load(sys.stdin)['bundleId'])")
echo "✓ Created emergency bundle: ${BUNDLE_ID:0:20}..."
echo ""

# Test 4: List outbox
echo "Test 4: List bundles in outbox"
OUTBOX_COUNT=$(curl -sf "$BASE_URL/bundles?queue=outbox&limit=10" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "✓ Outbox contains $OUTBOX_COUNT bundles"
echo ""

# Test 5: Get specific bundle
echo "Test 5: Get specific bundle"
BUNDLE=$(curl -sf "$BASE_URL/bundles/$BUNDLE_ID")
PRIORITY=$(echo "$BUNDLE" | python3 -c "import sys, json; print(json.load(sys.stdin)['priority'])")
echo "✓ Retrieved bundle with priority: $PRIORITY"
echo ""

# Test 6: Move to pending
echo "Test 6: Move bundle to pending queue"
curl -sf -X POST "$BASE_URL/bundles/$BUNDLE_ID/to-pending" > /dev/null && echo "✓ Moved to pending" || echo "⚠ Already in pending"
echo ""

# Test 7: Check forwarding eligibility
echo "Test 7: Check forwarding eligibility"
FORWARD_CHECK=$(curl -sf -X POST "$BASE_URL/bundles/$BUNDLE_ID/forward?peer_trust_score=0.8&peer_is_local=true")
CAN_FORWARD=$(echo "$FORWARD_CHECK" | python3 -c "import sys, json; print(json.load(sys.stdin)['can_forward'])")
echo "✓ Can forward to peer: $CAN_FORWARD"
echo ""

# Test 8: Get sync index
echo "Test 8: Get sync index"
INDEX_COUNT=$(curl -sf "$BASE_URL/sync/index?queue=pending&limit=100" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "✓ Sync index contains $INDEX_COUNT bundles"
echo ""

# Test 9: Pull bundles for forwarding
echo "Test 9: Pull bundles for forwarding"
PULL_RESULT=$(curl -sf "$BASE_URL/sync/pull?max_bundles=5&peer_trust_score=0.5&peer_is_local=true")
PULL_COUNT=$(echo "$PULL_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_count'])")
echo "✓ Pulled $PULL_COUNT bundles for forwarding"
echo ""

# Test 10: Queue statistics
echo "Test 10: Queue statistics"
STATS=$(curl -sf "$BASE_URL/bundles/stats/queues")
echo "✓ Queue stats:"
echo "$STATS" | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f'   {k}: {v}') for k, v in data['queue_counts'].items()]"
echo ""

# Test 11: Sync statistics
echo "Test 11: Sync statistics"
SYNC_STATS=$(curl -sf "$BASE_URL/sync/stats")
CACHE_USAGE=$(echo "$SYNC_STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['cache']['usage_percentage'])")
echo "✓ Cache usage: ${CACHE_USAGE}%"
echo ""

# Test 12: Create perishable bundle
echo "Test 12: Create perishable food bundle"
FOOD_BUNDLE=$(curl -sf -X POST "$BASE_URL/bundles" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"type": "offer", "content": "Fresh apples, expires tomorrow"},
    "payloadType": "vf:Listing",
    "priority": "perishable",
    "audience": "local",
    "topic": "mutual-aid",
    "tags": ["food", "perishable", "apples"]
  }')
FOOD_ID=$(echo "$FOOD_BUNDLE" | python3 -c "import sys, json; print(json.load(sys.stdin)['bundleId'])")
echo "✓ Created perishable food bundle: ${FOOD_ID:0:20}..."
TTL=$(echo "$FOOD_BUNDLE" | python3 -c "import sys, json; b = json.load(sys.stdin); from datetime import datetime; created = datetime.fromisoformat(b['createdAt']); expires = datetime.fromisoformat(b['expiresAt']); print(int((expires - created).total_seconds() / 3600))")
echo "  TTL: ${TTL} hours (should be ~48 hours for perishable food)"
echo ""

echo "============================================"
echo "All API tests passed!"
echo "============================================"
