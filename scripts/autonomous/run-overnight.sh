#!/bin/bash
# Run Autonomous Workers Overnight
# Development worker every 30 minutes
# Gap analysis every 6 hours

set -e

PROJECT_DIR="/Users/annhoward/src/solarpunk_utopia"
SCRIPTS_DIR="$PROJECT_DIR/scripts/autonomous"
LOG_DIR="$PROJECT_DIR/logs/autonomous"

mkdir -p "$LOG_DIR"

echo "=== Starting Overnight Autonomous Workers ==="
echo "Started: $(date)"
echo "Development worker: every 30 minutes (Sonnet)"
echo "Gap analysis: every 6 hours (Opus)"
echo ""
echo "Logs: $LOG_DIR"
echo "Press Ctrl+C to stop"
echo ""

# Track time for gap analysis (every 6 hours = 360 minutes)
MINUTES_SINCE_GAP_ANALYSIS=360  # Run immediately on start

while true; do
    echo "---"
    echo "Cycle start: $(date)"

    # Run development worker (every cycle = every 30 min)
    echo "Running development worker (Sonnet)..."
    bash "$SCRIPTS_DIR/development-worker.sh" &
    DEV_PID=$!

    # Check if it's time for gap analysis (every 6 hours)
    if [ $MINUTES_SINCE_GAP_ANALYSIS -ge 360 ]; then
        echo "Running gap analysis worker (Opus)..."
        bash "$SCRIPTS_DIR/gap-analysis-worker.sh" &
        GAP_PID=$!
        MINUTES_SINCE_GAP_ANALYSIS=0
    fi

    # Wait for development worker to complete
    wait $DEV_PID 2>/dev/null || true

    # If gap analysis is running, wait for it too
    if [ ! -z "$GAP_PID" ]; then
        wait $GAP_PID 2>/dev/null || true
        unset GAP_PID
    fi

    echo "Cycle complete: $(date)"
    echo "Sleeping 30 minutes..."

    # Sleep 30 minutes
    sleep 1800

    MINUTES_SINCE_GAP_ANALYSIS=$((MINUTES_SINCE_GAP_ANALYSIS + 30))
done
