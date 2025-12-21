# GAP-50: Logging System

**Status:** ✅ Implemented
**Priority:** P2 - Operations
**Effort:** 3-4 hours
**Completed:** 2025-12-20

## Problem

No structured logging. Debugging requires print statements.

## Solution

Add structlog:

```python
import structlog

logger = structlog.get_logger()

# Structured logging
logger.info("proposal_approved",
    proposal_id=proposal_id,
    user_id=user_id,
    agent_type=agent.type
)

# Outputs JSON for easy parsing:
# {"event": "proposal_approved", "proposal_id": "xxx", "user_id": "yyy", ...}
```

Configure levels:

```python
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))
    )
)
```

## Tasks

1. ✅ Add structlog dependency
2. ✅ Configure in app startup
3. ✅ Replace print statements with logger
4. ✅ Add request correlation IDs (ties to GAP-53)

## Success Criteria

- [x] Structured JSON logs
- [x] Configurable log level
- [x] No print statements in production code

## Implementation Summary

**Files Created:**
- `app/logging_config.py` - Structured logging configuration with JSON/dev modes
- `valueflows_node/app/logging_config.py` - Logging config for ValueFlows node
- `app/middleware/correlation_id.py` - Correlation ID middleware (implemented GAP-53)
- `valueflows_node/app/middleware/correlation_id.py` - Correlation ID for VF node
- `valueflows_node/app/middleware/__init__.py` - Middleware module

**Files Modified:**
- `requirements.txt` - Added structlog==24.1.0 and pydantic-settings==2.1.0
- `app/config.py` - Added `json_logs` setting
- `valueflows_node/app/config.py` - Added `json_logs` setting
- `app/main.py` - Configured structlog, added CorrelationIdMiddleware
- `valueflows_node/app/main.py` - Configured structlog, added CorrelationIdMiddleware
- `.env.example` - Added JSON_LOGS configuration option

**Features:**
- Structured logging with automatic correlation ID inclusion
- JSON logs for production, colored console logs for development
- Automatic HTTP request logging with duration tracking
- Service event logging helpers
- Context variables for correlation IDs
- ISO timestamps
- Configurable log levels via environment
- Service name tagging (dtn-bundle-system, valueflows-node)
