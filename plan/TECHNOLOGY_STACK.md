# Wflo Technology Stack - Final Decisions

**Last Updated**: 2025-11-09
**Status**: Finalized for Phase 1 Development

## Core Technology Decisions

### 1. Workflow Orchestration: **Temporal.io**

**Decision**: Use Temporal Python SDK for durable workflow execution

**Rationale**:
- Production-grade durability and fault tolerance
- Built-in state management and recovery
- Scalable from day one (handles millions of workflows)
- Strong Python SDK with async/await support
- Active development and enterprise backing

**Key Libraries**:
- `temporalio` - Official Python SDK (2024-2025 version)

**Patterns to Follow**:
- Workflow naming: `*_workflow` suffix
- Activity naming: `*_activity` suffix
- Deterministic workflow code (no random, no direct I/O)
- Use `SandboxedWorkflowRunner` for Pydantic models
- Worker versioning for deployments

**References**:
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal Python Docs](https://docs.temporal.io/develop/python)

---

### 2. Message Queue: **Apache Kafka**

**Decision**: Use Kafka with confluent-kafka-python client

**Rationale**:
- Industry-standard for event streaming
- High throughput and low latency
- Strong ordering guarantees
- Excellent Python support with async capabilities
- Production-ready with extensive tooling

**Key Libraries**:
- `confluent-kafka` (v2.x) - Best performance, built on librdkafka C library
- Native async/await support (added in recent versions)
- Actively maintained by Confluent

**Why Not Alternatives**:
- ❌ `kafka-python`: Minimal updates (2020-2024 gap)
- ❌ `aiokafka`: Good for pure asyncio, but confluent-kafka now has async support
- ❌ Redis Streams: Not as scalable for high-volume event streaming

**References**:
- [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python)
- [Confluent Python Docs](https://docs.confluent.io/kafka-clients/python/current/overview.html)

---

### 3. Sandbox Execution: **Docker + E2B Code Interpreter**

**Decision**: Multi-layered sandbox approach

**Phase 1**: `aiodocker` for general container management
- Async Docker API wrapper
- Full control over container lifecycle
- Resource limit enforcement (CPU, memory, network)

**Phase 2**: `e2b-code-interpreter` for AI-generated code execution
- Pre-built sandboxed Jupyter environments
- Firecracker microVM isolation
- 24-hour max execution time
- Built-in support for popular data science packages

**Key Libraries**:
- `aiodocker` - AsyncIO Docker SDK
- `e2b-code-interpreter` - Specialized AI code sandbox (later phase)

**Security Measures**:
- Network isolation by default (opt-in networking)
- Read-only filesystems with writable temp dirs
- Seccomp and AppArmor profiles
- Resource limits enforced at container level

**References**:
- [aiodocker GitHub](https://github.com/aio-libs/aiodocker)
- [E2B Code Interpreter](https://github.com/e2b-dev/code-interpreter)

---

### 4. Cost Tracking: **tokencost + LiteLLM**

**Decision**: Hybrid approach for accurate cost tracking

**Primary**: `tokencost` (AgentOps-AI)
- Supports 400+ LLM models
- Uses real token counting APIs (Tiktoken for OpenAI, Anthropic API for Claude)
- No estimates - only real usage data
- Cached token discount tracking

**Fallback/Alternative**: `litellm`
- Unified API across providers
- Built-in cost calculation
- Model routing for cost optimization

**Key Libraries**:
- `tokencost` - Primary cost tracking
- `litellm` - Optional unified LLM interface
- `tiktoken` - OpenAI token counting
- Anthropic token counting API (native)

**Features**:
- Real-time cost calculation
- Per-provider pricing tables
- Support for OpenAI, Anthropic, Google, Cohere, etc.
- Cached token discounting

**References**:
- [tokencost GitHub](https://github.com/AgentOps-AI/tokencost)
- [LiteLLM Docs](https://docs.litellm.ai/docs/completion/token_usage)

---

### 5. Configuration Management: **pydantic-settings v2**

**Decision**: Use pydantic-settings for type-safe configuration

**Key Features**:
- Type validation with Pydantic v2
- Environment variable support (.env files)
- Nested configuration with `env_nested_delimiter`
- Secret management (Docker secrets, cloud secret managers)
- Integration with AWS Secrets Manager, GCP Secret Manager, Azure Key Vault

**Key Libraries**:
- `pydantic-settings` (v2.11+)
- `python-dotenv` - .env file loading

**Pattern**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
    )

    database_url: str
    kafka_bootstrap_servers: str
    temporal_host: str
```

**References**:
- [pydantic-settings Docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

### 6. Database: **PostgreSQL with asyncpg + SQLAlchemy 2.0**

**Decision**: Async PostgreSQL with modern SQLAlchemy

**Key Libraries**:
- `asyncpg` - Fastest async PostgreSQL driver
- `sqlalchemy[asyncio]` (v2.0+) - Modern async ORM
- `alembic` - Database migrations

**Connection Pattern**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host:port/db",
    echo=True,
)
```

**Best Practices**:
- AsyncSession is NOT concurrency-safe (one per request/workflow)
- Use async context managers for session lifecycle
- Explicit transaction management
- Connection pooling via AsyncEngine

**References**:
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [asyncpg Performance Guide](https://www.tigerdata.com/blog/how-to-build-applications-with-asyncpg-and-postgresql)

---

### 7. Caching: **Redis**

**Decision**: Redis for caching, session state, and distributed locks

**Key Libraries**:
- `redis[asyncio]` - Async Redis client

**Use Cases**:
- Session state storage
- Distributed locks for coordination
- Cache for workflow metadata
- Rate limiting

---

### 8. Observability: **OpenTelemetry + Prometheus + structlog**

**Decision**: Industry-standard observability stack

**Tracing**: OpenTelemetry
- `opentelemetry-api` - Core API
- `opentelemetry-sdk` - SDK implementation
- `opentelemetry-instrumentation` - Auto-instrumentation
- Export to Jaeger, Tempo, or cloud providers

**Metrics**: Prometheus
- `prometheus-client` - Python client for Prometheus

**Logging**: structlog
- `structlog` - Structured logging with JSON output
- Correlation IDs across all logs

**Approach**:
- Auto-instrumentation for common libraries (SQLAlchemy, aiohttp, etc.)
- Manual spans for custom workflow logic
- Batch processing for production efficiency

**References**:
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [structlog Docs](https://www.structlog.org/)

---

### 9. Testing: **pytest + pytest-asyncio**

**Decision**: pytest with async support and comprehensive coverage

**Key Libraries**:
- `pytest` (v8.x+) - Main testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `AsyncMock` (stdlib) - Async mocking

**Testing Strategy**:
1. **Unit Tests**: Individual components, no external dependencies
2. **Integration Tests**: Component interactions with Docker containers (PostgreSQL, Redis, Kafka)
3. **E2E Tests**: Full workflow execution through Temporal

**Coverage Target**: 80% minimum

**Patterns**:
- Use `@pytest.mark.asyncio` for async tests
- Async fixtures for setup/teardown
- `asyncio.gather()` for concurrent test operations
- `asyncio.Event` for race condition testing

**References**:
- [pytest-asyncio Guide](https://pytest-with-eric.com/pytest-advanced/pytest-asyncio/)

---

### 10. Development Tools

**Package Management**:
- `poetry` - Dependency management and packaging

**Code Quality**:
- `ruff` - Fast Python linter (replaces flake8, isort, etc.)
- `black` - Code formatter
- `mypy` - Static type checking (strict mode)

**CI/CD**:
- GitHub Actions - Automated testing and deployment

**Documentation**:
- `mkdocs-material` - Documentation site generator

---

## Dependency Summary

### Core Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
temporalio = "^1.5.0"
confluent-kafka = "^2.3.0"
aiodocker = "^0.21.0"
asyncpg = "^0.29.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
alembic = "^1.13.0"
redis = {extras = ["asyncio"], version = "^5.0.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
tokencost = "^0.1.0"
opentelemetry-api = "^1.21.0"
opentelemetry-sdk = "^1.21.0"
opentelemetry-instrumentation = "^0.42b0"
prometheus-client = "^0.19.0"
structlog = "^24.1.0"
```

### Development Dependencies
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
ruff = "^0.1.0"
black = "^24.0.0"
mypy = "^1.8.0"
mkdocs-material = "^9.5.0"
```

---

## Key Design Patterns

### 1. Async-First Architecture
- All I/O operations use async/await
- Event loop management via asyncio
- Concurrent operations with `asyncio.gather()`

### 2. Type Safety
- Full type hints on all functions
- Pydantic models for data validation
- mypy strict mode enforcement

### 3. Observability-First
- Structured logging with correlation IDs
- Distributed tracing on all workflows
- Metrics for all critical operations

### 4. Security-First
- Sandboxed execution by default
- Least privilege principles
- Secret management via environment/vault

### 5. Testing-First
- Tests written alongside code
- Integration tests with Docker containers
- 80% coverage minimum

---

## Infrastructure Requirements

### Local Development
- Docker Desktop or Docker Engine
- PostgreSQL 15+ (via docker-compose)
- Redis 7+ (via docker-compose)
- Kafka 3.6+ (via docker-compose)
- Python 3.11+

### Production (Phase 3)
- Kubernetes cluster or managed container service
- Managed PostgreSQL (RDS, Cloud SQL, etc.)
- Managed Redis (ElastiCache, MemoryStore, etc.)
- Managed Kafka (Confluent Cloud, MSK, etc.)
- Temporal Cloud or self-hosted Temporal cluster

---

## Learning from Open Source

### Projects Analyzed
- **LangGraph**: Graph-based agent orchestration (fastest performance)
- **AutoGPT**: Goal-oriented agent platform
- **E2B**: Secure code execution sandboxes
- **Temporal Samples**: Production workflow patterns

### Code Reuse Opportunities
- E2B's sandbox isolation patterns
- Temporal's workflow/activity patterns
- LangGraph's state management approach
- tokencost's multi-provider pricing tables

### DRY Principle
- Use established libraries instead of custom implementations
- Follow proven patterns from production systems
- Contribute improvements back to open source
- Document deviations from standard patterns

---

## Phase 1 Scope (MVP)

**In Scope**:
- ✅ Temporal workflow orchestration
- ✅ Basic Docker sandbox execution (aiodocker)
- ✅ PostgreSQL state persistence
- ✅ Kafka event streaming
- ✅ Cost tracking (tokencost)
- ✅ Structured logging (structlog)
- ✅ Python SDK for workflow definition
- ✅ Basic observability (logs + basic metrics)

**Out of Scope (Phase 2+)**:
- ❌ E2B advanced sandboxing
- ❌ Human approval gates
- ❌ Advanced OpenTelemetry tracing
- ❌ REST API
- ❌ CLI tool
- ❌ Rollback system
- ❌ Policy engine

---

## Next Steps

1. Initialize Poetry project with dependencies
2. Set up docker-compose for local development
3. Create package structure (`src/wflo/`)
4. Implement core data models (Pydantic)
5. Build Temporal workflow/activity scaffolding
6. Add PostgreSQL state persistence
7. Integrate Kafka event streaming
8. Implement Docker sandbox runtime
9. Add cost tracking integration
10. Set up testing infrastructure

**Ready to build!** 🚀
