# Phase 2: Observability Stack Implementation Plan

**Goal**: Implement production-grade observability with structlog, OpenTelemetry, and Prometheus

**Estimated Effort**: 14 hours
**Priority**: HIGH
**Status**: In Progress

---

## Overview

Implement comprehensive observability stack for Wflo:
1. **Structlog**: Structured logging with JSON output and trace correlation
2. **OpenTelemetry**: Distributed tracing for workflows and database operations
3. **Prometheus**: Metrics collection for monitoring and alerting

---

## Current State

**Dependencies Already Installed** ✅:
- `structlog ^24.1.0`
- `opentelemetry-api ^1.21.0`
- `opentelemetry-sdk ^1.21.0`
- `opentelemetry-instrumentation ^0.42b0`
- `opentelemetry-instrumentation-sqlalchemy ^0.42b0`
- `opentelemetry-instrumentation-aiohttp-client ^0.42b0`
- `prometheus-client ^0.19.0`

**Status**: Installed but not integrated

---

## Phase 2.1: Structlog Implementation (4 hours)

### Goals
- Replace `logging` with `structlog` throughout codebase
- Add trace correlation (trace_id, span_id)
- JSON output for production, colored for development
- Context processors for workflow metadata

### Implementation Steps

#### Step 1: Create Logging Configuration Module (30 min)

**File**: `src/wflo/observability/logging.py`

```python
"""Structured logging configuration using structlog."""

import logging
import sys

import structlog
from opentelemetry import trace


def configure_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog with OpenTelemetry integration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON logs (for production)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Processors for all logs
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Add trace context from OpenTelemetry
        add_trace_context,
    ]

    # Different renderers for dev vs prod
    if json_output:
        # Production: JSON logs
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Colored console output
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_trace_context(logger, method_name, event_dict):
    """Add OpenTelemetry trace context to log events."""
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
            event_dict["trace_flags"] = ctx.trace_flags
    return event_dict


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        BoundLogger with context support
    """
    return structlog.get_logger(name)
```

#### Step 2: Update Settings to Support Logging Config (15 min)

**File**: `src/wflo/config/settings.py`

Add:
```python
# Logging
log_json_output: bool = Field(
    default=False,
    description="Use JSON logging format (for production)",
)
```

#### Step 3: Initialize Logging in Application Startup (15 min)

**File**: `src/wflo/__init__.py` or create `src/wflo/app.py`

```python
from wflo.config import get_settings
from wflo.observability.logging import configure_logging

def initialize():
    """Initialize Wflo application."""
    settings = get_settings()

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        json_output=settings.log_json_output,
    )
```

#### Step 4: Replace logging imports (2 hours)

**Strategy**: Gradual migration

**Priority Files** (migrate first):
1. `src/wflo/cost/tracker.py`
2. `src/wflo/temporal/workflows.py`
3. `src/wflo/temporal/activities.py`
4. `src/wflo/sandbox/runtime.py`

**Pattern**:
```python
# Before
import logging
logger = logging.getLogger(__name__)
logger.info("Message", extra={"key": "value"})

# After
from wflo.observability.logging import get_logger
logger = get_logger(__name__)
logger.info("message", key="value")  # Direct kwargs, not extra=
```

#### Step 5: Add Workflow Context Binding (30 min)

**In workflows and activities**:
```python
from wflo.observability.logging import get_logger

logger = get_logger(__name__)

# Bind workflow context
workflow_logger = logger.bind(
    workflow_id=workflow_id,
    execution_id=execution_id,
)

workflow_logger.info("workflow_started")
# Outputs: {"event": "workflow_started", "workflow_id": "...", "execution_id": "..."}
```

#### Step 6: Test Structured Logging (30 min)

```bash
# Test JSON output
LOG_JSON_OUTPUT=true python -m wflo

# Test colored output
LOG_JSON_OUTPUT=false python -m wflo

# Verify trace_id appears when OpenTelemetry is active
```

---

## Phase 2.2: OpenTelemetry Implementation (6 hours)

### Goals
- Auto-instrument SQLAlchemy queries
- Auto-instrument HTTP clients
- Manual instrumentation for workflows
- Trace propagation across services
- Export to OTLP (OpenTelemetry Protocol)

### Implementation Steps

#### Step 1: Create OpenTelemetry Configuration (1 hour)

**File**: `src/wflo/observability/tracing.py`

```python
"""OpenTelemetry tracing configuration."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(
    service_name: str = "wflo",
    service_version: str = "0.1.0",
    otlp_endpoint: str = None,
) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP gRPC endpoint (e.g., "localhost:4317")
                      If None, traces are not exported
    """
    # Create resource with service metadata
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processor with OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,  # Use TLS in production
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()

    # Auto-instrument aiohttp client
    AioHttpClientInstrumentor().instrument()


def get_tracer(name: str = None) -> trace.Tracer:
    """Get an OpenTelemetry tracer.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer for creating spans
    """
    return trace.get_tracer(name or "wflo")
```

#### Step 2: Add OpenTelemetry Settings (15 min)

**File**: `src/wflo/config/settings.py`

```python
# OpenTelemetry
opentelemetry_enabled: bool = Field(
    default=False,
    description="Enable OpenTelemetry tracing",
)
opentelemetry_otlp_endpoint: str | None = Field(
    default=None,
    description="OTLP gRPC endpoint (e.g., localhost:4317)",
)
```

#### Step 3: Initialize Tracing at Startup (15 min)

**Update**: `src/wflo/app.py`

```python
from wflo.observability.tracing import configure_tracing

def initialize():
    settings = get_settings()

    # Configure logging
    configure_logging(...)

    # Configure tracing
    if settings.opentelemetry_enabled:
        configure_tracing(
            service_name="wflo",
            service_version="0.1.0",
            otlp_endpoint=settings.opentelemetry_otlp_endpoint,
        )
```

#### Step 4: Add Manual Instrumentation to Workflows (2 hours)

**File**: `src/wflo/temporal/workflows.py`

```python
from wflo.observability.tracing import get_tracer
from opentelemetry import trace

tracer = get_tracer(__name__)

@workflow.defn
class WfloWorkflow:
    @workflow.run
    async def run(self, workflow_id: str, inputs: dict, max_cost_usd: float | None = None):
        # Create span for workflow execution
        with tracer.start_as_current_span(
            "workflow.execute",
            attributes={
                "workflow.id": workflow_id,
                "workflow.execution_id": self.execution_id,
            }
        ) as span:
            try:
                outputs = await self._execute_steps(...)
                span.set_attribute("workflow.status", "completed")
                return outputs
            except Exception as e:
                span.set_attribute("workflow.status", "failed")
                span.record_exception(e)
                raise
```

#### Step 5: Add Manual Instrumentation to Activities (1.5 hours)

**File**: `src/wflo/temporal/activities.py`

```python
from wflo.observability.tracing import get_tracer

tracer = get_tracer(__name__)

@activity.defn
async def save_workflow_execution(...):
    with tracer.start_as_current_span("activity.save_workflow_execution"):
        async for session in get_session():
            # Database operations automatically instrumented by SQLAlchemy instrumentor
            pass
```

#### Step 6: Add Sandbox Instrumentation (1 hour)

**File**: `src/wflo/sandbox/runtime.py`

```python
from wflo.observability.tracing import get_tracer

tracer = get_tracer(__name__)

async def execute_code(self, code: str, ...):
    with tracer.start_as_current_span(
        "sandbox.execute",
        attributes={
            "sandbox.language": language,
            "sandbox.timeout": timeout_seconds,
        }
    ) as span:
        container = await self._create_container(...)
        # ... execution logic
        span.set_attribute("sandbox.exit_code", exit_code)
        return result
```

#### Step 7: Test OpenTelemetry (30 min)

```bash
# Start Jaeger for local testing
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Run with tracing enabled
OPENTELEMETRY_ENABLED=true OPENTELEMETRY_OTLP_ENDPOINT=localhost:4317 python -m wflo

# View traces at http://localhost:16686
```

---

## Phase 2.3: Prometheus Metrics (4 hours)

### Goals
- Workflow execution metrics
- Cost tracking metrics
- Performance metrics (latency, throughput)
- HTTP endpoint for Prometheus scraping

### Implementation Steps

#### Step 1: Create Metrics Module (1 hour)

**File**: `src/wflo/observability/metrics.py`

```python
"""Prometheus metrics for Wflo."""

from prometheus_client import Counter, Histogram, Gauge, Info

# Workflow metrics
workflow_executions_total = Counter(
    "wflo_workflow_executions_total",
    "Total number of workflow executions",
    ["workflow_id", "status"],
)

workflow_duration_seconds = Histogram(
    "wflo_workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
)

workflow_executions_active = Gauge(
    "wflo_workflow_executions_active",
    "Number of currently active workflow executions",
)

# Cost metrics
llm_cost_total_usd = Counter(
    "wflo_llm_cost_total_usd",
    "Total LLM API cost in USD",
    ["model"],
)

llm_tokens_total = Counter(
    "wflo_llm_tokens_total",
    "Total LLM tokens used",
    ["model", "token_type"],  # token_type: prompt or completion
)

# Sandbox metrics
sandbox_executions_total = Counter(
    "wflo_sandbox_executions_total",
    "Total sandbox code executions",
    ["language", "status"],
)

sandbox_duration_seconds = Histogram(
    "wflo_sandbox_duration_seconds",
    "Sandbox execution duration in seconds",
    ["language"],
)

# Database metrics (already instrumented by SQLAlchemy, but add custom ones)
database_operations_total = Counter(
    "wflo_database_operations_total",
    "Total database operations",
    ["operation"],  # operation: select, insert, update, delete
)

# Service info
service_info = Info(
    "wflo_service",
    "Wflo service information",
)
```

#### Step 2: Instrument Workflows (1 hour)

**File**: `src/wflo/temporal/workflows.py`

```python
from wflo.observability.metrics import (
    workflow_executions_total,
    workflow_duration_seconds,
    workflow_executions_active,
)
import time

@workflow.defn
class WfloWorkflow:
    @workflow.run
    async def run(self, ...):
        workflow_executions_active.inc()
        start_time = time.time()

        try:
            outputs = await self._execute_steps(...)
            workflow_executions_total.labels(
                workflow_id=workflow_id,
                status="completed",
            ).inc()
            return outputs
        except Exception as e:
            workflow_executions_total.labels(
                workflow_id=workflow_id,
                status="failed",
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            workflow_duration_seconds.labels(workflow_id=workflow_id).observe(duration)
            workflow_executions_active.dec()
```

#### Step 3: Instrument Cost Tracking (30 min)

**File**: `src/wflo/cost/tracker.py`

```python
from wflo.observability.metrics import llm_cost_total_usd, llm_tokens_total

class CostTracker:
    def calculate_cost(self, usage: TokenUsage) -> float:
        cost = # ... calculation

        # Record metrics
        llm_cost_total_usd.labels(model=usage.model).inc(cost)
        llm_tokens_total.labels(model=usage.model, token_type="prompt").inc(usage.prompt_tokens)
        llm_tokens_total.labels(model=usage.model, token_type="completion").inc(usage.completion_tokens)

        return cost
```

#### Step 4: Instrument Sandbox (30 min)

**File**: `src/wflo/sandbox/runtime.py`

```python
from wflo.observability.metrics import (
    sandbox_executions_total,
    sandbox_duration_seconds,
)

async def execute_code(self, ...):
    start_time = time.time()

    try:
        result = # ... execution
        sandbox_executions_total.labels(
            language=language,
            status="success" if result.exit_code == 0 else "error",
        ).inc()
        return result
    finally:
        duration = time.time() - start_time
        sandbox_duration_seconds.labels(language=language).observe(duration)
```

#### Step 5: Create Metrics HTTP Endpoint (1 hour)

**File**: `src/wflo/observability/server.py`

```python
"""HTTP server for metrics and health endpoints."""

import asyncio
from aiohttp import web
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

async def metrics_handler(request):
    """Prometheus metrics endpoint."""
    return web.Response(
        body=generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )

async def health_handler(request):
    """Health check endpoint."""
    return web.json_response({"status": "healthy"})

async def start_metrics_server(host: str = "0.0.0.0", port: int = 8000):
    """Start HTTP server for metrics."""
    app = web.Application()
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"Metrics server started on http://{host}:{port}")
    print(f"Metrics available at http://{host}:{port}/metrics")

    # Keep server running
    await asyncio.Event().wait()
```

#### Step 6: Integrate Metrics Server with Worker (30 min)

**File**: `src/wflo/temporal/worker.py`

```python
from wflo.observability.server import start_metrics_server

async def run_worker(...):
    # Start metrics server in background
    metrics_task = asyncio.create_task(start_metrics_server(port=8000))

    # Run worker
    client = await Client.connect(...)
    # ... rest of worker logic
```

#### Step 7: Test Prometheus Metrics (30 min)

```bash
# Start worker with metrics
poetry run python -m wflo.temporal.worker

# Check metrics
curl http://localhost:8000/metrics

# Should see:
# wflo_workflow_executions_total{workflow_id="...",status="completed"} 5
# wflo_llm_cost_total_usd{model="gpt-4"} 0.125
# wflo_sandbox_executions_total{language="python",status="success"} 10
```

---

## Phase 2.4: Integration and Testing (1 hour)

### Create Observability Package Init

**File**: `src/wflo/observability/__init__.py`

```python
"""Observability package with logging, tracing, and metrics."""

from wflo.observability.logging import configure_logging, get_logger
from wflo.observability.tracing import configure_tracing, get_tracer
from wflo.observability.metrics import (
    workflow_executions_total,
    workflow_duration_seconds,
    llm_cost_total_usd,
    sandbox_executions_total,
)
from wflo.observability.server import start_metrics_server

__all__ = [
    "configure_logging",
    "get_logger",
    "configure_tracing",
    "get_tracer",
    "workflow_executions_total",
    "workflow_duration_seconds",
    "llm_cost_total_usd",
    "sandbox_executions_total",
    "start_metrics_server",
]
```

### Update Documentation

**File**: `docs/observability.md` (create)

- Structlog configuration and usage
- OpenTelemetry setup with Jaeger
- Prometheus metrics catalog
- Grafana dashboard examples

---

## Success Criteria

- [ ] Structlog configured and working (JSON + colored output)
- [ ] All major modules using structlog
- [ ] Trace correlation working (trace_id in logs)
- [ ] OpenTelemetry auto-instrumentation active
- [ ] Manual spans created for workflows/activities
- [ ] Prometheus metrics exposed on /metrics
- [ ] Metrics recorded for workflows, costs, sandbox
- [ ] Integration tests pass
- [ ] Documentation updated

---

## Testing Checklist

```bash
# 1. Test structured logging
python -m wflo.temporal.worker

# 2. Test with JSON output
LOG_JSON_OUTPUT=true python -m wflo.temporal.worker

# 3. Test OpenTelemetry with Jaeger
docker run -d --name jaeger -e COLLECTOR_OTLP_ENABLED=true -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one:latest
OPENTELEMETRY_ENABLED=true OPENTELEMETRY_OTLP_ENDPOINT=localhost:4317 python -m wflo.temporal.worker

# 4. Test Prometheus metrics
curl http://localhost:8000/metrics

# 5. Test trace propagation
# Execute a workflow and verify traces appear in Jaeger UI

# 6. Run integration tests
pytest tests/integration/ -v
```

---

## Next Steps After Phase 2

- Phase 3: Redis (distributed locks, caching)
- Phase 4: Kafka (event streaming)
- Phase 5: Security hardening
- Phase 6: Testing improvements

**Estimated Total Time Phase 2**: 14 hours
