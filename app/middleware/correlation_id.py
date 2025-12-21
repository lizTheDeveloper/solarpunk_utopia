"""
Correlation ID Middleware

Adds correlation IDs to all requests for distributed tracing.
The correlation ID is:
1. Extracted from X-Correlation-ID header if present (for cross-service tracing)
2. Generated as a new UUID if not present
3. Added to the request state for access in handlers
4. Bound to structlog context for automatic inclusion in all logs
5. Added to the response headers for client-side tracing
"""

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import log_request


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests and logs"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add correlation ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in request state for access in handlers
        request.state.correlation_id = correlation_id

        # Bind to structlog context so all logs include it
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=correlation_id,  # Alias for backwards compatibility
        )

        # Record start time for duration tracking
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request
            log_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Log error with correlation ID
            duration_ms = (time.time() - start_time) * 1000

            logger = structlog.get_logger("http")
            logger.error(
                "request_failed",
                method=request.method,
                path=str(request.url.path),
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
            )

            # Re-raise the exception to be handled by FastAPI's exception handlers
            raise

        finally:
            # Clear context variables for this request
            structlog.contextvars.clear_contextvars()


def get_correlation_id(request: Request) -> str:
    """
    Get correlation ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    return getattr(request.state, "correlation_id", "unknown")
