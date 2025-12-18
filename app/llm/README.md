# LLM Integration Layer

Pluggable LLM backend system for running AI agents with different inference providers.

## Features

- **Pluggable Backends**: Easily switch between Ollama, MLX, Remote APIs, or Mock
- **Environment-Based Config**: Configure via environment variables
- **Built-in Caching**: Reduce redundant LLM calls
- **Async/Await**: Non-blocking LLM operations
- **Type-Safe**: Full type hints with dataclasses

## Supported Backends

### 1. Ollama (Cross-Platform)

Local inference for Raspberry Pi, Linux, Mac.

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull a small model
ollama pull qwen2.5:1.5b
```

**Configuration:**
```bash
export LLM_BACKEND=ollama
export LLM_MODEL=qwen2.5:1.5b
```

**Recommended models:**
- `qwen2.5:1.5b` - Fast, lightweight (1.5B params)
- `llama3.2:1b` - Efficient (1B params)
- `phi3:mini` - Good balance (3.8B params)

### 2. MLX (Apple Silicon Only)

Optimized for M1/M2/M3 Macs using Apple's MLX framework.

**Setup:**
```bash
pip install mlx mlx-lm
```

**Configuration:**
```bash
export LLM_BACKEND=mlx
export LLM_MODEL=mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

### 3. Remote API (OpenAI, Anthropic, etc.)

Use cloud APIs for development or fallback.

**Configuration:**
```bash
export LLM_BACKEND=remote
export LLM_MODEL=gpt-4  # or claude-3-opus, etc.
export LLM_API_KEY=your-api-key-here
```

### 4. Mock (Testing)

Returns canned responses without calling any LLM.

**Configuration:**
```bash
export LLM_BACKEND=mock
```

## Usage

### Basic Example

```python
from app.llm import get_llm_client, LLMConfig

# Use environment config
client = get_llm_client()

# Or explicit config
config = LLMConfig(
    backend="ollama",
    model="qwen2.5:1.5b",
    temperature=0.7,
    max_tokens=512,
)
client = get_llm_client(config)

# Generate text
response = await client.generate(
    prompt="What are the benefits of gift economies?",
    system_prompt="You are a solarpunk AI assistant.",
)

print(response.content)
print(f"Tokens used: {response.tokens_used}")
print(f"Cached: {response.cached}")
```

### Using with Agents

Agents automatically receive the LLM client via the scheduler:

```python
from app.services import AgentScheduler

# Scheduler creates all agents with LLM client
scheduler = AgentScheduler()

# Or provide custom config
from app.llm import LLMConfig
config = LLMConfig(backend="ollama", model="qwen2.5:1.5b")
scheduler = AgentScheduler(llm_config=config)

# Run agents once
await scheduler.run_once()

# Or start background scheduling
await scheduler.start()
```

Within an agent:

```python
class MyAgent(BaseAgent):
    async def analyze(self) -> List[Proposal]:
        # Use LLM for reasoning
        response = await self.use_llm(
            prompt="Should we match these resources?",
            context={"offer": "10kg tomatoes", "need": "vegetables"},
        )

        # Parse response and create proposals
        ...
```

## Environment Variables

All configuration can be done via environment variables:

```bash
# Backend selection
LLM_BACKEND=ollama          # ollama, mlx, remote, mock

# Model selection
LLM_MODEL=qwen2.5:1.5b      # Model name/ID

# API settings (for remote backend)
LLM_API_KEY=your-key
LLM_API_BASE=https://api.openai.com/v1

# Generation parameters
LLM_TEMPERATURE=0.7         # Sampling temperature (0.0-1.0)
LLM_MAX_TOKENS=512          # Max tokens to generate
LLM_TOP_P=0.9              # Nucleus sampling threshold

# Performance
LLM_TIMEOUT=30              # Request timeout in seconds
LLM_ENABLE_CACHE=true       # Enable response caching
LLM_CACHE_DIR=.llm_cache    # Cache directory
```

## Architecture

```
app/llm/
├── __init__.py           # Public exports
├── config.py             # LLMConfig dataclass
├── client.py             # LLMClient abstract base
├── backends.py           # Backend implementations
└── README.md            # This file
```

### Key Classes

**LLMConfig**: Configuration dataclass
- Loaded from environment or explicit values
- Controls backend selection, model, parameters

**LLMClient**: Abstract base class
- `generate()` - Single prompt generation
- `chat()` - Multi-turn conversation
- `health_check()` - Test if backend is available

**Backend Implementations**:
- `OllamaBackend` - Local inference via Ollama
- `MLXBackend` - Apple Silicon optimized
- `RemoteBackend` - Cloud APIs (OpenAI, Anthropic)
- `MockBackend` - Testing without real LLM

**Factory**: `get_llm_client(config)`
- Returns appropriate backend based on config
- Falls back to MockBackend if backend unknown

## Testing

Run the integration test:

```bash
python test_llm_integration.py
```

This tests:
1. MockBackend (always works)
2. OllamaBackend (if Ollama running)
3. Agent LLM usage
4. Scheduler with LLM

## Performance Tips

### For Raspberry Pi

Use Ollama with small models:
```bash
export LLM_BACKEND=ollama
export LLM_MODEL=qwen2.5:1.5b  # or llama3.2:1b
export LLM_MAX_TOKENS=256      # Limit generation length
```

### For Mac (Apple Silicon)

Use MLX for best performance:
```bash
export LLM_BACKEND=mlx
export LLM_MODEL=mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

### For Development

Use Mock backend for fast testing:
```bash
export LLM_BACKEND=mock
```

Or use Remote API with fast models:
```bash
export LLM_BACKEND=remote
export LLM_MODEL=gpt-3.5-turbo
```

## Caching

The LLM client includes built-in caching to avoid redundant calls:

- Cache key: `f"{prompt}::{system_prompt}"`
- Cached responses marked with `cached=True`
- Disable with `LLM_ENABLE_CACHE=false`

Example:
```python
# First call - makes LLM request
response1 = await client.generate(prompt="Hello")
assert response1.cached == False

# Second call - returns cached
response2 = await client.generate(prompt="Hello")
assert response2.cached == True
```

## Error Handling

All backends handle errors gracefully:

```python
try:
    response = await client.generate(prompt="...")
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    # Fall back to rule-based logic
```

Health checks return `False` instead of raising:

```python
if not await client.health_check():
    logger.warning("LLM backend not available")
    # Use mock backend or skip LLM features
```

## Future Enhancements

- [ ] Streaming responses for long generations
- [ ] Token usage tracking and budgets
- [ ] Multiple LLM backends in same system
- [ ] Fine-tuning support for custom models
- [ ] Prompt template system
- [ ] RAG (retrieval-augmented generation)
