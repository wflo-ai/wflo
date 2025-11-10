# Testing Guide

Quick reference for running tests in Wflo.

## Quick Start

```bash
# 1. Verify setup
./scripts/verify_setup.sh

# 2. Run integration tests
./scripts/run_tests.sh integration

# 3. View results
```

## Test Organization

### Integration Tests (100+ tests)

| Test File | Tests | Requirements | Description |
|-----------|-------|--------------|-------------|
| **test_database.py** | 15 | PostgreSQL | Database engine, ORM models, CRUD operations |
| **test_redis.py** | 20+ | Redis | Distributed locks, LLM caching, connection pooling |
| **test_kafka.py** | 20+ | Kafka + Zookeeper | Event streaming, producer/consumer, topics |
| **test_temporal.py** | 10+ | Temporal + PostgreSQL | Workflows, activities, execution |
| **test_sandbox.py** | 30+ | Docker | Code execution, resource limits, security |
| **test_cost_tracking.py** | 11 | PostgreSQL | Cost calculation, budget enforcement |

### Unit Tests

Located in `tests/unit/` - Run without Docker dependencies.

## Running Tests Locally

### Prerequisites

Ensure Docker services are running:

```bash
# Start all services
docker-compose up -d

# Verify services are healthy (wait 30-60 seconds)
docker-compose ps

# Expected output: All services show "Up (healthy)"
```

### Run All Integration Tests

```bash
# Using test runner script (recommended)
./scripts/run_tests.sh integration

# Or directly with pytest
poetry run pytest tests/integration/ -v

# Expected: 100+ tests pass in 45-60 seconds
```

### Run Specific Test Files

#### Database Tests
```bash
poetry run pytest tests/integration/test_database.py -v

# Expected: 15 passed
# Tests: workflow CRUD, executions, state snapshots, approvals
```

#### Redis Tests
```bash
poetry run pytest tests/integration/test_redis.py -v

# Expected: 20+ passed
# Tests: client connection, distributed locks, LLM cache, auto-renewal
```

#### Kafka Tests
```bash
poetry run pytest tests/integration/test_kafka.py -v

# Expected: 17+ passed
# Tests: producer, consumer, event schemas, topics, serialization
```

#### Temporal Tests
```bash
poetry run pytest tests/integration/test_temporal.py -v

# Expected: 10+ passed
# Tests: workflow execution, activities, retries, cancellation
```

#### Sandbox Tests
```bash
poetry run pytest tests/integration/test_sandbox.py -v

# Expected: 30+ passed
# Tests: code execution, timeouts, resource limits, security
```

#### Cost Tracking Tests
```bash
poetry run pytest tests/integration/test_cost_tracking.py -v

# Expected: 11 passed
# Tests: cost calculation, budget checks, multi-model support
```

### Run Specific Test Classes

```bash
# Redis: Test only distributed locks
poetry run pytest tests/integration/test_redis.py::TestDistributedLock -v

# Kafka: Test only producer functionality
poetry run pytest tests/integration/test_kafka.py::TestKafkaProducer -v

# Cost: Test only budget enforcement
poetry run pytest tests/integration/test_cost_tracking.py::TestBudgetCheck -v
```

### Run Specific Test Methods

```bash
# Single test
poetry run pytest tests/integration/test_redis.py::TestDistributedLock::test_lock_auto_renewal -v

# Multiple tests with pattern
poetry run pytest tests/integration/ -k "cache" -v
```

### Run with Coverage

```bash
# Generate HTML coverage report
poetry run pytest tests/integration/ --cov=wflo --cov-report=html -v

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Expected: 80%+ coverage
```

### Run with Different Verbosity

```bash
# Minimal output
poetry run pytest tests/integration/ -q

# Standard output
poetry run pytest tests/integration/ -v

# Detailed output with print statements
poetry run pytest tests/integration/ -vv -s

# Show only test names
poetry run pytest tests/integration/ --collect-only
```

## Test Results Reference

### Expected Success Output

```
tests/integration/test_database.py::TestWorkflowDefinitionModel::test_create_workflow_definition PASSED
tests/integration/test_database.py::TestWorkflowDefinitionModel::test_read_workflow_definition PASSED
tests/integration/test_database.py::TestWorkflowDefinitionModel::test_update_workflow_definition PASSED
...
tests/integration/test_redis.py::TestRedisClient::test_redis_health_check PASSED
tests/integration/test_redis.py::TestDistributedLock::test_lock_acquisition_and_release PASSED
tests/integration/test_redis.py::TestLLMCache::test_cache_get_or_compute PASSED
...
tests/integration/test_kafka.py::TestKafkaProducer::test_send_workflow_event PASSED
tests/integration/test_kafka.py::TestKafkaConsumer::test_produce_and_consume PASSED
...

======================== 100+ passed in 45.23s =========================
```

### Key Metrics Being Tested

**Redis Tests:**
- ✅ Connection pooling and health checks
- ✅ Distributed lock acquisition/release
- ✅ Lock auto-renewal for long operations
- ✅ Concurrent lock prevention
- ✅ LLM cache hit/miss rates
- ✅ Cache expiration and invalidation

**Kafka Tests:**
- ✅ Producer idempotent delivery
- ✅ Consumer group coordination
- ✅ Event serialization/deserialization
- ✅ Topic creation and management
- ✅ End-to-end message flow
- ✅ Schema validation (WorkflowEvent, CostEvent, etc.)

**Cost Tracking Tests:**
- ✅ Cost calculation for GPT-4, Claude, Gemini
- ✅ Token counting accuracy
- ✅ Budget enforcement (50%, 75%, 90%, 100%)
- ✅ Multi-model support (400+ models)
- ✅ Database persistence

## Troubleshooting Tests

### Tests Fail with Connection Error

**Problem**: `ConnectionRefusedError` or `asyncpg.exceptions.CannotConnectNowError`

**Solution**:
```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose restart

# Wait for health checks (30-60 seconds)
sleep 30

# Verify connections
./scripts/verify_setup.sh

# Run tests again
./scripts/run_tests.sh integration
```

### Redis Tests Timeout

**Problem**: `asyncio.TimeoutError` in test_redis.py

**Solution**:
```bash
# Check Redis status
docker-compose ps redis
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Test connection
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Kafka Tests Fail

**Problem**: `confluent_kafka.KafkaException` or consumer timeout

**Solution**:
```bash
# Kafka depends on Zookeeper - check both
docker-compose ps zookeeper kafka

# Restart Kafka stack
docker-compose restart zookeeper
sleep 10
docker-compose restart kafka
sleep 20

# Verify Kafka is ready
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Run tests again
poetry run pytest tests/integration/test_kafka.py -v
```

### Sandbox Tests Fail

**Problem**: Docker-in-Docker issues or container errors

**Solution**:
```bash
# Ensure Docker daemon is running
docker ps

# Check Docker socket permissions
ls -la /var/run/docker.sock

# Pull required images
docker pull python:3.11-slim

# Run tests with more verbose output
poetry run pytest tests/integration/test_sandbox.py -vv -s
```

### Database Tests Fail

**Problem**: Table doesn't exist or migration errors

**Solution**:
```bash
# Check if migrations are applied
docker-compose exec postgres psql -U wflo_user -d wflo -c "\dt"

# Run migrations
poetry run alembic upgrade head

# Verify tables exist
docker-compose exec postgres psql -U wflo_user -d wflo -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'public';
"

# Run tests again
poetry run pytest tests/integration/test_database.py -v
```

## Continuous Integration

### Running Tests in CI/CD

```yaml
# Example GitHub Actions workflow
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -

      - name: Install dependencies
        run: poetry install

      - name: Start Docker services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 30

      - name: Run migrations
        run: poetry run alembic upgrade head

      - name: Run integration tests
        run: poetry run pytest tests/integration/ -v --cov=wflo

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Performance Benchmarks

Typical test execution times on modern hardware:

| Test Suite | Duration | CPU | Memory |
|------------|----------|-----|--------|
| Unit tests | < 5s | Low | < 100MB |
| Database tests | 5-10s | Low | < 200MB |
| Redis tests | 10-15s | Low | < 150MB |
| Kafka tests | 15-25s | Medium | < 300MB |
| Temporal tests | 20-30s | Medium | < 500MB |
| Sandbox tests | 30-60s | High | < 1GB |
| **All integration** | **45-90s** | **Medium** | **< 2GB** |

## Best Practices

### Before Running Tests

1. ✅ Ensure Docker services are healthy
2. ✅ Run `./scripts/verify_setup.sh`
3. ✅ Check disk space (at least 5GB free)
4. ✅ Close resource-intensive applications

### During Test Development

1. ✅ Run specific test file first
2. ✅ Use `-s` flag to see print statements
3. ✅ Add `--tb=short` for concise tracebacks
4. ✅ Use `--pdb` to debug on failure

### After Tests Pass

1. ✅ Check coverage report
2. ✅ Review test output for warnings
3. ✅ Commit passing tests
4. ✅ Update documentation if needed

## Quick Reference Commands

```bash
# Verify setup
./scripts/verify_setup.sh

# Run all integration tests
./scripts/run_tests.sh integration

# Run specific test file
poetry run pytest tests/integration/test_redis.py -v

# Run with coverage
poetry run pytest tests/integration/ --cov=wflo --cov-report=html

# Debug failing test
poetry run pytest tests/integration/test_kafka.py::TestKafkaProducer::test_send_workflow_event -vv -s --pdb

# Run tests matching pattern
poetry run pytest tests/integration/ -k "cache or lock" -v

# List all tests without running
poetry run pytest tests/integration/ --collect-only

# Run tests in parallel (faster)
poetry run pytest tests/integration/ -n auto
```

## Need Help?

- **Documentation**: See `GETTING_STARTED.md`
- **Setup Issues**: Run `./scripts/verify_setup.sh`
- **Test Failures**: Check service logs with `docker-compose logs <service>`
- **Questions**: Open an issue on GitHub

---

**Pro Tip**: Run `./scripts/verify_setup.sh` before every test session to catch issues early!
