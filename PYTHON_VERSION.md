# Python Version Requirements

## Required Version: Python 3.11

This project **requires Python 3.11**. Python 3.12 is **not supported** due to dependency issues.

## Why Not Python 3.12?

The `anthropic` package (used for LLM agent features) depends on `tokenizers`, which requires Rust and maturin to build from source on Python 3.12. The Rust installation process fails on Python 3.12 with the error:

```
Rust not found, installing from a temporary directory
Unsupported platform: Python 3.12
```

Even with `--only-binary` flags, pip may attempt to build from source if binary wheels are unavailable for your platform.

## Automatic Setup (Recommended)

**Just run `./setup.sh` and it will handle everything!**

The setup script will automatically:
1. Detect if you have Python 3.12 or another incompatible version
2. Install Python 3.11 for you (via brew on Mac, apt/dnf on Linux)
3. Remove any existing venv created with the wrong Python version
4. Create a new venv with Python 3.11
5. Install all dependencies with binary wheels only (no Rust compilation)

**You don't need to do anything manually - just run:**

```bash
./setup.sh
```

## Manual Installation (If Automatic Fails)

### macOS

```bash
# Install Python 3.11
brew install python@3.11

# Run setup (it will handle the rest)
./setup.sh
```

### Linux (Debian/Ubuntu)

```bash
# Install Python 3.11
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Run setup (it will handle the rest)
./setup.sh
```

### Linux (Fedora/RHEL)

```bash
# Install Python 3.11
sudo dnf install python3.11

# Run setup (it will handle the rest)
./setup.sh
```

### Android/Termux

Termux handles this automatically - just run `./setup.sh`

## What the Setup Script Does

The `setup.sh` script intelligently handles Python versions:

1. **Searches for Python 3.11** - Tries `python3.11` first, then checks `python3` version
2. **Auto-installs if needed** - If you have Python 3.12, it installs Python 3.11 alongside it
3. **Cleans up old venvs** - Removes any venv created with the wrong Python version
4. **Creates fresh venv** - Uses Python 3.11 to create the virtual environment
5. **Binary-only install** - Forces `--only-binary` for problematic packages to avoid Rust builds

## Version Files

- `.python-version` - Specifies Python 3.11 for pyenv and other version managers
- `setup.sh` - Validates Python version before setup
- `fix_tokenizers.sh` - Checks Python version and provides guidance

## Workarounds (Not Recommended)

If you absolutely cannot use Python 3.11:

1. **Install Rust manually** (complex, platform-dependent)
2. **Remove anthropic from requirements** (disables LLM agent features)
3. **Use older tokenizers version** (may have compatibility issues)

**Recommended:** Just use Python 3.11 - it's the simplest and most reliable solution.
