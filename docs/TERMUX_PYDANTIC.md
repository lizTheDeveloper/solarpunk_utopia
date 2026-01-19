# Pydantic Installation on Termux

## Problem

Pydantic v2.x requires `pydantic-core`, which is a Rust-based extension. On Termux (Android), building Rust packages can be:
- Slow (5-10 minutes on phone hardware)
- Resource-intensive (drains battery, generates heat)
- Unreliable (Maturin build tool can fail)

## Solution Strategy

The `setup.sh` script uses a three-tier approach:

### 1. Try Specific Version with ARM Wheels (Fast)

```bash
pip install --only-binary :all: pydantic==2.9.2 pydantic-core==2.9.0
```

**Why**: These versions have confirmed ARM64 (aarch64) binary wheels on PyPI. Installation is instant.

**Versions with ARM wheels**:
- pydantic-core: 2.9.0, 2.8.0, 2.7.0, and most 2.x versions
- pydantic: Uses pure Python wheels (py3-none-any)

### 2. Try Latest Version with Wheels (Fallback)

```bash
pip install --only-binary :all: pydantic pydantic-settings
```

**Why**: Newer versions may have ARM wheels. Worth trying before compiling.

### 3. Install Rust and Compile (Last Resort)

```bash
pkg install -y rust
export PATH="$HOME/.cargo/bin:$PATH"
pip install pydantic pydantic-settings
```

**Why**: If no binary wheels exist for your architecture, compile from source.

**Downsides**:
- Takes 5-10 minutes
- Uses significant CPU/battery
- May fail on low-memory devices

## Finding Working Versions

Use `scripts/find_working_pydantic.py` to check PyPI for versions with ARM wheels:

```bash
python scripts/find_working_pydantic.py
```

**Output**:
```
✅ pydantic-core 2.9.0 has ARM wheels
✅ pydantic 2.9.2 (compatible)
   pip install --only-binary :all: pydantic==2.9.2
```

## Manual Installation

If automatic installation fails:

```bash
# Activate venv
source venv/bin/activate

# Try specific version with wheels
pip install --only-binary :all: pydantic==2.9.2 pydantic-core==2.9.0

# Or install Rust manually and compile
pkg install rust
export PATH="$HOME/.cargo/bin:$PATH"
pip install pydantic

# Then install FastAPI
pip install fastapi
```

## Without Pydantic

The system can run without pydantic/FastAPI:

- **LLM backends** work fine (use httpx for HTTP)
- **Core services** (DTN, discovery, mesh) don't need FastAPI
- **Database** (aiosqlite) works independently

FastAPI is only needed for:
- REST API endpoints
- OpenAPI documentation
- Request validation

## Compatibility Notes

### Python Version
- **Use Python 3.11**: Best compatibility with Rust toolchain
- **Avoid Python 3.12**: Known issues with Maturin/tokenizers

### Package Managers
- **Termux**: `pkg install rust` (uses Termux's package repository)
- **Desktop Linux**: `rustup` (installs via rustup.rs)

### Architecture Support
- **ARM64 (aarch64)**: Full support, binary wheels available
- **ARM32 (armv7l)**: Limited support, may need compilation
- **x86_64 (emulator)**: Full support

## References

- [PyPI pydantic releases](https://pypi.org/project/pydantic/#history)
- [PyPI pydantic-core releases](https://pypi.org/project/pydantic-core/#history)
- [Termux Rust package](https://github.com/termux/termux-packages/tree/master/packages/rust)

## Related Scripts

- `scripts/find_working_pydantic.py` - Find versions with ARM wheels
- `scripts/check_termux_compatibility.py` - Check all requirements
- `scripts/find_termux_wheels.py` - Check PyPI for binary wheels
- `scripts/check_rust_termux.sh` - Verify Rust installation
