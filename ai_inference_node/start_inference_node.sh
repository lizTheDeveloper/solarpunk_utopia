#!/bin/bash
# Start AI Inference Node - Share your compute with the mesh!

set -e

echo "🤖 Solarpunk AI Inference Node"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo ""
    echo "This inference node uses Ollama for easy AI model management."
    echo ""
    echo "Install Ollama:"
    echo "  • macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  • Or visit: https://ollama.com"
    echo ""
    read -p "Continue without Ollama? (you'll need another backend) [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    if ! curl -s http://localhost:11434 &> /dev/null; then
        echo -e "${BLUE}Starting Ollama...${NC}"
        ollama serve &> /dev/null &
        sleep 2
    fi

    # Check if default model is available
    if ! ollama list | grep -q "llama3.2:3b"; then
        echo -e "${YELLOW}Default model not found. Downloading llama3.2:3b...${NC}"
        echo "This may take a few minutes..."
        ollama pull llama3.2:3b
    fi
fi

# Create Python virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q fastapi uvicorn httpx structlog pydantic

# Environment configuration
export NODE_ID="${NODE_ID:-inference-node-$(openssl rand -hex 4)}"
export INFERENCE_BACKEND="${INFERENCE_BACKEND:-ollama}"
export INFERENCE_URL="${INFERENCE_URL:-http://localhost:11434}"
export DEFAULT_MODEL="${DEFAULT_MODEL:-llama3.2:3b}"
export PORT="${PORT:-8005}"

# Resource limits
export MAX_CONCURRENT="${MAX_CONCURRENT:-5}"
export MAX_TOKENS="${MAX_TOKENS:-2048}"
export TIMEOUT="${TIMEOUT:-120}"

# Mesh network integration
export DTN_BUNDLE_URL="${DTN_BUNDLE_URL:-http://localhost:8000}"
export REGISTER_WITH_MESH="${REGISTER_WITH_MESH:-true}"
export TRACK_CONTRIBUTIONS="${TRACK_CONTRIBUTIONS:-true}"

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo -e "${GREEN}Starting AI Inference Node...${NC}"
echo ""
echo "Configuration:"
echo "  Node ID:        $NODE_ID"
echo "  Backend:        $INFERENCE_BACKEND"
echo "  Default Model:  $DEFAULT_MODEL"
echo "  Port:           $PORT"
echo "  Max Concurrent: $MAX_CONCURRENT"
echo ""
echo "Endpoints:"
echo "  Status:    http://localhost:$PORT/status"
echo "  Inference: http://localhost:$PORT/inference"
echo "  Docs:      http://localhost:$PORT/docs"
echo ""
echo -e "${YELLOW}Gift Economy Mode: ${NC}Your contributions will be tracked!"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python inference_server.py
