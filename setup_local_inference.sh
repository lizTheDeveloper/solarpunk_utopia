#!/bin/bash
# Auto-setup AI Inference Node (called by main setup.sh)

# Note: Don't use 'set -e' - we want to show errors but not exit the terminal

echo "🤖 Setting up AI Inference Node"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect if we can run AI inference
CAN_RUN_AI=false

# Check for Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama found${NC}"
    CAN_RUN_AI=true
else
    echo -e "${YELLOW}ℹ Ollama not installed${NC}"
    echo ""
    echo "Would you like to enable AI inference on this device?"
    echo "This lets you share compute with the mesh network."
    echo ""
    echo "Install Ollama to enable:"
    echo "  • macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  • Android/Termux: pkg install ollama (if available)"
    echo ""
    read -p "Skip AI inference setup? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}Skipping AI inference setup${NC}"
        echo "You can run ./ai_inference_node/start_inference_node.sh later"
        exit 0
    fi
fi

# Install AI inference node requirements
echo -e "${BLUE}Installing AI inference dependencies...${NC}"
cd ai_inference_node

# Use existing venv if available, create if not
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# If Ollama is available, pull default model
if command -v ollama &> /dev/null; then
    # Check if Ollama server is running
    if ! curl -s http://localhost:11434 &> /dev/null; then
        echo -e "${BLUE}Starting Ollama service...${NC}"
        ollama serve &> /dev/null &
        sleep 2
    fi

    # Check if we have the lightweight model
    if ! ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
        echo -e "${BLUE}Downloading lightweight AI model (llama3.2:1b - ~1.3GB)...${NC}"
        echo "This will run locally and provide AI to the mesh"
        ollama pull llama3.2:1b
    fi

    echo -e "${GREEN}✓ AI model ready${NC}"
    CAN_RUN_AI=true
fi

cd ..

if [ "$CAN_RUN_AI" = true ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}AI Inference Node Ready!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Your device will provide AI to the mesh network with priority:"
    echo "  1. Local requests (your device) - HIGHEST"
    echo "  2. Community members - MEDIUM"
    echo "  3. Everyone else - LOWEST"
    echo ""
    echo "The inference node will start automatically with other services."
    echo ""
    echo "Manual control:"
    echo "  Start: cd ai_inference_node && ./start_inference_node.sh"
    echo "  Test:  cd ai_inference_node && python test_inference.py"
    echo ""
else
    echo -e "${YELLOW}AI inference not enabled (Ollama not available)${NC}"
fi
