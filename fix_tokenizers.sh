#!/bin/bash
# Fix for tokenizers/maturin build errors
# This script reinstalls packages that might fail to build from source

set -e

echo "================================================"
echo "Fixing tokenizers/maturin build errors"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Virtual environment not activated. Activating...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: venv not found. Please run setup.sh first${NC}"
        return 1
    fi
fi

echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

echo ""
echo -e "${BLUE}Uninstalling tokenizers (if present)...${NC}"
pip uninstall -y tokenizers 2>/dev/null || echo "tokenizers not installed, skipping"

echo ""
echo -e "${BLUE}Installing tokenizers from prebuilt wheel (no source build)...${NC}"
pip install --only-binary :all: tokenizers

echo ""
echo -e "${BLUE}Reinstalling anthropic with binary-only tokenizers...${NC}"
pip install --only-binary tokenizers --force-reinstall anthropic

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Fix complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}If you still have issues, you can:${NC}"
echo ""
echo "1. Install Rust (if you want to build from source):"
echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
echo ""
echo "2. Or use an older version without Rust dependencies:"
echo "   pip install 'tokenizers<0.14' --force-reinstall"
echo ""
echo "3. Or skip the anthropic package entirely (remove from requirements.txt)"
echo ""
