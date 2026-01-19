# Termux Scripts

Tools for diagnosing and fixing package installation issues on Termux (Android).

## The Problem

**Binary wheels from PyPI don't work on Termux** because:

- **Termux uses**: Bionic libc (Android's C library)
- **PyPI wheels need**: glibc (GNU C Library, standard Linux)
- **Result**: Packages like `pydantic-core` that have "ARM wheels" won't install

Even though Termux is `linux_aarch64`, the wheels are built for `manylinux_aarch64` which requires glibc.

## Available Tools

### 1. diagnose_termux_wheels.sh

**Diagnose why binary wheels don't work on your device.**

```bash
./scripts/diagnose_termux_wheels.sh
```

**Shows:**
- Your platform (architecture, kernel, Python version)
- C library type (Bionic vs glibc) - this is the critical difference
- Pip platform tags (what pip thinks your system is)
- Available wheels from PyPI
- Why they're incompatible

**Use when:**
- You're confused why `--only-binary` fails
- You want to understand the libc mismatch
- Debugging installation issues

### 2. compile_pydantic_termux.sh

**Compile pydantic-core from source for Termux.**

```bash
./scripts/compile_pydantic_termux.sh
```

**What it does:**
1. Installs Rust compiler via `pkg install rust`
2. Sets up Rust environment (PATH, CARGO_HOME)
3. Compiles pydantic-core from source (5-15 minutes)
4. Installs pydantic and pydantic-settings
5. Verifies the installation works

**Requirements:**
- ~500MB free space
- 5-15 minutes of time
- Phone will get warm (this is normal)
- Battery: Keep phone charging during compilation

**Use when:**
- You need FastAPI on Termux
- You want pydantic validation
- You're willing to wait for compilation

### 3. find_working_pydantic.py

**Check PyPI for pydantic versions with ARM wheels.**

```bash
python scripts/find_working_pydantic.py
```

**Shows:**
- Recent pydantic-core versions with wheels
- Which specific wheels are available (aarch64, armv7l, any)
- Recommended versions to try

**Note:** Even if it shows ARM wheels, they won't work on Termux (glibc vs Bionic issue).

**Use when:**
- You want to see what's available on PyPI
- Debugging on normal Linux ARM systems (not Termux)

## Quick Start Guide

### Automatic Installation (Default)

```bash
# Just run setup - it automatically compiles pydantic on Termux
./setup.sh

# What happens:
# 1. Tries binary wheel (usually fails on Termux)
# 2. Installs Rust compiler automatically
# 3. Compiles pydantic from source (5-15 min)
# 4. Installs all packages including FastAPI
```

**That's it!** No flags, no extra steps. Everything is automatic.

### If Compilation Fails

If pydantic compilation fails, core functionality still works:

```bash
# What works without pydantic:
# ✓ DTN Bundle System
# ✓ ValueFlows
# ✓ Mesh networking
# ✓ AI agents (httpx backends)
# ✓ Database

# To retry compilation manually:
./scripts/compile_pydantic_termux.sh
```

## Common Issues

### "No matching distribution found"

**Cause:** Trying to install binary-only with `--only-binary :all:`
**Solution:** Either compile from source OR skip the package

### "Rust compiler not found"

**Cause:** maturin/setuptools-rust needs Rust to compile
**Solution:** `pkg install rust`

### "Memory error" during compilation

**Cause:** Phone ran out of RAM
**Solution:**
- Close all other apps
- Reduce parallel jobs: `export CARGO_BUILD_JOBS=1`
- Restart Termux and try again

### Compilation takes forever

**Normal:** 5-15 minutes on phone hardware
**Too long:** If >30 minutes, something's wrong:
- Check `/tmp/pydantic_compile.log`
- Make sure Rust is installed: `rustc --version`
- Try with fewer parallel jobs

### Phone gets very hot

**Normal:** Compilation is CPU-intensive
**Solution:**
- Keep phone in a cool place
- Don't use phone during compilation
- Consider using wake-lock to prevent sleep

## Technical Details

### Why Binary Wheels Don't Work

```python
# What pip sees on Termux
import sysconfig
sysconfig.get_platform()
# Returns: 'linux-aarch64'

# What PyPI wheels need
# Filename: pydantic_core-2.9.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
# Requires: manylinux (glibc 2.17+)

# What Termux has
# C Library: Bionic (Android's libc, not glibc)
# Result: Incompatible, wheel rejected
```

### Compilation Process

```bash
# 1. Download source distribution (.tar.gz)
pip download --no-binary pydantic-core pydantic-core

# 2. Extract and run setup.py
python setup.py build

# 3. setuptools-rust invokes cargo (Rust compiler)
cargo build --release

# 4. Build wheel from compiled artifacts
python setup.py bdist_wheel

# 5. Install the wheel
pip install ./dist/pydantic_core-*.whl
```

### Memory Usage

- **Rust compiler**: ~200MB
- **pydantic-core source**: ~50MB
- **Build artifacts**: ~150MB
- **Peak RAM usage**: ~1GB (during linking)

### Build Time

- **Fast phone (Snapdragon 8 Gen 2)**: 3-5 minutes
- **Mid-range phone**: 8-12 minutes
- **Older phone**: 15-25 minutes

## Alternatives to Pydantic

If compilation fails or takes too long, you can run the system without pydantic:

### What Still Works

```python
# LLM backends (Anthropic, OpenAI, HuggingFace)
from app.llm.backends import AnthropicBackend
backend = AnthropicBackend(config)
response = await backend.generate("Hello")

# Database operations
import aiosqlite
async with aiosqlite.connect("db.sqlite") as db:
    await db.execute("CREATE TABLE ...")

# DTN Bundle System
from app.bundle import BundleProtocol
bundle = BundleProtocol()

# Mesh networking
from mesh_network.batman import setup_batman_adv
```

### What Doesn't Work

- FastAPI (requires pydantic)
- REST API endpoints (/docs, /health)
- OpenAPI schema generation
- Request/response validation

### Workaround

Use the Python services directly without FastAPI wrapper:

```python
# Instead of HTTP API calls
response = requests.post("http://localhost:8000/bundles", json=data)

# Call Python functions directly
from app.services import create_bundle
bundle = await create_bundle(data)
```

## See Also

- [docs/TERMUX_PYDANTIC.md](../docs/TERMUX_PYDANTIC.md) - Full pydantic strategy
- [CLAUDE.md](../CLAUDE.md) - Project setup instructions
- [setup.sh](../setup.sh) - Main installation script
