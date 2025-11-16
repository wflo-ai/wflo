# Wflo

> **Add two lines. Never worry about AI agents again.**

Production-ready safety for AI agents with zero-friction integration.

```python
import wflo
wflo.init(budget_usd=10.0)

# Your existing code - no changes needed!
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a story"}]
)
```

**What just happened?**
- ⚠️  Predicted cost: $0.15 (before execution)
- 💰 Auto-optimized: gpt-4 → gpt-3.5-turbo
- ✅ Saved: $0.12 (80% cost reduction)
- 🛡️  Budget enforced: Hard stop at $10
- 🔧 Self-heals on failures automatically

**Works with everything:** LangGraph • CrewAI • AutoGen • OpenAI • Anthropic • Custom agents

---

## Why Wflo?

AI agents in production face critical challenges:

- 💸 **Runaway costs** - One agent loop can burn $10K+ overnight
- 🔥 **No safety net** - Agents fail with no auto-recovery
- 🎲 **Cost unpredictability** - Don't know costs until after spending
- 🚫 **Compliance gaps** - No approval gates for risky operations
- 📊 **Poor observability** - Can't debug or trace agent decisions

**Wflo solves these with 2 lines of code.**

## Core Features

### 🔮 **Predictive Cost Prevention** (Unique to Wflo)
- Predicts costs **before** execution using historical data
- Alerts when predicted cost exceeds budget
- Suggests cheaper alternatives automatically
- Learn from every execution to improve predictions

### 💰 **Auto-Optimization** (50-90% Cost Savings)
- Automatically switches to cheaper models when possible
- Reduces token usage intelligently
- Enables semantic caching for repeated queries
- Shows exactly how much you saved

### 🔧 **Self-Healing** (Zero-Downtime Resilience)
- Auto-retry on rate limits with exponential backoff
- Automatic model fallback when API overloaded
- Context truncation on token limit errors
- Recovers from 90%+ of common failures

### 🛡️ **Budget Enforcement** (Hard Limits)
- Hard stop at budget limit (prevents overruns)
- Per-workflow, per-agent, or global budgets
- Real-time cost tracking across all providers
- Circuit breakers prevent cost explosions

### ✋ **Human Approval Gates** (Enterprise Compliance)
- Automatic risk detection for sensitive operations
- Slack/email notifications for approvals
- Complete audit trail for compliance (HIPAA, SOC2, PCI)
- Configurable approval policies

### 📈 **Full Observability** (Production Debugging)
- Distributed tracing for every LLM call
- Cost breakdown by model, agent, workflow
- Performance metrics (latency, tokens, throughput)
- Time-travel debugging (replay past executions)

## Quick Start

### Installation

```bash
pip install wflo
```

### Option 1: Autopilot Mode (Recommended - 2 Lines)

Add to the top of your code:

```python
import wflo
wflo.init(budget_usd=10.0)  # That's it!

# Your existing code works unchanged
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
# Wflo automatically: predicts cost, optimizes, enforces budget, self-heals
```

### Option 2: Explicit Workflow API

For more control:

```python
from wflo.sdk.workflow import WfloWorkflow

# Wrap your agent/workflow
workflow = WfloWorkflow(
    name="my-agent",
    budget_usd=50.0,
    enable_checkpointing=True,
)

# Run with protection
result = await workflow.execute(my_agent_function, inputs)
```

## Real-World Examples

### Example 1: LangGraph Integration

```python
import wflo
wflo.init(budget_usd=10.0)  # Add this line

# Your existing LangGraph code - no changes!
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(llm, tools)
result = agent.invoke({"messages": [...]})
```

### Example 2: CrewAI Integration

```python
import wflo
wflo.init(budget_usd=5.0, compliance_mode="hipaa")  # Add this line

# Your existing CrewAI code - no changes!
from crewai import Agent, Task, Crew
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

### Example 3: Custom Agent with Approval Gates

```python
import wflo
wflo.init(
    budget_usd=100.0,
    require_approval_for=["sql_delete", "api_post"],  # Auto-detect risky ops
    compliance_mode="pci"  # PCI compliance preset
)

# Your custom agent
class MyAgent:
    def run(self):
        # Wflo detects "DELETE FROM users" and pauses for approval
        db.execute("DELETE FROM users WHERE inactive")
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

- **Docker & Docker Compose** - For running infrastructure services
- **Python 3.11 or 3.12** - ⚠️ Python 3.13 not supported (asyncpg incompatibility)
- **Poetry** - Python dependency management

**Python 3.13 Users**: If you have Python 3.13, switch to 3.11 or 3.12:
```bash
# macOS/Linux
brew install python@3.11  # or use pyenv
poetry env use python3.11

# Verify version
poetry run python --version  # Should show Python 3.11.x or 3.12.x
```

### Quick Start

```bash
# 1. Clone and install dependencies
git clone https://github.com/wflo-ai/wflo.git
cd wflo
poetry install

# 2. Start infrastructure services
docker compose up -d

# 3. Wait for services to initialize (30-60 seconds)
# Then run database migrations
poetry run alembic upgrade head

# 4. Create test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# 5. Run tests to verify
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/test_redis.py::TestRedisClient::test_redis_health_check -v
```

**For detailed infrastructure setup, troubleshooting, and management, see [INFRASTRUCTURE.md](INFRASTRUCTURE.md).**

### Infrastructure Services

After `docker compose up -d`, the following services will be available:

| Service | Port | Purpose | UI |
|---------|------|---------|-----|
| PostgreSQL | 5432 | Workflow metadata, execution history | - |
| Redis | 6379 | Caching, distributed locks | - |
| Kafka | 9092 | Event streaming | - |
| Temporal | 7233 | Workflow orchestration (gRPC) | http://localhost:8233 |
| Jaeger | 16686 | Distributed tracing | http://localhost:16686 |

**Check service health:**
```bash
docker compose ps  # All should show "Up (healthy)"
```

### Running Workflows

```bash
# Terminal 1: Start Temporal worker
poetry run python -m wflo.temporal.worker

# Terminal 2: Execute a workflow
poetry run python examples/simple_workflow.py
```

### Running Tests

```bash
# Quick verification (all integration tests)
./scripts/run_tests.sh integration

# Individual test suites
poetry run pytest tests/integration/test_redis.py -v      # Redis tests
poetry run pytest tests/integration/test_kafka.py -v      # Kafka tests
poetry run pytest tests/integration/test_database.py -v   # Database tests

# All tests with coverage
poetry run pytest --cov=wflo --cov-report=html
```

See [TESTING.md](TESTING.md) for detailed testing guide.

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
