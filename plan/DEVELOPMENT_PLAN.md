# Wflo Development Plan - Phase 1 (MVP)

**Timeline**: 8-10 weeks
**Goal**: Production-ready foundation for AI agent orchestration

---

## Phase 1 Overview

### Objectives
- Core workflow orchestration with Temporal
- Sandboxed execution environment
- State persistence and recovery
- Cost tracking foundation
- Basic observability
- Python SDK for workflow definition
- 80% test coverage

### Success Criteria
- Can define and execute multi-step workflows
- Workflows run in isolated Docker containers
- All workflow state persists to PostgreSQL
- Real-time cost tracking for LLM operations
- Structured logging with correlation IDs
- Full test coverage for critical paths

---

## Week-by-Week Breakdown

### Week 1-2: Project Foundation

#### Goals
- Project structure initialized
- Development environment working
- CI/CD pipeline configured
- Core dependencies installed

#### Tasks
1. **Project Initialization**
   - Initialize Poetry project with `pyproject.toml`
   - Define package structure (`src/wflo/`)
   - Create `.gitignore` for Python/Docker
   - Set up pre-commit hooks

2. **Infrastructure Setup**
   - Create `docker-compose.yml` for local development
   - Configure PostgreSQL, Redis, Kafka, Temporal
   - Create `.env.example` with configuration template
   - Document environment variables

3. **Development Tooling**
   - Configure Ruff for linting
   - Set up Black for formatting
   - Configure mypy for type checking
   - Create `Makefile` for common tasks

4. **CI/CD Pipeline**
   - GitHub Actions workflow for tests
   - Automated linting and type checking
   - Coverage reporting
   - Docker image builds

5. **Testing Infrastructure**
   - pytest configuration
   - pytest-asyncio setup
   - Coverage reporting (pytest-cov)
   - Test fixtures for database/Redis/Kafka

**Deliverables**:
- ✅ Working development environment
- ✅ CI/CD pipeline running
- ✅ All services running via docker-compose
- ✅ Empty package structure with tests

---

### Week 3-4: Core Data Models & Configuration

#### Goals
- Type-safe configuration system
- Core domain models defined
- Database schema created
- Settings management working

#### Tasks
1. **Configuration Management**
   - Implement pydantic-settings for config
   - Create `Settings` class with all config values
   - Environment variable loading (.env)
   - Secret management patterns

2. **Core Data Models**
   - `WorkflowDefinition` - Workflow DAG specification
   - `WorkflowStep` - Individual step configuration
   - `WorkflowExecution` - Runtime execution instance
   - `WorkflowState` - Execution state and variables
   - `StateSnapshot` - Point-in-time state capture
   - `CostSummary` - Cost tracking aggregation
   - `ExecutionResult` - Step execution results

3. **Database Schema**
   - SQLAlchemy async models
   - Alembic migration setup
   - Initial migration for core tables
   - Database connection pooling

4. **Validation & Serialization**
   - Pydantic models for API validation
   - JSON serialization helpers
   - Type conversion utilities

**Deliverables**:
- ✅ Configuration system working with .env
- ✅ All core models defined with types
- ✅ Database schema migrations
- ✅ Unit tests for models (>80% coverage)

---

### Week 5-6: Temporal Integration & Workflow Engine

#### Goals
- Temporal worker running
- Basic workflow execution
- Activity implementations
- State management

#### Tasks
1. **Temporal Setup**
   - Temporal worker configuration
   - Workflow/activity registration
   - Worker versioning setup
   - Sandboxed workflow runner for Pydantic

2. **Workflow Manager**
   - `WorkflowManager` class for workflow CRUD
   - Create workflow from definition
   - Start workflow execution
   - Query workflow status
   - Cancel/terminate workflows

3. **Core Activities**
   - `execute_step_activity` - Run workflow step
   - `save_state_activity` - Persist state to database
   - `create_snapshot_activity` - Save state snapshot
   - `track_cost_activity` - Record operation costs

4. **State Manager**
   - `StateManager` for state persistence
   - State snapshot creation/restoration
   - Distributed locking (Redis)
   - State query and retrieval

5. **Workflow Execution Logic**
   - DAG parsing and validation
   - Step dependency resolution
   - Sequential execution engine
   - Error handling and retries

**Deliverables**:
- ✅ Temporal worker running workflows
- ✅ Can execute simple multi-step workflow
- ✅ State persists to PostgreSQL
- ✅ Integration tests with Temporal
- ✅ Workflow execution traces in Temporal UI

---

### Week 7-8: Sandbox Runtime & Execution

#### Goals
- Docker sandbox working
- Code execution isolated
- Resource limits enforced
- Sandbox lifecycle managed

#### Tasks
1. **Sandbox Runtime**
   - `SandboxRuntime` class using aiodocker
   - Container creation with resource limits
   - Network isolation configuration
   - Filesystem isolation (read-only + writable temp)

2. **Code Execution**
   - Execute Python code in sandbox
   - Capture stdout/stderr
   - Return execution results
   - Timeout handling

3. **Resource Management**
   - CPU limit enforcement
   - Memory limit enforcement
   - Network access control (default: disabled)
   - Disk space limits

4. **Sandbox Lifecycle**
   - Container creation/startup
   - Health checks
   - Cleanup on completion
   - Error recovery

5. **Security Hardening**
   - Seccomp profile configuration
   - AppArmor profile (Linux)
   - Non-root user execution
   - Capability dropping

**Deliverables**:
- ✅ Sandboxed Python code execution
- ✅ Resource limits enforced
- ✅ Network isolation working
- ✅ Sandbox integration tests
- ✅ Security profiles configured

---

### Week 9: Cost Tracking & Observability

#### Goals
- Real-time cost tracking
- Structured logging
- Basic metrics
- Correlation IDs

#### Tasks
1. **Cost Tracking**
   - `CostTracker` class using tokencost
   - LLM API call tracking
   - Token counting (OpenAI, Anthropic, etc.)
   - Cost aggregation per workflow
   - Budget checking utilities

2. **Structured Logging**
   - structlog configuration
   - JSON log formatting
   - Correlation ID propagation
   - Log level configuration
   - Context binding (workflow_id, execution_id, etc.)

3. **Metrics**
   - Prometheus client setup
   - Core metrics:
     - `workflow_executions_total`
     - `workflow_duration_seconds`
     - `workflow_cost_usd`
     - `sandbox_creation_duration`
     - `step_execution_duration`
   - Metrics export endpoint

4. **Correlation & Tracing**
   - Generate correlation IDs
   - Propagate IDs through workflow
   - Include in all logs
   - Link to Temporal trace IDs

**Deliverables**:
- ✅ Cost tracking for all LLM calls
- ✅ Structured JSON logs
- ✅ Prometheus metrics exposed
- ✅ Correlation IDs in all operations

---

### Week 10: Python SDK & Integration Testing

#### Goals
- Python SDK for users
- End-to-end tests
- Example workflows
- Documentation

#### Tasks
1. **Python SDK**
   - `Workflow` class for workflow definition
   - `@workflow.step()` decorator
   - `WorkflowContext` for step execution
   - Budget setting API
   - Sandbox configuration API

2. **SDK Features**
   - Workflow definition DSL
   - Step dependencies (DAG)
   - Type-safe context
   - Result passing between steps

3. **Example Workflows**
   - Simple linear workflow
   - Parallel execution workflow
   - Conditional branching workflow
   - LLM-based workflow with cost tracking

4. **End-to-End Testing**
   - Full workflow execution tests
   - Multi-step workflow tests
   - Error handling tests
   - Sandbox isolation tests
   - Cost tracking tests

5. **Documentation**
   - API reference
   - Getting started guide
   - Example workflows
   - Configuration guide
   - Troubleshooting

**Deliverables**:
- ✅ Working Python SDK
- ✅ 3+ example workflows
- ✅ End-to-end tests passing
- ✅ User documentation
- ✅ >80% overall test coverage

---

## Package Structure

```
wflo/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI/CD pipeline
│       └── release.yml         # Release automation
├── docs/
│   ├── ARCHITECTURE.md         # (existing)
│   ├── api/                    # API reference
│   ├── guides/                 # User guides
│   └── examples/               # Example workflows
├── plan/
│   ├── TECHNOLOGY_STACK.md     # (created)
│   ├── MINIMUM_REQUIREMENTS.md # (created)
│   ├── DEVELOPMENT_PLAN.md     # (this file)
│   └── TODO.md                 # Detailed task list
├── src/
│   └── wflo/
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py     # pydantic-settings configuration
│       ├── models/
│       │   ├── __init__.py
│       │   ├── workflow.py     # Workflow data models
│       │   ├── execution.py    # Execution models
│       │   └── state.py        # State models
│       ├── db/
│       │   ├── __init__.py
│       │   ├── engine.py       # Database engine setup
│       │   ├── models.py       # SQLAlchemy models
│       │   └── migrations/     # Alembic migrations
│       ├── workflow/
│       │   ├── __init__.py
│       │   ├── manager.py      # WorkflowManager
│       │   ├── engine.py       # Execution engine
│       │   └── state.py        # StateManager
│       ├── temporal/
│       │   ├── __init__.py
│       │   ├── worker.py       # Temporal worker setup
│       │   ├── workflows.py    # Temporal workflow definitions
│       │   └── activities.py   # Temporal activities
│       ├── sandbox/
│       │   ├── __init__.py
│       │   ├── runtime.py      # SandboxRuntime (aiodocker)
│       │   └── executor.py     # Code execution
│       ├── cost/
│       │   ├── __init__.py
│       │   ├── tracker.py      # CostTracker (tokencost)
│       │   └── pricing.py      # Pricing tables
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py      # structlog setup
│       │   ├── metrics.py      # Prometheus metrics
│       │   └── correlation.py  # Correlation ID handling
│       ├── events/
│       │   ├── __init__.py
│       │   └── kafka.py        # Kafka producer/consumer
│       └── sdk/
│           ├── __init__.py
│           ├── workflow.py     # User-facing Workflow class
│           ├── decorators.py   # @workflow.step decorator
│           └── context.py      # WorkflowContext
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_workflow_manager.py
│   │   ├── test_sandbox.py
│   │   ├── test_cost_tracker.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_database.py
│   │   ├── test_temporal.py
│   │   ├── test_kafka.py
│   │   └── test_sandbox_integration.py
│   ├── e2e/
│   │   ├── test_simple_workflow.py
│   │   ├── test_parallel_workflow.py
│   │   └── test_llm_workflow.py
│   ├── conftest.py             # Shared fixtures
│   └── fixtures/
│       ├── docker.py           # Docker fixtures
│       └── workflows.py        # Test workflow definitions
├── examples/
│   ├── simple_workflow.py
│   ├── llm_workflow.py
│   └── data_processing.py
├── docker-compose.yml          # Local development infrastructure
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Poetry configuration
├── Makefile                    # Common development tasks
├── README.md                   # (existing)
├── CONTRIBUTING.md             # (existing)
└── LICENSE                     # (existing)
```

---

## Testing Strategy

### Unit Tests (50% of coverage)
- Individual class/function testing
- No external dependencies
- Mock all I/O (database, Kafka, Docker)
- Fast execution (< 1 second each)

**Coverage targets**:
- Models: 100%
- Managers: 90%
- Utilities: 90%

### Integration Tests (30% of coverage)
- Component interaction testing
- Real external dependencies (via Docker)
- Database migrations
- Kafka message flow
- Temporal workflow execution

**Coverage targets**:
- Database layer: 90%
- Temporal integration: 80%
- Kafka integration: 80%
- Sandbox runtime: 90%

### End-to-End Tests (20% of coverage)
- Full workflow execution
- User-facing SDK
- Real-world scenarios
- Performance benchmarks

**Coverage targets**:
- SDK: 85%
- Example workflows: 100%

---

## Development Workflows

### Daily Development
```bash
# Start services
make dev-up

# Run tests in watch mode
make test-watch

# Run linting
make lint

# Format code
make format

# Type check
make typecheck

# Stop services
make dev-down
```

### Common Makefile Targets
```makefile
.PHONY: dev-up dev-down test lint format typecheck

dev-up:
    docker compose up -d

dev-down:
    docker compose down

test:
    poetry run pytest -v --cov=wflo --cov-report=html

test-watch:
    poetry run ptw -- -v --cov=wflo

lint:
    poetry run ruff check src/ tests/

format:
    poetry run black src/ tests/
    poetry run ruff check --fix src/ tests/

typecheck:
    poetry run mypy src/

migrate:
    poetry run alembic upgrade head

migration:
    poetry run alembic revision --autogenerate -m "$(msg)"
```

---

## Code Quality Standards

### Type Hints
- **Required**: All function signatures must have type hints
- **Strictness**: mypy strict mode enforced
- **Example**:
  ```python
  async def execute_workflow(
      workflow_id: str,
      inputs: dict[str, Any],
      *,
      budget: float | None = None,
  ) -> WorkflowExecution:
      ...
  ```

### Docstrings
- **Format**: Google-style docstrings
- **Required for**: All public APIs
- **Example**:
  ```python
  async def execute_workflow(workflow_id: str) -> WorkflowExecution:
      """Execute a workflow by ID.

      Args:
          workflow_id: Unique identifier for the workflow

      Returns:
          WorkflowExecution containing results and status

      Raises:
          WorkflowNotFoundError: If workflow doesn't exist
          BudgetExceededError: If execution exceeds budget
      """
  ```

### Testing
- **Coverage**: 80% minimum, 90% target
- **Naming**: `test_<functionality>_<scenario>`
- **Structure**: Arrange-Act-Assert pattern
- **Example**:
  ```python
  async def test_execute_workflow_success():
      # Arrange
      workflow = create_test_workflow()

      # Act
      result = await workflow_manager.execute(workflow.id)

      # Assert
      assert result.status == ExecutionStatus.COMPLETED
  ```

### Logging
- **Format**: Structured JSON via structlog
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Required fields**: correlation_id, workflow_id, execution_id
- **Example**:
  ```python
  logger.info(
      "workflow_started",
      workflow_id=workflow.id,
      execution_id=execution.id,
      user_id=user.id,
  )
  ```

---

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release preparation

### Commit Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Adding tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Examples**:
```
feat(workflow): add parallel step execution

Implement concurrent execution of independent workflow steps
using asyncio.gather() for improved performance.

Closes #123
```

```
fix(sandbox): prevent resource leak on container cleanup

Ensure all containers are properly removed even when
execution fails or times out.

Fixes #456
```

### Pull Request Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Ensure all tests pass locally
4. Run linting and type checking
5. Submit PR with description
6. Address review feedback
7. Squash and merge to `develop`

---

## Risk Management

### Technical Risks

**Risk**: Temporal learning curve
- **Mitigation**: Follow official examples, start simple
- **Fallback**: Custom DAG engine (less durable)

**Risk**: Docker performance on macOS
- **Mitigation**: Document known issues, use Linux for production
- **Fallback**: Native execution mode (less secure)

**Risk**: Kafka complexity for simple use cases
- **Mitigation**: Start with basic producer/consumer
- **Fallback**: Redis Streams for MVP

### Schedule Risks

**Risk**: Scope creep
- **Mitigation**: Strict Phase 1 boundaries, defer features
- **Impact**: Delays to Phase 2

**Risk**: Infrastructure debugging
- **Mitigation**: Allocate buffer time, use managed services
- **Impact**: Less time for features

---

## Success Metrics

### Performance Targets
- Workflow submission: < 100ms p99
- Sandbox creation: < 2s p99
- Step execution overhead: < 50ms
- Database queries: < 10ms p99

### Quality Targets
- Test coverage: > 80%
- Zero critical security vulnerabilities
- Documentation completeness: 100% of public APIs
- All examples working

### User Experience
- Can run example workflow in < 5 minutes
- Clear error messages
- Comprehensive logging
- Working Temporal UI integration

---

## Post-Phase 1: Phase 2 Planning

### Phase 2 Features (Weeks 11-20)
- Human approval gates (API + basic UI)
- Cost budget enforcement
- Policy engine (approval rules)
- Advanced OpenTelemetry tracing
- E2B code interpreter integration
- Rollback system (state restoration)

### Phase 3 Features (Weeks 21-30)
- REST API
- CLI tool
- Multi-agent orchestration
- Advanced observability dashboards
- Compliance features (audit logs, SOC2)
- TypeScript SDK

---

## Appendix: Dependencies Reference

See `plan/TECHNOLOGY_STACK.md` for complete dependency list and rationale.

### Key Dependencies
- **temporalio**: Workflow orchestration
- **confluent-kafka**: Event streaming
- **aiodocker**: Container management
- **asyncpg + sqlalchemy**: Database ORM
- **pydantic-settings**: Configuration
- **tokencost**: Cost tracking
- **structlog**: Structured logging
- **prometheus-client**: Metrics

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **ruff**: Linting
- **black**: Formatting
- **mypy**: Type checking

---

**Ready to build!** See `plan/TODO.md` for detailed task breakdown. 🚀
