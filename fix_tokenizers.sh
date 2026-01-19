#!/bin/bash
# Fix for tokenizers/maturin build errors
# This script reinstalls packages that might fail to build from source

# Note: Don't use 'set -e' - we want to show errors but not exit the terminal

echo "================================================"
echo "Fixing tokenizers/maturin build errors"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Python version
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
    echo -e "${BLUE}Detected Python version: ${PY_VERSION}${NC}"

    if [[ "$PY_VERSION" == "3.12"* ]]; then
        echo -e "${RED}================================================${NC}"
        echo -e "${RED}ERROR: Python 3.12 is not compatible!${NC}"
        echo -e "${RED}================================================${NC}"
        echo -e "${YELLOW}The tokenizers package requires Rust/maturin to build on Python 3.12${NC}"
        echo -e "${YELLOW}and Rust installation fails with Python 3.12${NC}"
        echo ""
        echo -e "${YELLOW}SOLUTION: Install Python 3.11 instead${NC}"
        echo ""
        echo "On macOS:"
        echo "  brew install python@3.11"
        echo "  rm -rf venv"
        echo "  python3.11 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  ./setup.sh"
        echo ""
        echo "On Linux:"
        echo "  sudo apt-get install python3.11 python3.11-venv  # Debian/Ubuntu"
        echo "  sudo dnf install python3.11                      # Fedora"
        echo "  rm -rf venv"
        echo "  python3.11 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  ./setup.sh"
        echo ""
        return
    fi
fi

# Check if in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Virtual environment not activated. Activating...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: venv not found. Please run setup.sh first${NC}"
        return
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
