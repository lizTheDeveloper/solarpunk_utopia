"""
Structured Logging Configuration for ValueFlows Node

Sets up structlog for JSON-based structured logging with correlation IDs,
log levels, and proper formatting for both development and production.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger


def add_app_context(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events"""
    event_dict["service"] = "valueflows-node"
    return event_dict


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """
    Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON logs. If False, use human-readable format.
    """
    # Convert log level string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Disable uvicorn's default access logs (we'll log them ourselves)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Common processors for all configurations
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # Merge context variables (correlation IDs, etc.)
        structlog.stdlib.add_log_level,  # Add log level
        structlog.stdlib.add_logger_name,  # Add logger name
        add_app_context,  # Add service name
        structlog.processors.TimeStamper(fmt="iso"),  # Add ISO timestamp
        structlog.processors.StackInfoRenderer(),  # Render stack info if present
    ]

    if json_logs:
        # Production: JSON logs for parsing by log aggregators
        processors = shared_processors + [
            structlog.processors.format_exc_info,  # Format exceptions as string
            structlog.processors.JSONRenderer(),  # Render as JSON
        ]
    else:
        # Development: Human-readable colored output
        processors = shared_processors + [
            structlog.processors.ExceptionRenderer(),  # Pretty-print exceptions
            structlog.dev.ConsoleRenderer(colors=True),  # Colored console output
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Convenience function for request logging
def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra: Any
) -> None:
    """
    Log an HTTP request with standard fields.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **extra: Additional fields to log
    """
    logger = get_logger("http")

    log_data = {
        "event": "http_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        **extra
    }

    if status_code >= 500:
        logger.error(**log_data)
    elif status_code >= 400:
        logger.warning(**log_data)
    else:
        logger.info(**log_data)


# Convenience function for service logging
def log_service_event(
    event_type: str,
    message: str,
    level: str = "info",
    **extra: Any
) -> None:
    """
    Log a service event with standard fields.

    Args:
        event_type: Type of event (e.g., "exchange_completed", "match_created")
        message: Human-readable message
        level: Log level (info, warning, error, debug)
        **extra: Additional fields to log
    """
    logger = get_logger("service")

    log_data = {
        "event": event_type,
        "message": message,
        **extra
    }

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(**log_data)
