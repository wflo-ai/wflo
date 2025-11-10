"""OpenTelemetry tracing configuration for distributed tracing."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracing(
    service_name: str = "wflo",
    service_version: str = "0.1.0",
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> None:
    """Configure OpenTelemetry tracing with auto-instrumentation.

    Args:
        service_name: Name of the service for trace identification
        service_version: Version of the service
        otlp_endpoint: OTLP gRPC endpoint (e.g., "localhost:4317")
                      If None, traces are not exported (unless console_export=True)
        console_export: If True, print traces to console (for development)

    Example:
        # Production setup with OTLP exporter
        configure_tracing(
            service_name="wflo",
            service_version="0.1.0",
            otlp_endpoint="localhost:4317",
        )

        # Development setup with console output
        configure_tracing(console_export=True)
    """
    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processors based on configuration
    if otlp_endpoint:
        # Export to OTLP endpoint (Jaeger, Grafana Tempo, etc.)
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,  # TODO: Use TLS in production
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

    if console_export:
        # Print traces to console for development
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument SQLAlchemy (tracks all database queries)
    SQLAlchemyInstrumentor().instrument()

    # Auto-instrument aiohttp client (tracks all HTTP requests)
    AioHttpClientInstrumentor().instrument()


def get_tracer(name: str | None = None) -> trace.Tracer:
    """Get an OpenTelemetry tracer for creating spans.

    Args:
        name: Tracer name, typically __name__ of the calling module

    Returns:
        Tracer for creating manual spans

    Example:
        >>> from wflo.observability.tracing import get_tracer
        >>> tracer = get_tracer(__name__)
        >>>
        >>> # Create a span for a code block
        >>> with tracer.start_as_current_span("operation_name") as span:
        ...     span.set_attribute("key", "value")
        ...     # Do some work
        ...     result = expensive_operation()
        ...     span.set_attribute("result_size", len(result))
    """
    return trace.get_tracer(name or "wflo")
