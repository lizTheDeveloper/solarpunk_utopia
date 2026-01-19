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
echo ""

# Show pip platform tags
echo "2. Pip Platform Tags:"
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
echo "3. Checking PyPI for pydantic-core wheels..."
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
echo "4. Testing pip install (dry-run):"
pip install --dry-run --only-binary :all: pydantic-core 2>&1 | head -20
echo ""

echo "5. Recommendation:"
echo "   If no ARM wheels found, try:"
echo "   - Skip pydantic entirely (use httpx directly)"
echo "   - Install from Termux pkg: pkg install python-pydantic (if available)"
echo "   - Compile with Rust: pkg install rust && pip install pydantic"
echo ""
