#!/bin/bash
# Diagnose why binary wheels aren't working on Termux

echo "======================================"
echo "Termux Binary Wheel Diagnostics"
echo "======================================"
echo ""

# Show platform info
echo "1. Platform Information:"
echo "   Architecture: $(uname -m)"
echo "   Kernel: $(uname -s)"
echo "   Python version: $(python --version 2>&1)"
echo "   Termux version: ${TERMUX_VERSION:-not set}"
echo ""

# Show libc version
echo "2. C Library (the critical difference):"
if ldd --version 2>/dev/null | head -1; then
    echo "   Type: glibc (normal Linux)"
    echo "   ✓ Should work with manylinux wheels"
else
    echo "   Type: Bionic (Android)"
    echo "   ✗ Incompatible with manylinux wheels (requires glibc)"
    echo "   → This is why binary wheels don't work on Termux"
fi
echo ""

# Show pip platform tags
echo "3. Pip Platform Tags:"
python -c "
import sys
try:
    from pip._internal.utils.compatibility_tags import get_supported
    tags = list(get_supported())
    print(f'   Total tags: {len(tags)}')
    print('   First 5 tags:')
    for tag in tags[:5]:
        print(f'     {tag}')
except Exception as e:
    print(f'   Error: {e}')
"
echo ""

# Check what pydantic-core versions exist with wheels
echo "4. Checking PyPI for pydantic-core wheels..."
python -c "
import json
import urllib.request

try:
    url = 'https://pypi.org/pypi/pydantic-core/json'
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    # Get latest version
    latest = data['info']['version']
    print(f'   Latest version: {latest}')

    # Check wheels for latest
    wheels = [f for f in data['urls'] if f['packagetype'] == 'bdist_wheel']
    print(f'   Total wheels for {latest}: {len(wheels)}')

    # Show ARM wheels
    arm_wheels = [w for w in wheels if 'aarch64' in w['filename'] or 'arm' in w['filename']]
    if arm_wheels:
        print(f'   ARM wheels found: {len(arm_wheels)}')
        for w in arm_wheels[:3]:
            print(f'     {w[\"filename\"]}')
    else:
        print('   No ARM wheels found')

except Exception as e:
    print(f'   Error: {e}')
"
echo ""

# Try to install with verbose output
echo "5. Testing pip install (dry-run):"
pip install --dry-run --only-binary :all: pydantic-core 2>&1 | head -20
echo ""

echo "6. Recommendation:"
echo "   The issue: Termux uses Bionic libc (Android), not glibc (Linux)"
echo "   PyPI wheels are built for manylinux (glibc), so they're incompatible"
echo ""
echo "   Solutions:"
echo "   1. Skip pydantic entirely (recommended)"
echo "      - Core functionality works without it"
echo "      - Use httpx for LLM backends (already works)"
echo ""
echo "   2. Compile from source (advanced)"
echo "      - Run: ./scripts/compile_pydantic_termux.sh"
echo "      - Takes 5-15 minutes, requires Rust"
echo "      - Phone may get warm"
echo ""
