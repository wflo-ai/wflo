"""Structured logging configuration using structlog with OpenTelemetry integration."""

import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace


def configure_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog with OpenTelemetry integration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON logs (for production)

    Example:
        # Development mode (colored output)
        configure_logging("INFO", json_output=False)

        # Production mode (JSON output)
        configure_logging("INFO", json_output=True)
    """
    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Silence noisy loggers
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    # Build processor chain
    shared_processors = [
        # Merge in context from contextvars
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Add trace context processor (before rendering)
    trace_processors = [
        add_trace_context,
    ]

    # Choose renderer based on environment
    if json_output:
        # Production: JSON logs for structured log aggregation
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: Colored console output with nice formatting
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.better_traceback,
        )

    # Stack processors
    processors = [
        # First, add all shared processors
        *shared_processors,
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions nicely
        structlog.processors.format_exc_info,
        # Add trace context
        *trace_processors,
        # Finally, render the output
        renderer,
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_trace_context(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add OpenTelemetry trace context to log events.

    This processor adds trace_id and span_id from the current OpenTelemetry
    span to every log event, enabling correlation between logs and traces.

    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Dictionary containing log event data

    Returns:
        Updated event dict with trace context
    """
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            # Format as hex strings for consistency with tracing UIs
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
            event_dict["trace_flags"] = format(ctx.trace_flags, "02x")
    return event_dict


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with context binding support.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        BoundLogger that supports context binding and structured logging

    Example:
        >>> from wflo.observability.logging import get_logger
        >>> logger = get_logger(__name__)
        >>>
        >>> # Simple logging
        >>> logger.info("workflow started")
        >>>
        >>> # Structured logging with fields
        >>> logger.info("workflow completed",
        ...             workflow_id="abc-123",
        ...             duration=45.2,
        ...             cost_usd=0.05)
        >>>
        >>> # Context binding for all subsequent logs
        >>> workflow_logger = logger.bind(workflow_id="abc-123")
        >>> workflow_logger.info("step 1 started")  # workflow_id auto-included
        >>> workflow_logger.info("step 2 started")  # workflow_id auto-included
    """
    return structlog.get_logger(name)
