#!/bin/bash

# Solarpunk Mesh Network - Service Orchestration Script
# Runs all backend services in separate terminal tabs/windows

# Note: Don't use 'set -e' - we want to show errors but not exit the terminal

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
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    if python3 -m venv venv 2>/dev/null || python -m venv venv 2>/dev/null; then
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        echo -e "${YELLOW}Cannot continue without venv${NC}"
        echo -e "${YELLOW}Please run: ./setup.sh${NC}"
        return
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
echo -e "${BLUE}Checking dependencies...${NC}"

# Check for core dependencies
MISSING_DEPS=false
for module in fastapi uvicorn aiosqlite; do
    if ! python -c "import $module" 2>/dev/null; then
        echo -e "${YELLOW}Missing: $module${NC}"
        MISSING_DEPS=true
    fi
done

if [ "$MISSING_DEPS" = true ]; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"

    # Detect Termux
    IS_TERMUX=false
    if [ -n "$TERMUX_VERSION" ] || [ -n "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
        IS_TERMUX=true
    fi

    if [ "$IS_TERMUX" = true ]; then
        # Install individually on Termux
        for pkg in fastapi uvicorn aiosqlite httpx python-multipart structlog; do
            pip install "$pkg" 2>/dev/null || echo -e "${YELLOW}  Skipped: $pkg${NC}"
        done
    else
        # Bulk install on other platforms
        pip install -r requirements.txt 2>&1 | grep -v "^Requirement already satisfied" || true
    fi

    echo -e "${GREEN}✓ Dependencies checked${NC}"
else
    echo -e "${GREEN}✓ All dependencies installed${NC}"
fi

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

    # Check if command can be executed
    if ! bash -c "source venv/bin/activate && which python" > /dev/null 2>&1; then
        echo -e "${RED}✗ ${name} - Python not available in venv${NC}"
        return
    fi

    # Run in background and save PID
    bash -c "source venv/bin/activate && $command" > "$log_file" 2>&1 &
    local pid=$!

    # Check if process started successfully
    sleep 1
    if kill -0 $pid 2>/dev/null; then
        echo $pid > "logs/${name}.pid"
        echo -e "${GREEN}✓ ${name} started (PID: $pid, logs: $log_file)${NC}"
    else
        echo -e "${RED}✗ ${name} failed to start - check $log_file${NC}"
        # Show last few lines of log
        if [ -f "$log_file" ]; then
            echo -e "${YELLOW}Last error:${NC}"
            tail -n 3 "$log_file" | sed 's/^/  /'
        fi
    fi

    # Give it a moment to fully initialize
    sleep 1
}

# Clean up old log files
rm -rf logs/*.log logs/*.pid 2>/dev/null || true

# Start services
start_service "dtn_bundle_system" "python -m app.main" "8000"
start_service "valueflows_node" "cd valueflows_node && python -m app.main" "8001"
start_service "discovery_search" "python -m discovery_search.main" "8001"
start_service "file_chunking" "python -m file_chunking.main" "8001"
start_service "bridge_management" "python -m mesh_network.bridge_node.main" "8002"

# Start AI inference node if available
if [ -f "ai_inference_node/inference_server.py" ] && command -v ollama &> /dev/null; then
    # Start Ollama if not running
    if ! curl -s http://localhost:11434 &> /dev/null; then
        echo -e "${BLUE}Starting Ollama service...${NC}"
        ollama serve > logs/ollama.log 2>&1 &
        sleep 2
    fi

    # Set default model to lightweight version
    export DEFAULT_MODEL="${DEFAULT_MODEL:-llama3.2:1b}"
    export ENABLE_PRIORITIES="true"
    export PORT="8005"

    # Start inference node
    cd ai_inference_node
    start_service "ai_inference_node" "python inference_server.py" "8005"
    cd ..
fi

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

if [ -f "logs/ai_inference_node.pid" ]; then
    echo -e "  ${GREEN}AI Inference Node:      http://localhost:8005${NC}"
    echo -e "  ${GREEN}AI Inference Docs:      http://localhost:8005/docs${NC}"
    echo -e "  ${GREEN}AI Status:              http://localhost:8005/status${NC}"
fi
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

if [ -f "logs/ai_inference_node.pid" ]; then
    check_health "AI Inference Node" "http://localhost:8005/"
    echo -e "${GREEN}AI inference available with priority: Local > Community > Network${NC}"
fi

echo ""
echo -e "${GREEN}Solarpunk Mesh Network is running!${NC}"
echo ""

# Tail the DTN logs to show activity
echo -e "${BLUE}Showing DTN Bundle System logs (Ctrl+C to exit, services keep running):${NC}"
echo ""
tail -f logs/dtn_bundle_system.log
