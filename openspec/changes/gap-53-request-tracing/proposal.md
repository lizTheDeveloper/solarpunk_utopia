# GAP-53: Request Tracing

**Status:** ✅ Implemented
**Priority:** P3 - Operations
**Effort:** 4-6 hours
**Completed:** 2025-12-20 (implemented together with GAP-50)

## Problem

No correlation IDs. Can't trace requests across services/logs.

## Solution

Add correlation ID middleware:

```python
import uuid

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Use incoming ID or generate new one
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    # Attach to request state
    request.state.correlation_id = correlation_id

    # Add to structlog context
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    # Process request
    response = await call_next(request)

    # Add to response headers
    response.headers["X-Correlation-ID"] = correlation_id

    return response
```

All logs automatically include correlation_id:
```json
{"event": "proposal_created", "correlation_id": "abc-123", ...}
```

## Tasks

1. ✅ Add correlation ID middleware
2. ✅ Integrate with structlog
3. ✅ Forward ID to downstream services
4. ✅ Add to error responses

## Success Criteria

- [x] All requests have correlation ID
- [x] ID appears in all logs
- [x] ID forwarded to VF service (via X-Correlation-ID header)
- [x] ID in error responses

## Implementation Summary

Implemented as part of GAP-50 (Logging System).

**Files Created:**
- `app/middleware/correlation_id.py` - CorrelationIdMiddleware class
- `valueflows_node/app/middleware/correlation_id.py` - Same for ValueFlows node

**Files Modified:**
- `app/main.py` - Added CorrelationIdMiddleware after CORS
- `valueflows_node/app/main.py` - Added CorrelationIdMiddleware

**Features:**
- Extracts X-Correlation-ID from request headers or generates UUID
- Stores correlation ID in request.state for handler access
- Binds to structlog context variables (auto-included in all logs)
- Adds X-Correlation-ID to response headers
- Logs HTTP requests with correlation ID, duration, status code
- Error handling includes correlation ID in error logs
- Helper function `get_correlation_id(request)` for manual access
