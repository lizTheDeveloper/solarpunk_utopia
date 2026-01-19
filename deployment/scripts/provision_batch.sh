#!/bin/bash
# Solarpunk Batch Phone Provisioning Script
# Provisions multiple phones in parallel

# Note: Don't use 'set -e' - we want to show errors but not exit the terminal

# Default values
ROLE="citizen"
COUNT=1
MAX_PARALLEL=5

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Provision multiple phones in parallel.

OPTIONS:
    --role=ROLE         Phone role for all phones (default: citizen)
    --count=N           Number of phones to provision (default: 1)
    --parallel=N        Max parallel provisions (default: 5)
    -h, --help          Show this help

EXAMPLES:
    $0 --role=citizen --count=10
    $0 --role=bridge --count=3 --parallel=3

PREREQUISITES:
    - Multiple phones connected via USB hub
    - adb installed
    - USB debugging enabled on all phones

EOF
    return
}

# Parse arguments
for arg in "$@"; do
    case $arg in
        --role=*)
            ROLE="${arg#*=}"
            ;;
        --count=*)
            COUNT="${arg#*=}"
            ;;
        --parallel=*)
            MAX_PARALLEL="${arg#*=}"
            ;;
        -h|--help)
            usage
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get list of connected devices
get_devices() {
    adb devices | grep -v "List" | grep "device$" | awk '{print $1}'
}

main() {
    print_info "Starting batch provisioning..."
    print_info "Role: $ROLE"
    print_info "Target count: $COUNT"
    print_info "Max parallel: $MAX_PARALLEL"
    echo ""

    # Get connected devices
    local devices=($(get_devices))
    local device_count=${#devices[@]}

    if [ "$device_count" -eq 0 ]; then
        print_error "No devices connected"
        return
    fi

    if [ "$device_count" -lt "$COUNT" ]; then
        print_warn "Only $device_count devices connected, but $COUNT requested"
        COUNT=$device_count
    fi

    print_info "Found $device_count connected devices"
    echo ""

    # Create results directory
    local results_dir="$SCRIPT_DIR/../results/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$results_dir"

    # Provision devices in batches
    local provisioned=0
    local failed=0
    local pids=()

    for ((i=0; i<COUNT; i++)); do
        local serial="${devices[$i]}"
        local log_file="$results_dir/provision_${serial}.log"

        print_info "Starting provisioning for device $((i+1))/$COUNT: $serial"

        # Start provisioning in background
        ("$SCRIPT_DIR/provision_phone.sh" --role="$ROLE" --serial="$serial" > "$log_file" 2>&1 && \
            echo "SUCCESS:$serial" || echo "FAILED:$serial") &
        pids+=($!)

        # Wait if we've hit max parallel
        if [ ${#pids[@]} -ge "$MAX_PARALLEL" ]; then
            print_info "Waiting for batch to complete..."
            for pid in "${pids[@]}"; do
                wait "$pid"
            done
            pids=()
        fi
    done

    # Wait for remaining processes
    if [ ${#pids[@]} -gt 0 ]; then
        print_info "Waiting for final batch..."
        for pid in "${pids[@]}"; do
            wait "$pid"
        done
    fi

    echo ""
    print_info "Batch provisioning complete!"
    print_info "Results saved to: $results_dir"

    # Summarize results
    local success_count=$(grep -l "SUCCESS:" "$results_dir"/*.log 2>/dev/null | wc -l)
    local failed_count=$(grep -l "FAILED:" "$results_dir"/*.log 2>/dev/null | wc -l)

    echo ""
    print_info "Summary:"
    echo "  Success: $success_count"
    echo "  Failed: $failed_count"
    echo ""

    if [ "$failed_count" -gt 0 ]; then
        print_warn "Some devices failed. Check logs in $results_dir"
        return
    fi
}

main
