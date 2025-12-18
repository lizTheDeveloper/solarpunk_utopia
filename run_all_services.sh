#!/bin/bash

# Solarpunk Mesh Network - Service Orchestration Script
# Runs all backend services in separate terminal tabs/windows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Solarpunk Mesh Network - Service Launcher${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo -e "${YELLOW}Please create venv first: python3 -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
echo -e "${BLUE}Checking dependencies...${NC}"
python -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
}

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file="logs/${name}.log"

    mkdir -p logs

    echo -e "${BLUE}Starting ${name} on port ${port}...${NC}"

    # Run in background and save PID
    bash -c "source venv/bin/activate && $command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "logs/${name}.pid"

    echo -e "${GREEN}✓ ${name} started (PID: $pid, logs: $log_file)${NC}"

    # Give it a moment to start
    sleep 2
}

# Clean up old log files
rm -rf logs/*.log logs/*.pid 2>/dev/null || true

# Start services
start_service "dtn_bundle_system" "python -m app.main" "8000"
start_service "valueflows_node" "python -m valueflows_node.main" "8001"
start_service "discovery_search" "python -m discovery_search.main" "8001"
start_service "file_chunking" "python -m file_chunking.main" "8001"
start_service "bridge_management" "python -m mesh_network.bridge_node.main" "8002"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All services started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Service Endpoints:${NC}"
echo -e "  DTN Bundle System:      http://localhost:8000"
echo -e "  DTN API Docs:           http://localhost:8000/docs"
echo -e "  ValueFlows Node:        http://localhost:8001"
echo -e "  ValueFlows API Docs:    http://localhost:8001/docs"
echo -e "  Discovery & Search:     http://localhost:8001"
echo -e "  File Chunking:          http://localhost:8001"
echo -e "  Bridge Management:      http://localhost:8002"
echo -e "  Bridge API Docs:        http://localhost:8002/docs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  All logs are in: ${SCRIPT_DIR}/logs/"
echo -e "  View DTN logs:   tail -f logs/dtn_bundle_system.log"
echo -e "  View VF logs:    tail -f logs/valueflows_node.log"
echo ""
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  ./stop_all_services.sh"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop watching logs, services will continue running${NC}"
echo ""

# Wait a bit for services to fully start
sleep 3

# Check health
echo -e "${BLUE}Checking service health...${NC}"
echo ""

check_health() {
    local name=$1
    local url=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${name} is healthy${NC}"
    else
        echo -e "${RED}✗ ${name} failed to start - check logs/${name}.log${NC}"
    fi
}

check_health "DTN Bundle System" "http://localhost:8000/health"
check_health "Bridge Management" "http://localhost:8002/bridge/health"

echo ""
echo -e "${GREEN}Solarpunk Mesh Network is running!${NC}"
echo ""

# Tail the DTN logs to show activity
echo -e "${BLUE}Showing DTN Bundle System logs (Ctrl+C to exit, services keep running):${NC}"
echo ""
tail -f logs/dtn_bundle_system.log
