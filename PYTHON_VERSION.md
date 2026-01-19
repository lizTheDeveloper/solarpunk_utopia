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

## Installation

### macOS

```bash
# Install Python 3.11
brew install python@3.11

# Remove old venv if it exists
rm -rf venv

# Create venv with Python 3.11
python3.11 -m venv venv

# Activate and run setup
source venv/bin/activate
./setup.sh
```

### Linux (Debian/Ubuntu)

```bash
# Install Python 3.11
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Remove old venv if it exists
rm -rf venv

# Create venv with Python 3.11
python3.11 -m venv venv

# Activate and run setup
source venv/bin/activate
./setup.sh
```

### Linux (Fedora/RHEL)

```bash
# Install Python 3.11
sudo dnf install python3.11

# Remove old venv if it exists
rm -rf venv

# Create venv with Python 3.11
python3.11 -m venv venv

# Activate and run setup
source venv/bin/activate
./setup.sh
```

### Android/Termux

Termux handles this automatically - just run `./setup.sh`

## Automatic Detection

The `setup.sh` script will automatically:
1. Look for `python3.11` first
2. Check the version of `python3`
3. Display an error if Python 3.12 is detected
4. Provide installation instructions

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
