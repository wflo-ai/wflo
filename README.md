# Wflo

> **The secure runtime for AI agents**

Wflo provides production-ready infrastructure for running AI agents safely: sandboxed execution, human approval gates, cost governance, rollback capabilities, and full observability.

## Why Wflo?

AI agents are powerful, but running them in production is risky:

- 💸 **Runaway costs** - One misconfigured agent can burn thousands in API fees
- 🔒 **Security concerns** - Agents executing arbitrary code without isolation
- 🚫 **Irreversible actions** - No way to undo agent mistakes
- 📊 **Poor observability** - Can't debug what agents actually did
- ⚖️ **Compliance gaps** - No audit trails for regulated industries

**Wflo solves these problems.**

## Core Features

### 🛡️ Sandboxed Execution
- Isolated container environments for each agent workflow
- Resource limits (CPU, memory, network)
- Filesystem isolation and security policies
- Based on proven container isolation technology

### ✋ Human Approval Gates
- Configurable checkpoints before critical operations
- Risk-based approval routing (auto-approve low-risk, require human for high-risk)
- Approval timeout policies and escalation
- Complete audit trail of all approvals/rejections

### 💰 Cost Governance
- Budget limits per workflow, agent, or time period
- Real-time cost tracking and alerts
- Circuit breakers when budgets exceeded
- Multi-provider cost attribution and optimization

### ⏮️ Rollback & Recovery
- State snapshots before critical operations
- Automatic rollback on failures
- Compensating transactions for external APIs
- Point-in-time recovery capabilities

### 📈 Full Observability
- Complete execution traces for every agent action
- Real-time metrics: latency, cost, token usage
- Structured logs with correlation IDs
- Integration with popular observability tools

## Quick Start

```bash
# Install Wflo CLI
pip install wflo

# Initialize a new workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 --require-approval
```

## Example: Safe Agent Workflow

```python
from wflo import Workflow, ApprovalGate, CostLimit

# Define a workflow with built-in safety
workflow = Workflow("data-processor")

# Set cost budget
workflow.set_budget(max_cost_usd=50.00)

# Add approval gate before destructive operations
@workflow.step(approval_required=True)
async def delete_old_records(context):
    """This will pause and wait for human approval"""
    await context.db.execute("DELETE FROM records WHERE age > 365")

# Add rollback capability
@workflow.step(rollback_enabled=True)
async def update_production_data(context):
    """Automatic rollback on failure"""
    snapshot = await context.db.snapshot()
    try:
        await context.db.bulk_update(records)
    except Exception:
        await context.db.restore(snapshot)
        raise

# Run with observability
result = await workflow.run(
    sandbox=True,           # Run in isolated container
    trace=True,            # Full execution tracing
    notify="slack://prod"  # Alert on approval needed
)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Wflo Application Layer                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Temporal   │  │     Cost     │  │  Approval    │         │
│  │  Workflows   │  │   Tracking   │  │    Gates     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Observability Infrastructure                 │  │
│  │  Structlog | OpenTelemetry | Prometheus | Kafka Events   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │    Redis    │  │      Kafka      │
│  (Workflows,    │  │  (Caching,  │  │ (Event Stream,  │
│   Executions,   │  │   Locks)    │  │  Real-time)     │
│   Costs, State) │  │             │  │                 │
└─────────────────┘  └─────────────┘  └─────────────────┘
           │
           ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Sandbox 1  │  │  Sandbox 2  │  │  Sandbox N  │
    │  (Docker)   │  │  (Docker)   │  │  (Docker)   │
    │   Python    │  │  JavaScript │  │     ...     │
    └─────────────┘  └─────────────┘  └─────────────┘
```

## Technology Stack

### Core Infrastructure
- **Temporal.io**: Durable workflow orchestration
- **PostgreSQL**: Workflow metadata, execution history, cost tracking
- **Redis**: Distributed locks, LLM response caching
- **Kafka**: Event streaming for observability and integrations
- **Docker**: Sandboxed code execution with resource limits

### Observability
- **Structlog**: Structured JSON logging with trace correlation
- **OpenTelemetry**: Distributed tracing across workflows and activities
- **Prometheus**: Metrics collection (30+ metrics)
- **Jaeger**: Trace visualization (development)

### Language & Frameworks
- **Python 3.11+**: Async/await, type hints, Pydantic models
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **Pydantic**: Data validation and serialization
- **FastAPI**: API endpoints (future)

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Poetry (for dependency management)

### 1. Clone and Install

```bash
# Clone repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install dependencies
poetry install
```

### 2. Start Infrastructure Services

```bash
# Start all services (PostgreSQL, Redis, Kafka, Temporal, Jaeger)
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

Services running:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Kafka**: `localhost:9092`
- **Temporal**: `localhost:7233` (gRPC) | `localhost:8233` (Web UI)
- **Jaeger**: `localhost:16686` (Web UI)

### 3. Initialize Database

```bash
# Run database migrations
poetry run alembic upgrade head

# (Optional) Seed test data
poetry run python scripts/seed_data.py
```

### 4. Run Tests

```bash
# Run all tests
poetry run pytest

# Run only unit tests (fast)
poetry run pytest tests/unit/ -v

# Run integration tests (requires Docker services)
poetry run pytest tests/integration/ -v

# Run with coverage
poetry run pytest --cov=wflo --cov-report=html
```

### 5. Run Temporal Worker

```bash
# Start Temporal worker (processes workflows)
poetry run python -m wflo.temporal.worker
```

## Running the Application

### Option 1: Development Mode

```bash
# Terminal 1: Start infrastructure
docker-compose up -d

# Terminal 2: Start Temporal worker
poetry run python -m wflo.temporal.worker

# Terminal 3: Run workflows
poetry run python examples/simple_workflow.py
```

### Option 2: Full Stack

```bash
# Start everything
docker-compose up -d

# Access services
# - Temporal UI: http://localhost:8233
# - Jaeger UI: http://localhost:16686
# - Prometheus: http://localhost:9090 (when configured)
```

## Current Implementation Status

### ✅ Completed (Phases 1-4)

**Phase 1: Cost Tracking**
- ✅ Automatic cost calculation for 400+ LLM models (tokencost library)
- ✅ Database persistence for cost history
- ✅ Budget enforcement and alerts
- ✅ Multi-model support (GPT-4, Claude, Gemini, etc.)

**Phase 2: Observability Foundation**
- ✅ Structured logging with structlog (JSON + colored output)
- ✅ OpenTelemetry distributed tracing
- ✅ Prometheus metrics (30+ metrics)
- ✅ Auto-instrumentation for SQLAlchemy and aiohttp

**Phase 3: Redis Infrastructure**
- ✅ Distributed locks for workflow deduplication
- ✅ LLM response caching (20-40% cost savings)
- ✅ Connection pooling and health checks
- ✅ Auto-renewal for long-running locks

**Phase 4: Kafka Event Streaming**
- ✅ Event schemas (Workflow, Cost, Sandbox, Audit)
- ✅ Async producer with idempotent delivery
- ✅ Consumer with group coordination
- ✅ Topic management and configuration
- ✅ 20+ integration tests

### 🚧 In Progress

**Phase 5: Security Hardening** (Planned)
- Container image scanning
- gVisor runtime evaluation
- Security audit logging
- Penetration testing

**Phase 6: Testing & Documentation** (Planned)
- Increase integration test coverage
- Performance benchmarks
- API documentation
- User guides

### 📋 Planned

- Human approval gates UI
- Multi-agent orchestration
- Rollback mechanisms
- CLI tool
- Cloud-hosted service

## Roadmap

### 2025 Q1 - Foundation ✅
- [x] Project setup and architecture
- [x] Temporal workflow engine
- [x] Docker sandbox execution
- [x] PostgreSQL database layer
- [x] Cost tracking (tokencost integration)
- [x] Observability (structlog, OpenTelemetry, Prometheus)
- [x] Redis caching and distributed locks
- [x] Kafka event streaming

### 2025 Q2 - Safety & Integration
- [ ] Human approval gates (API + UI)
- [ ] Event-driven workflow triggers
- [ ] Webhook integrations
- [ ] Slack/Discord notifications
- [ ] Advanced cost governance (rate limiting)
- [ ] State rollback mechanisms

### 2025 Q3 - Production Ready
- [ ] Multi-agent orchestration
- [ ] Policy engine (approval rules DSL)
- [ ] Security hardening (gVisor, image scanning)
- [ ] Compliance features (SOC2, HIPAA audit logs)
- [ ] Performance optimization
- [ ] Load testing and benchmarks

### 2025 Q4 - Platform & Ecosystem
- [ ] REST API and SDK
- [ ] TypeScript/JavaScript SDK
- [ ] CLI tool
- [ ] Cloud platform (hosted service)
- [ ] Marketplace for workflow templates
- [ ] Community integrations

## Use Cases

- **Financial Services**: Run fraud detection agents with mandatory approval gates
- **Healthcare**: HIPAA-compliant agent workflows with full audit trails
- **E-commerce**: Customer service automation with cost controls
- **Data Processing**: ETL agents with rollback on failures
- **DevOps**: Infrastructure automation with human oversight

## Contributing

We welcome contributions! Wflo is open-source and community-driven.

- **Discussions**: Share ideas and ask questions in [GitHub Discussions](https://github.com/wflo-ai/wflo/discussions)
- **Issues**: Report bugs or request features in [Issues](https://github.com/wflo-ai/wflo/issues)
- **Pull Requests**: See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

## Community

- **Discord**: [Join our community](https://discord.gg/wflo) (coming soon)
- **Twitter**: [@wflo_ai](https://twitter.com/wflo_ai) (coming soon)
- **Blog**: [wflo.ai/blog](https://wflo.ai/blog) (coming soon)

## Philosophy

We believe AI agents should be:
- **Safe by default** - Not bolted on as an afterthought
- **Production-ready** - Not just demos and prototypes
- **Observable** - You should know exactly what agents are doing
- **Governable** - Compliance and cost controls from day one
- **Recoverable** - Mistakes should be fixable, not fatal

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with inspiration from:
- **Kubernetes** - Container orchestration patterns
- **Temporal** - Durable workflow execution
- **LangChain/LangGraph** - Agent framework ecosystem
- **E2B** - Secure code execution sandboxes

---

**Status**: 🚧 Early Development - Not production ready yet

We're actively building in public. Star the repo to follow our progress!
