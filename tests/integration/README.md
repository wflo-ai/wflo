# Integration Tests

Integration tests verify that Wflo components work correctly with external services (PostgreSQL, Redis, Kafka, Temporal, etc.).

## Prerequisites

### 1. Start Required Services

Start the required services using Docker Compose:

```bash
# Start all services
make dev-up

# Or start individual services
docker compose up -d postgres redis kafka temporal
```

### 2. Create Test Database

The tests use a separate test database to avoid interfering with development data:

```bash
# Connect to PostgreSQL and create test database
docker compose exec postgres psql -U wflo_user -d wflo -c "CREATE DATABASE wflo_test;"

# Or use the provided script
./scripts/setup_test_db.sh
```

### 3. Verify Temporal is Running

```bash
# Check Temporal server status
docker compose ps temporal

# Access Temporal Web UI
open http://localhost:8233  # macOS
xdg-open http://localhost:8233  # Linux
```

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with markers
pytest -m integration -v
```

### Run Specific Test Files

```bash
# Run database tests only
pytest tests/integration/test_database.py -v

# Run specific test class
pytest tests/integration/test_database.py::TestWorkflowDefinitionModel -v

# Run specific test
pytest tests/integration/test_database.py::TestWorkflowDefinitionModel::test_create_workflow_definition -v
```

### Run with Coverage

```bash
# Run integration tests with coverage
pytest tests/integration/ -v --cov=wflo --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Environment Variables

Integration tests use environment variables to configure connections:

```bash
# Set custom test database URL (optional)
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/wflo_test"

# Run tests
pytest tests/integration/ -v
```

Default test database URL:
```
postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test
```

## Test Organization

Integration tests are organized by component:

- `test_database.py` - Database engine, ORM models, CRUD operations (15 tests)
- `test_temporal.py` - Temporal workflows and activities (10+ tests)
- `test_sandbox.py` - Sandboxed code execution with Docker (30+ tests)
- `test_cost_tracking.py` - Cost tracking and budget management (11 tests)
- `test_redis.py` - Redis caching and distributed locks (20+ tests)
- `test_kafka.py` - Kafka producers and consumers (TODO)

### Test Files

#### test_database.py (15 tests)
Tests database operations without requiring Temporal:
- Database connectivity
- Workflow definition CRUD
- Execution tracking
- State snapshots
- Approval requests

```bash
# Run database tests only
pytest tests/integration/test_database.py -v
```

#### test_temporal.py (10+ tests)
Tests Temporal workflows and activities:
- SimpleWorkflow execution
- CodeExecutionWorkflow with sandboxing
- WfloWorkflow with database integration
- Activity execution
- Workflow retries and cancellation

```bash
# Run Temporal tests only
pytest tests/integration/test_temporal.py -v

# Skip slow Temporal tests
pytest tests/integration/ -v -m "not slow"
```

#### test_sandbox.py (30+ tests)
Tests sandboxed code execution with Docker:
- Basic code execution (Python)
- Error handling (syntax, runtime, import errors)
- Timeout enforcement
- Resource limits (CPU, memory)
- Network isolation
- Container cleanup
- Security features (non-root user, filesystem isolation)
- Edge cases (empty code, Unicode, large output)

```bash
# Run sandbox tests only
pytest tests/integration/test_sandbox.py -v

# Run specific test class
pytest tests/integration/test_sandbox.py::TestSandboxBasicExecution -v

# Skip slow sandbox tests
pytest tests/integration/test_sandbox.py -v -m "not slow"
```

**Note:** Sandbox tests require Docker daemon to be running and accessible.

#### test_cost_tracking.py (11 tests)
Tests cost tracking and budget management:
- Cost calculation for different LLM models (GPT-4, GPT-3.5, Claude)
- Token counting and cost estimation
- Database cost tracking and aggregation
- Budget checking and enforcement
- Multi-call cost accumulation

```bash
# Run cost tracking tests only
pytest tests/integration/test_cost_tracking.py -v

# Run specific test class
pytest tests/integration/test_cost_tracking.py::TestCostTracker -v
pytest tests/integration/test_cost_tracking.py::TestBudgetCheck -v
```

**Test Classes**:
- `TestCostTracker` (6 tests) - Cost calculation and database tracking
- `TestBudgetCheck` (3 tests) - Budget limit enforcement
- `TestCostEstimation` (2 tests) - Cost estimation before execution

#### test_redis.py (20+ tests)
Tests Redis caching and distributed locking:
- Redis client connection and health checks
- Basic operations (set, get, delete, expiration)
- Distributed lock acquisition and release
- Lock auto-renewal for long operations
- Concurrent lock prevention
- LLM response caching (cache hits/misses)
- Cache expiration and invalidation

```bash
# Run Redis tests only
pytest tests/integration/test_redis.py -v

# Run specific test class
pytest tests/integration/test_redis.py::TestRedisClient -v
pytest tests/integration/test_redis.py::TestDistributedLock -v
pytest tests/integration/test_redis.py::TestLLMCache -v
```

**Test Classes**:
- `TestRedisClient` (3 tests) - Redis connection and basic operations
- `TestDistributedLock` (9 tests) - Distributed locking functionality
- `TestLLMCache` (8 tests) - LLM response caching

**Note:** Redis tests require Redis to be running via docker-compose.

## Debugging Integration Tests

### Enable SQL Logging

Set `database_echo=True` in the test settings fixture:

```python
# In tests/conftest.py
@pytest.fixture(scope="session")
def test_settings(test_db_url: str) -> Settings:
    return Settings(
        app_env="testing",
        database_url=test_db_url,
        database_echo=True,  # Enable SQL logging
    )
```

### Run Single Test with Print Statements

```bash
pytest tests/integration/test_database.py::TestWorkflowDefinitionModel::test_create_workflow_definition -v -s
```

The `-s` flag shows print statements and logging output.

### Check Database State

```bash
# Connect to test database
docker compose exec postgres psql -U wflo_user -d wflo_test

# List tables
\dt

# Query tables
SELECT * FROM workflow_definitions;
SELECT * FROM workflow_executions;
```

## CI/CD Integration

Integration tests are configured to run in GitHub Actions:

```yaml
# .github/workflows/ci.yml
- name: Run integration tests
  run: |
    docker compose up -d postgres redis kafka temporal
    pytest tests/integration/ -v
  env:
    TEST_DATABASE_URL: postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test
```

## Troubleshooting

### Database Connection Refused

**Problem**: `ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 5432)`

**Solution**:
1. Ensure PostgreSQL is running: `docker compose ps postgres`
2. Check PostgreSQL logs: `docker compose logs postgres`
3. Verify port is exposed: `docker compose port postgres 5432`

### Test Database Does Not Exist

**Problem**: `database "wflo_test" does not exist`

**Solution**:
```bash
docker compose exec postgres createdb -U wflo_user wflo_test
```

### Permission Denied

**Problem**: `permission denied for database wflo_test`

**Solution**:
```bash
docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE wflo_test TO wflo_user;"
```

### Tables Already Exist

**Problem**: Tests fail because tables already exist

**Solution**: The test fixtures automatically create and drop tables for each test. If you see this error, manually drop the test database:

```bash
docker compose exec postgres dropdb -U wflo_user wflo_test
docker compose exec postgres createdb -U wflo_user wflo_test
```

## Test Data Cleanup

Integration test fixtures automatically clean up test data:

- **Function scope**: Tables are created before each test and dropped after each test
- **Session scope**: Database connection is shared across all tests in a session
- **No manual cleanup needed**: Fixtures handle all cleanup automatically

## Performance

Integration tests are slower than unit tests:

- **Unit tests**: < 1 second (no external dependencies)
- **Integration tests**: 5-30 seconds (require database connections)
- **E2E tests**: 1-5 minutes (full workflow execution)

To skip slow tests:

```bash
# Skip integration tests (run unit tests only)
pytest -m "not integration" -v

# Run only unit tests
pytest tests/unit/ -v
```
