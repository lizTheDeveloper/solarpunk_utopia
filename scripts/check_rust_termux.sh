#!/bin/bash
# Check if Rust can be installed and used on Termux

echo "Checking Rust availability on Termux..."
echo "========================================"
echo ""

# Check if rust is available via pkg
echo "1. Checking pkg repository..."
if command -v pkg &> /dev/null; then
    echo "   pkg available - checking for rust package..."
    pkg search "^rust$" 2>/dev/null || echo "   Rust not found in pkg repository"
    pkg search "cargo" 2>/dev/null || echo "   Cargo not found in pkg repository"
else
    echo "   pkg not available (not on Termux)"
fi

echo ""
echo "2. Checking if Rust is already installed..."
if command -v rustc &> /dev/null; then
    rustc --version
    echo "   ✅ Rust is installed"
else
    echo "   ❌ Rust is not installed"
fi

if command -v cargo &> /dev/null; then
    cargo --version
    echo "   ✅ Cargo is installed"
else
    echo "   ❌ Cargo is not installed"
fi

echo ""
echo "3. Checking rustup (Rust installer)..."
if [ -f "$HOME/.cargo/bin/rustup" ]; then
    $HOME/.cargo/bin/rustup --version
    echo "   ✅ rustup is installed"
else
    echo "   ❌ rustup is not installed"
    echo ""
    echo "To install rustup on Termux:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
fi

echo ""
echo "4. Known Termux + Rust issues:"
echo "   - Rust CAN be installed via rustup"
echo "   - But maturin (Python build tool) often fails"
echo "   - Building pydantic-core/tokenizers is unreliable"
echo "   - Binary wheels are preferred when available"
echo ""
echo "Recommendation:"
echo "  Use --only-binary flag to avoid Rust builds when possible"
echo "  Binary wheels exist for most packages on aarch64"
