# LLM Backend Guide

## Overview

This project supports multiple LLM backends without requiring the `anthropic` package or any Rust/tokenizers dependencies. All remote API backends use simple HTTP requests via `httpx`.

## Available Backends

### 1. Anthropic (Claude)

**No SDK required** - Direct HTTP API implementation.

```bash
# Environment variables
export LLM_BACKEND=anthropic
export LLM_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=sk-ant-...

# Or use .env file
LLM_BACKEND=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

**Supported Models:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

**How it works:**
- Uses Anthropic Messages API directly
- Makes HTTP POST to `https://api.anthropic.com/v1/messages`
- No `anthropic` package needed
- No `tokenizers` package needed
- No Rust compilation required

### 2. OpenAI / OpenAI-Compatible

```bash
export LLM_BACKEND=remote
export LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-...
```

**Compatible APIs:**
- OpenAI (gpt-4, gpt-3.5-turbo, etc.)
- Azure OpenAI
- LocalAI
- Any OpenAI-compatible endpoint

### 3. HuggingFace Inference API

```bash
export LLM_BACKEND=huggingface
export LLM_MODEL=Qwen/Qwen2.5-72B-Instruct
export HF_TOKEN=hf_...
```

**Features:**
- Uses HuggingFace Router (OpenAI-compatible endpoint)
- Free tier available
- Many open-source models

### 4. Ollama (Local)

```bash
export LLM_BACKEND=ollama
export LLM_MODEL=qwen2.5:1.5b
export LLM_API_BASE=http://localhost:11434
```

**Best for:**
- Raspberry Pi
- Local development
- Offline usage

### 5. MLX (Apple Silicon)

```bash
export LLM_BACKEND=mlx
export LLM_MODEL=mlx-community/Qwen2.5-3B-Instruct
```

**Requirements:**
- Apple Silicon Mac
- `pip install mlx mlx-lm`

## Usage Examples

### Python Code

```python
from app.llm.backends import get_llm_client
from app.llm.config import LLMConfig

# Using environment variables
client = get_llm_client()
response = await client.generate("What is the capital of France?")
print(response.content)

# Using explicit config
config = LLMConfig(
    backend="anthropic",
    model="claude-3-5-sonnet-20241022",
    api_key="sk-ant-...",
)
client = get_llm_client(config)
response = await client.generate(
    prompt="Explain quantum computing",
    system_prompt="You are a physics teacher",
    temperature=0.7,
    max_tokens=500,
)
```

### Multi-turn Chat

```python
from app.llm.client import LLMMessage

messages = [
    LLMMessage(role="system", content="You are a helpful assistant"),
    LLMMessage(role="user", content="Hello!"),
    LLMMessage(role="assistant", content="Hi! How can I help?"),
    LLMMessage(role="user", content="Tell me a joke"),
]

response = await client.chat(messages)
print(response.content)
```

### Health Check

```python
is_healthy = await client.health_check()
if is_healthy:
    print(f"Backend {config.backend} is available")
else:
    print(f"Backend {config.backend} is not reachable")
```

## Why No `anthropic` Package?

The official `anthropic` Python package depends on `tokenizers`, which requires:
- Rust compiler
- `maturin` build tool
- 500+ MB of build dependencies

This causes problems on:
- Android/Termux (no Rust support)
- Python 3.12 (maturin compatibility issues)
- Embedded systems (limited resources)
- CI/CD pipelines (slow builds)

**Our solution:**
- Implement Anthropic Messages API directly using `httpx`
- Only dependency: `httpx` (pure Python, no compilation)
- Works everywhere Python works
- Same functionality, zero build overhead

## Termux/Android Support

**All backends work on Termux**, including Anthropic/Claude:

```bash
# Install
pkg install python git
git clone https://github.com/lizTheDeveloper/solarpunk_utopia.git
cd solarpunk_utopia
./setup.sh

# Configure
export LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Use
python -c "
from app.llm.backends import get_llm_client
import asyncio

async def main():
    client = get_llm_client()
    response = await client.generate('Hello from Android!')
    print(response.content)

asyncio.run(main())
"
```

## Performance & Caching

All backends include:
- Response caching (avoids duplicate API calls)
- Configurable timeouts
- Automatic retry logic
- Token usage tracking

## Switching Backends

Change backends by updating environment variables:

```bash
# Start with free HuggingFace
export LLM_BACKEND=huggingface
export HF_TOKEN=hf_...

# Switch to local Ollama
export LLM_BACKEND=ollama

# Switch to Claude for production
export LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

No code changes needed - the factory pattern handles everything.

## Troubleshooting

### API Key Issues

```bash
# Check your API key is set
echo $ANTHROPIC_API_KEY

# Test connection
python -c "
from app.llm.backends import get_llm_client
import asyncio

async def main():
    client = get_llm_client()
    healthy = await client.health_check()
    print(f'API reachable: {healthy}')

asyncio.run(main())
"
```

### Timeout Issues

```bash
# Increase timeout (default: 60 seconds)
export LLM_TIMEOUT_SECONDS=120
```

### Rate Limiting

Most APIs have rate limits. Check your plan:
- Anthropic: https://console.anthropic.com
- OpenAI: https://platform.openai.com/usage
- HuggingFace: https://huggingface.co/settings/tokens

## Cost Comparison

| Backend | Cost | Speed | Quality | Offline |
|---------|------|-------|---------|---------|
| Anthropic | $$$ | Fast | Excellent | No |
| OpenAI | $$$ | Fast | Excellent | No |
| HuggingFace | $ | Medium | Good | No |
| Ollama | Free | Fast* | Good | Yes |
| MLX | Free | Fast* | Good | Yes |

*Speed depends on hardware

## Development vs Production

**Development:**
```bash
export LLM_BACKEND=ollama  # Free, fast, good enough
```

**Production:**
```bash
export LLM_BACKEND=anthropic  # Best quality
export LLM_MODEL=claude-3-5-sonnet-20241022
```

**Testing:**
```python
# Use MockBackend for tests
client = get_llm_client(allow_mock=True)
```

## Further Reading

- [Anthropic API Docs](https://docs.anthropic.com/en/api/messages)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- [HuggingFace Inference](https://huggingface.co/docs/api-inference/index)
- [Ollama Docs](https://github.com/ollama/ollama)
