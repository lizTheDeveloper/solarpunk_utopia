#!/bin/bash

echo "==========================================="
echo "📱 MONITORING FOR PHONE ACTIVITY"
echo "==========================================="
echo ""
echo "Watching for:"
echo "  • HTTP requests to backend services"
echo "  • New listings in database"
echo "  • DTN bundle activity"
echo "  • WiFi Direct connections"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "==========================================="
echo ""

# Function to check backend service logs
check_service_logs() {
    echo "🔍 Backend Service Activity:"

    # Check ValueFlows Node access
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "  ✅ ValueFlows Node (port 8001) - RUNNING"
    else
        echo "  ❌ ValueFlows Node (port 8001) - DOWN"
    fi

    # Check Bridge Node
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "  ✅ Bridge Node (port 8002) - RUNNING"
    else
        echo "  ❌ Bridge Node (port 8002) - DOWN"
    fi

    echo ""
}

# Function to monitor database changes
monitor_database() {
    echo "📊 Current Database State:"

    # Count listings
    LISTING_COUNT=$(curl -s http://localhost:8001/vf/listings | jq '.listings | length' 2>/dev/null || echo "0")
    echo "  • Total listings: $LISTING_COUNT"

    # Get latest listing
    LATEST=$(curl -s http://localhost:8001/vf/listings | jq -r '.listings[0].created_at' 2>/dev/null || echo "none")
    echo "  • Latest listing created: $LATEST"

    echo ""
}

# Function to watch for new HTTP requests
monitor_requests() {
    echo "🌐 Watching for HTTP Requests (last 5 seconds):"

    # Use lsof to check for active connections on our ports
    CONNECTIONS=$(lsof -i :8001,8002,4444 -n 2>/dev/null | grep -c ESTABLISHED || echo "0")
    echo "  • Active connections: $CONNECTIONS"

    echo ""
}

# Initial status
check_service_logs
monitor_database

echo "==========================================="
echo "🔄 LIVE MONITORING (updates every 5 seconds)"
echo "==========================================="
echo ""

# Continuous monitoring loop
LAST_COUNT=0
while true; do
    sleep 5

    # Get current listing count
    CURRENT_COUNT=$(curl -s http://localhost:8001/vf/listings | jq '.listings | length' 2>/dev/null || echo "0")

    # Check for changes
    if [ "$CURRENT_COUNT" != "$LAST_COUNT" ]; then
        echo "🎉 NEW ACTIVITY DETECTED! Listing count changed: $LAST_COUNT → $CURRENT_COUNT"
        echo ""
        monitor_database
        LAST_COUNT=$CURRENT_COUNT
    fi

    # Monitor active connections
    monitor_requests

    # Show timestamp
    echo "⏰ $(date '+%H:%M:%S') - Monitoring... (Listings: $CURRENT_COUNT)"
    echo ""
done
