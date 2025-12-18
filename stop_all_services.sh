#!/bin/bash

# Solarpunk Mesh Network - Stop All Services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Stopping Solarpunk Mesh Network Services${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="logs/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${BLUE}Stopping ${name} (PID: $pid)...${NC}"
            kill $pid 2>/dev/null || true
            # Wait a moment
            sleep 1
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}Force stopping ${name}...${NC}"
                kill -9 $pid 2>/dev/null || true
            fi
            echo -e "${GREEN}✓ ${name} stopped${NC}"
        else
            echo -e "${YELLOW}${name} was not running (stale PID file)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}No PID file for ${name}${NC}"
    fi
}

# Stop all services
stop_service "dtn_bundle_system"
stop_service "valueflows_node"
stop_service "discovery_search"
stop_service "file_chunking"
stop_service "bridge_management"

# Also try to find and kill any Python processes running our services
echo ""
echo -e "${BLUE}Checking for any remaining service processes...${NC}"

pkill -f "python -m app.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped DTN Bundle System${NC}" || true
pkill -f "python -m valueflows_node.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped ValueFlows Node${NC}" || true
pkill -f "python -m discovery_search.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped Discovery & Search${NC}" || true
pkill -f "python -m file_chunking.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped File Chunking${NC}" || true
pkill -f "python -m mesh_network.bridge_node.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped Bridge Management${NC}" || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All services stopped${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Logs preserved in: ${SCRIPT_DIR}/logs/${NC}"
echo ""
