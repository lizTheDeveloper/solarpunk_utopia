# GAP-70: LLM Integration Uses Mock by Default

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Production Using Mock Data
**Source**: VISION_REALITY_DELTA.md Gap #70

## Problem Statement

The LLM client selection logic falls back to `MockBackend` by default when the backend type is unknown or misconfigured. This means agents that should use real AI (Ollama, MLX, or remote APIs) instead return useless mock responses like `"Mock response to: [prompt]"`. The system appears to have AI capabilities but doesn't actually use them.

**Impact**:
- Agents appear to work but generate nonsense mock responses
- Demo blocker - AI reasoning is completely fake
- Users waste time configuring "AI" that isn't actually running
- No error surfaced to users - silent degradation
- LLM-dependent features (matchmaking reasoning, scheduling optimization) are non-functional

**Evidence**:
```python
# app/llm/backends.py:446-453
def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    backend = config.backend if config else "mock"

    if backend == "ollama":
        return OllamaBackend(config)
    elif backend == "mlx":
        return MLXBackend(config)
    elif backend == "remote":
        return RemoteBackend(config)
    else:
        logger.warning(
            f"Unknown backend '{backend}', falling back to mock. "
            "Set LLM_BACKEND environment variable to 'ollama', 'mlx', or 'remote'."
        )
        return MockBackend(config)  # Silent fallback!
```

## Requirements

### MUST

- LLM backend selection MUST fail fast if misconfigured (not silently fall back)
- Configuration errors MUST be surfaced to users with clear error messages
- Mock backend MUST only be used when explicitly configured or in test environments
- LLM availability MUST be checkable before agent execution
- Agents MUST be able to detect if LLM is available and fail gracefully if required

### SHOULD

- LLM configuration SHOULD be validated on startup
- Missing dependencies (ollama, transformers) SHOULD show helpful setup instructions
- LLM health checks SHOULD run periodically
- Agent execution SHOULD show which LLM backend is being used
- Configuration guide SHOULD be provided in docs

### MAY

- LLM responses MAY be cached for identical prompts
- Multiple LLM backends MAY be configured with fallback order
- LLM usage MAY be tracked for billing/monitoring

## Root Cause Analysis

The current logic assumes:
1. If no backend is configured → use mock
2. If unknown backend → warn but use mock anyway

This is wrong for production. Better approach:
1. **Require explicit configuration** - no default
2. **Fail loudly** if misconfigured
3. **Only use mock in tests** - never in production

## Proposed Solution

### 1. Update LLM Client Factory

```python
# app/llm/backends.py
class LLMConfigError(Exception):
    """Raised when LLM is misconfigured"""
    pass

def get_llm_client(config: Optional[LLMConfig] = None, allow_mock: bool = False) -> LLMClient:
    """Get LLM client with strict configuration

    Args:
        config: LLM configuration (reads from env if None)
        allow_mock: If True, allows MockBackend (for testing only)

    Returns:
        Configured LLM client

    Raises:
        LLMConfigError: If configuration is invalid or backend unavailable
    """

    # Load config from environment if not provided
    if not config:
        backend_type = os.getenv("LLM_BACKEND")
        if not backend_type:
            if allow_mock:
                logger.warning("No LLM_BACKEND configured, using mock (testing only)")
                return MockBackend(None)
            else:
                raise LLMConfigError(
                    "LLM_BACKEND environment variable not set. "
                    "Set to 'ollama', 'mlx', or 'remote'. "
                    "See docs/llm-setup.md for configuration guide."
                )

        config = LLMConfig(
            backend=backend_type,
            model=os.getenv("LLM_MODEL", "llama2"),
            api_url=os.getenv("LLM_API_URL"),
            api_key=os.getenv("LLM_API_KEY")
        )

    backend = config.backend

    # Create appropriate backend
    if backend == "ollama":
        client = OllamaBackend(config)
    elif backend == "mlx":
        client = MLXBackend(config)
    elif backend == "remote":
        client = RemoteBackend(config)
    elif backend == "mock":
        if not allow_mock:
            raise LLMConfigError(
                "MockBackend not allowed in production. "
                "Configure a real LLM backend."
            )
        client = MockBackend(config)
    else:
        raise LLMConfigError(
            f"Unknown LLM backend: '{backend}'. "
            f"Valid options: ollama, mlx, remote"
        )

    # Verify backend is actually available
    try:
        if not client.is_available():
            raise LLMConfigError(
                f"{backend} backend not available. "
                f"Check configuration and service status."
            )
    except Exception as e:
        raise LLMConfigError(
            f"Failed to connect to {backend} backend: {e}"
        ) from e

    logger.info(f"LLM client initialized: {backend} ({config.model})")
    return client


def validate_llm_config() -> dict:
    """Validate LLM configuration on startup

    Returns:
        Dict with status and any errors

    Raises:
        LLMConfigError: If configuration is critically broken
    """
    try:
        client = get_llm_client(allow_mock=False)
        return {
            "status": "ok",
            "backend": client.backend_type,
            "model": client.config.model if client.config else None,
            "available": client.is_available()
        }
    except LLMConfigError as e:
        return {
            "status": "error",
            "error": str(e),
            "backend": None
        }
```

### 2. Add Health Check to Each Backend

```python
# app/llm/backends.py
class OllamaBackend(LLMClient):
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(
                f"{self.config.api_url or 'http://localhost:11434'}/api/tags",
                timeout=2
            )
            if response.status_code != 200:
                return False

            # Check if our model is downloaded
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            return self.config.model in model_names

        except requests.RequestException:
            return False

class MLXBackend(LLMClient):
    def is_available(self) -> bool:
        """Check if MLX is installed and model is available"""
        try:
            import mlx
            import mlx.core as mx
            # Check if we can actually use MLX
            test_array = mx.array([1, 2, 3])
            return True
        except ImportError:
            return False
        except Exception:
            return False

class RemoteBackend(LLMClient):
    def is_available(self) -> bool:
        """Check if remote API is reachable"""
        try:
            response = requests.get(
                f"{self.config.api_url}/health",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
```

### 3. Update Agent Execution to Check LLM

```python
# app/agents/framework/base_agent.py
class BaseAgent:
    async def execute(self, context: dict) -> dict:
        """Execute agent with LLM availability check"""

        # Check if this agent requires LLM
        if self.requires_llm():
            try:
                llm_client = get_llm_client(allow_mock=False)
                context["llm_client"] = llm_client
            except LLMConfigError as e:
                error_msg = f"{self.agent_name} requires LLM but it's not available: {e}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "error_type": "llm_unavailable"
                }

        return await self._execute_internal(context)

    def requires_llm(self) -> bool:
        """Override in subclasses that need LLM"""
        return False  # Most agents don't need LLM


# Example agent that uses LLM
class PermaculturePlannerAgent(BaseAgent):
    def requires_llm(self) -> bool:
        return True  # This agent needs AI reasoning

    async def _execute_internal(self, context: dict) -> dict:
        llm = context["llm_client"]  # Safe to access now

        prompt = self._build_planning_prompt(context)
        response = await llm.generate(prompt)
        return self._parse_plan(response)
```

### 4. Add Startup Validation

```python
# app/main.py
from app.llm.backends import validate_llm_config

@app.on_event("startup")
async def startup_validation():
    """Validate configuration on startup"""

    # Validate LLM if any agents require it
    llm_status = validate_llm_config()
    if llm_status["status"] == "error":
        logger.error(f"LLM validation failed: {llm_status['error']}")
        logger.warning(
            "AI agents will be unavailable. "
            "Set LLM_BACKEND environment variable to enable. "
            "See docs/llm-setup.md"
        )
    else:
        logger.info(
            f"LLM configured: {llm_status['backend']} "
            f"(model: {llm_status['model']})"
        )
```

### 5. Add Configuration Guide

```markdown
# docs/llm-setup.md

## LLM Configuration

The Solarpunk mesh network supports multiple LLM backends for AI agent reasoning.

### Option 1: Ollama (Local, Recommended)

1. Install Ollama: https://ollama.ai
2. Download a model:
   ```bash
   ollama pull llama2
   ```
3. Set environment variables:
   ```bash
   export LLM_BACKEND=ollama
   export LLM_MODEL=llama2
   export LLM_API_URL=http://localhost:11434  # Optional, defaults to this
   ```

### Option 2: MLX (Mac M1/M2 Only)

1. Install MLX:
   ```bash
   pip install mlx mlx-transformers
   ```
2. Set environment variables:
   ```bash
   export LLM_BACKEND=mlx
   export LLM_MODEL=llama2-7b
   ```

### Option 3: Remote API (Anthropic, OpenAI, etc.)

```bash
export LLM_BACKEND=remote
export LLM_API_URL=https://api.anthropic.com/v1
export LLM_API_KEY=your-api-key
export LLM_MODEL=claude-3-sonnet-20240229
```

### Testing Configuration

```bash
python -c "from app.llm.backends import validate_llm_config; print(validate_llm_config())"
```

Should output:
```json
{
  "status": "ok",
  "backend": "ollama",
  "model": "llama2",
  "available": true
}
```
```

## Test Scenarios

### WHEN LLM_BACKEND is not configured
THEN startup MUST log a warning about AI agents being unavailable
AND agents requiring LLM MUST fail with clear error messages
AND the system MUST continue to work for non-LLM features

### WHEN LLM_BACKEND is set to invalid value
THEN `get_llm_client()` MUST raise LLMConfigError
AND the error message MUST list valid backend options

### WHEN Ollama backend is configured but service is not running
THEN `is_available()` MUST return False
AND agents requiring LLM MUST fail with clear error about Ollama not running

### WHEN a test explicitly requests MockBackend
THEN MockBackend MUST be allowed
AND responses MUST be clearly marked as mock

### WHEN production code tries to use MockBackend
THEN LLMConfigError MUST be raised
AND the error MUST explain that mock is not allowed in production

## Implementation Steps

1. Add `LLMConfigError` exception class
2. Update `get_llm_client()` with strict validation
3. Add `is_available()` method to all backends
4. Add `requires_llm()` to BaseAgent
5. Update agent execution to check LLM availability
6. Add startup validation in main.py
7. Create docs/llm-setup.md
8. Update .env.example with LLM variables
9. Add tests for all error cases

## Files to Modify

- `app/llm/backends.py` - Add strict validation
- `app/agents/framework/base_agent.py` - Check LLM before execution
- `app/main.py` - Add startup validation
- `docs/llm-setup.md` - New configuration guide
- `.env.example` - Add LLM variables
- `tests/test_llm_config.py` - Comprehensive tests

## Environment Variables

```bash
# Required (choose one)
LLM_BACKEND=ollama|mlx|remote|mock

# Backend-specific
LLM_MODEL=llama2  # Model name
LLM_API_URL=http://localhost:11434  # For ollama/remote
LLM_API_KEY=sk-...  # For remote APIs
```

## Related Gaps

- GAP-77: Permaculture planner (needs real LLM)
- All agent gaps that have TODO comments about LLM
- Agent reasoning quality depends on LLM being configured

## Migration Path

1. Add validation code (backward compatible - still works with mock)
2. Update .env.example with LLM config
3. Send announcement: "LLM configuration required for AI features"
4. After grace period: remove `allow_mock=True` from production code
