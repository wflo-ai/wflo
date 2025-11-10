# Testing Guide

This document describes the testing strategy and how to run tests for Wflo.

## Test Structure

```
tests/
├── unit/                  # Unit tests (no external dependencies)
│   ├── test_settings.py
│   ├── test_workflow_models.py
│   ├── test_execution_models.py
│   └── test_database_engine.py
├── integration/           # Integration tests (requires Docker services)
│   ├── README.md
│   └── test_database.py
├── e2e/                   # End-to-end tests (full workflow execution)
└── conftest.py           # Shared fixtures
```

## Test Categories

### Unit Tests
- **No external dependencies** - all I/O is mocked
- **Fast execution** - typically < 1 second
- **Test individual functions and classes**
- **Run frequently during development**

Coverage targets:
- Models: 100%
- Utilities: 90%
- Managers: 90%

### Integration Tests
- **Require Docker services** (PostgreSQL, Redis, Kafka, Temporal)
- **Test component interactions**
- **Slower execution** - typically 5-30 seconds
- **Run before commits and in CI/CD**

Coverage targets:
- Database layer: 90%
- Temporal integration: 80%
- Kafka integration: 80%

### End-to-End Tests
- **Full workflow execution**
- **Test user-facing functionality**
- **Slowest execution** - typically 1-5 minutes
- **Run before releases**

Coverage targets:
- SDK: 85%
- Example workflows: 100%

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
poetry install
```

2. For integration/e2e tests, start services:
```bash
make dev-up
```

### Quick Commands

```bash
# Run all tests
make test

# Run unit tests only (fast)
make test-unit

# Run integration tests
make test-integration

# Run with coverage
make test

# Run in watch mode (during development)
make test-watch
```

### Detailed Commands

#### Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_workflow_models.py -v

# Specific test class
pytest tests/unit/test_workflow_models.py::TestWorkflowDefinition -v

# Specific test
pytest tests/unit/test_workflow_models.py::TestWorkflowDefinition::test_validate_dag -v

# With coverage
pytest tests/unit/ -v --cov=wflo --cov-report=html
```

#### Integration Tests

Integration tests require a test database. Use the helper scripts:

```bash
# Setup test database
make test-integration-setup
# or
./scripts/setup_test_db.sh

# Run integration tests
make test-integration

# Run with setup (one command)
make test-integration-full

# Cleanup test database
make test-integration-clean
```

Manual setup:
```bash
# Start PostgreSQL
docker compose up -d postgres

# Create test database
docker compose exec postgres createdb -U wflo_user wflo_test

# Run migrations
DATABASE_URL="postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test" \
  poetry run alembic upgrade head

# Run tests
TEST_DATABASE_URL="postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test" \
  pytest tests/integration/ -v
```

#### End-to-End Tests

```bash
# Run all e2e tests
make test-e2e

# Run specific e2e test
pytest tests/e2e/test_simple_workflow.py -v
```

### Test Markers

Tests are marked with pytest markers:

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run only e2e tests
pytest -m e2e -v

# Run only slow tests
pytest -m slow -v

# Skip slow tests
pytest -m "not slow" -v

# Skip integration and e2e tests
pytest -m "not integration and not e2e" -v
```

## Writing Tests

### Unit Test Example

```python
import pytest
from wflo.models.workflow import WorkflowDefinition, WorkflowStep

class TestWorkflowDefinition:
    """Unit tests for WorkflowDefinition."""

    def test_create_workflow(self):
        """Test creating a basic workflow."""
        workflow = WorkflowDefinition(
            name="test-workflow",
            steps=[
                WorkflowStep(id="step1", type="AGENT"),
            ],
            policies={"max_cost_usd": 10.0},
        )

        assert workflow.name == "test-workflow"
        assert len(workflow.steps) == 1
```

### Integration Test Example

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from wflo.db.models import WorkflowDefinitionModel

@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowDatabase:
    """Integration tests for workflow database operations."""

    async def test_create_workflow(self, db_session: AsyncSession):
        """Test creating a workflow in the database."""
        workflow = WorkflowDefinitionModel(
            id="test-123",
            name="test-workflow",
            steps=[],
            policies={},
        )

        db_session.add(workflow)
        await db_session.commit()

        assert workflow.id == "test-123"
```

### Using Fixtures

```python
# Use db_session fixture for database tests
async def test_with_database(db_session: AsyncSession):
    # db_session automatically creates and drops tables
    result = await db_session.execute(select(WorkflowDefinition))
    workflows = result.scalars().all()
    assert len(workflows) == 0

# Use sample fixtures
def test_with_sample_data(sample_workflow_id: str):
    assert sample_workflow_id == "test-workflow-123"
```

## Coverage

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=wflo --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Requirements

- **Minimum**: 80% (enforced by pytest-cov)
- **Target**: 90%
- **Critical paths**: 100%

Coverage configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=wflo",
    "--cov-report=html",
    "--cov-fail-under=80",
]

[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
]
```

## CI/CD Integration

Tests run automatically in GitHub Actions:

```yaml
# .github/workflows/ci.yml
- name: Run unit tests
  run: poetry run pytest tests/unit/ -v

- name: Run integration tests
  run: |
    docker compose up -d postgres redis
    ./scripts/setup_test_db.sh
    poetry run pytest tests/integration/ -v
```

## Debugging Tests

### Enable SQL Logging

Set `database_echo=True` in test settings:

```python
# In tests/conftest.py
@pytest.fixture(scope="session")
def test_settings(test_db_url: str) -> Settings:
    return Settings(
        database_url=test_db_url,
        database_echo=True,  # Enable SQL logging
    )
```

### Show Print Statements

```bash
pytest tests/integration/test_database.py -v -s
```

The `-s` flag disables output capture.

### Run with Debug Logging

```bash
pytest tests/integration/ -v --log-cli-level=DEBUG
```

### Drop into Debugger on Failure

```bash
pytest tests/integration/ -v --pdb
```

### Inspect Database State

```bash
# Connect to test database
docker compose exec postgres psql -U wflo_user -d wflo_test

# List tables
\dt

# Query tables
SELECT * FROM workflow_definitions;
```

## Troubleshooting

### Database Connection Refused

**Problem**: `ConnectionRefusedError: [Errno 111] Connect call failed`

**Solutions**:
1. Ensure PostgreSQL is running: `docker compose ps postgres`
2. Check logs: `docker compose logs postgres`
3. Verify port: `docker compose port postgres 5432`

### Test Database Does Not Exist

**Problem**: `database "wflo_test" does not exist`

**Solution**:
```bash
./scripts/setup_test_db.sh
```

### Tests Fail with "Table Already Exists"

**Problem**: Tables already exist from previous run

**Solution**:
```bash
./scripts/cleanup_test_db.sh
./scripts/setup_test_db.sh
```

### Slow Tests

**Problem**: Tests take too long

**Solutions**:
1. Run unit tests only: `pytest tests/unit/ -v`
2. Run without coverage: `pytest -v --no-cov`
3. Run specific test: `pytest tests/unit/test_models.py::test_specific -v`
4. Use parallel execution: `pytest -n auto` (requires pytest-xdist)

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'wflo'`

**Solution**:
```bash
# Install package in editable mode
poetry install

# Or activate virtual environment
poetry shell
```

## Best Practices

1. **Write tests first** - Test-driven development (TDD)
2. **One assertion per test** - Keep tests focused
3. **Use descriptive test names** - `test_create_workflow_with_invalid_dag_raises_error`
4. **Mock external dependencies** in unit tests
5. **Use fixtures** - Avoid code duplication
6. **Clean up after tests** - Use fixtures for automatic cleanup
7. **Test edge cases** - Not just happy paths
8. **Keep tests fast** - Unit tests should be < 1 second
9. **Isolate tests** - Tests should not depend on each other
10. **Test behavior, not implementation** - Focus on outcomes

## Performance Tips

1. **Use session-scoped fixtures** for expensive setup
2. **Reuse database connections** when possible
3. **Mock slow operations** in unit tests
4. **Run tests in parallel**: `pytest -n auto`
5. **Skip slow tests** during development: `pytest -m "not slow"`
6. **Use `--lf`** to run last failed tests: `pytest --lf`
7. **Use `--ff`** to run failed first: `pytest --ff`

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Temporal Testing](https://docs.temporal.io/develop/python/testing-suite)
