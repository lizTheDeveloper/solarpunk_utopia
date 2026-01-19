#!/bin/bash
# Compile pydantic-core for Termux (Android aarch64)
# The issue: PyPI wheels are manylinux (glibc), Termux uses Bionic libc

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}======================================"
echo "Compiling pydantic-core for Termux"
echo "======================================${NC}"
echo ""

# Check if we're on Termux
if [ -z "$TERMUX_VERSION" ]; then
    echo -e "${RED}This script is for Termux only${NC}"
    echo "Run it on your Android device in Termux"
    return
fi

echo -e "${BLUE}Platform: $(uname -m) $(uname -s)${NC}"
echo -e "${BLUE}Python: $(python --version 2>&1)${NC}"
echo ""

# Step 1: Install Rust and build tools
echo -e "${BLUE}1. Installing Rust compiler and build tools...${NC}"
if command -v rustc &> /dev/null; then
    echo -e "${GREEN}✓ Rust already installed: $(rustc --version)${NC}"
else
    echo -ne "  Installing Rust and binutils via pkg... "
    if pkg install -y rust binutils 2>&1 | grep -q "Setting up"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo -e "${YELLOW}Try manually: pkg install rust binutils${NC}"
        return
    fi
fi

# Set Rust environment
export PATH="$HOME/.cargo/bin:$PATH"
export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
export CARGO_BUILD_JOBS=2  # Limit parallel jobs to save memory

# Verify Rust is working
echo -ne "  Verifying Rust installation... "
if rustc --version >/dev/null 2>&1; then
    echo -e "${GREEN}✓ $(rustc --version)${NC}"
else
    echo -e "${RED}✗ Rust not in PATH${NC}"
    echo -e "${YELLOW}Check your PATH: echo \$PATH${NC}"
    return
fi

echo ""
echo -e "${BLUE}2. Preparing Python environment...${NC}"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠ No venv found - installing globally${NC}"
fi

# Upgrade pip and install build tools
echo -ne "  Upgrading pip... "
pip install --upgrade pip 2>&1 | tail -1
echo -e "${GREEN}✓${NC}"

echo -ne "  Installing build tools... "
pip install --upgrade setuptools wheel 2>&1 | tail -1
echo -e "${GREEN}✓${NC}"

echo -ne "  Installing maturin (Rust build tool)... "
pip install maturin setuptools-rust 2>&1 | tail -1
echo -e "${GREEN}✓${NC}"

echo ""
echo -e "${BLUE}3. Compiling pydantic-core from source...${NC}"
echo -e "${YELLOW}This will take 5-15 minutes on phone hardware${NC}"
echo -e "${YELLOW}Phone may get warm - this is normal${NC}"
echo ""

# Show progress
echo -e "${BLUE}Starting compilation...${NC}"
echo -e "${BLUE}(Press Ctrl+C to cancel if it takes too long)${NC}"
echo ""

# Compile with visible output
START_TIME=$(date +%s)

echo -e "${BLUE}Step 1/2: Building pydantic-core (this is the slow part)...${NC}"
if pip install --no-binary :all: pydantic-core 2>&1 | tee /tmp/pydantic_compile.log | grep -E "(Collecting|Building|Compiling|Finished|Successfully|error|ERROR)"; then
    echo ""
    echo -e "${GREEN}✓ pydantic-core built${NC}"

    # Now install pydantic and pydantic-settings
    echo ""
    echo -e "${BLUE}Step 2/2: Installing pydantic and pydantic-settings...${NC}"
    if pip install pydantic pydantic-settings 2>&1 | tail -5; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo ""
        echo -e "${GREEN}✓ pydantic installed in ${DURATION}s${NC}"

        # Verify it works
        echo ""
        echo -e "${BLUE}4. Verifying installation...${NC}"
        if python -c "from pydantic import BaseModel; print('✓ pydantic works!')" 2>/dev/null; then
            echo -e "${GREEN}✓ Installation verified${NC}"
            echo ""
            echo -e "${GREEN}======================================"
            echo "SUCCESS!"
            echo "======================================${NC}"
            echo -e "${GREEN}pydantic is now installed and working${NC}"
            echo ""
            echo -e "${YELLOW}You can now install FastAPI:${NC}"
            echo -e "  pip install fastapi"
            echo ""
        else
            echo -e "${RED}✗ Import failed${NC}"
        fi
    else
        echo -e "${RED}✗ pydantic install failed${NC}"
    fi
else
    echo ""
    echo -e "${RED}✗ pydantic-core compilation failed${NC}"
    echo ""
    echo -e "${YELLOW}Check the log: /tmp/pydantic_compile.log${NC}"
    echo -e "${YELLOW}Common issues:${NC}"
    echo -e "  - Low memory: Close other apps"
    echo -e "  - Rust version: pkg upgrade rust"
    echo -e "  - Python version: Should be 3.11"
    echo -e "  - Missing maturin: pip install maturin"
    echo ""
    echo -e "${YELLOW}Last 15 lines of error:${NC}"
    tail -15 /tmp/pydantic_compile.log | sed 's/^/  /'
fi
