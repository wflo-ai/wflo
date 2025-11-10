# Getting Started with Wflo

This guide will walk you through setting up Wflo locally and running your first workflow.

## Prerequisites

### Required Software

- **Docker Desktop** (v24.0+) - For running infrastructure services
- **Python 3.11 or 3.12** - ⚠️ **NOT Python 3.13** (asyncpg incompatibility)
- **Poetry** - Python dependency manager

### Install Prerequisites

#### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

# Install Docker Desktop
brew install --cask docker
# Start Docker Desktop from Applications
```

#### Linux (Ubuntu/Debian)

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows

```powershell
# Install Python 3.11
# Download from: https://www.python.org/downloads/release/python-3118/

# Install Poetry (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/
```

### Python 3.13 Compatibility Issue

**If you have Python 3.13 installed**, you need to switch to Python 3.11 or 3.12 because the `asyncpg` library (used for PostgreSQL) doesn't support Python 3.13 yet.

```bash
# Check your Python version
python3 --version

# If it shows Python 3.13.x, install Python 3.11:

# macOS
brew install python@3.11

# Linux
sudo apt install python3.11

# Configure Poetry to use Python 3.11
poetry env use python3.11
poetry env info  # Verify it's using 3.11

# Verify
poetry run python --version  # Should output: Python 3.11.x
```

**Why not Python 3.13?**
Python 3.13 introduced breaking C API changes that affect `asyncpg` (a Cython-based PostgreSQL driver). Until asyncpg releases Python 3.13 support, use Python 3.11 or 3.12.

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/wflo-ai/wflo.git
cd wflo
```

### Step 2: Install Python Dependencies

```bash
# Ensure you're using Python 3.11 or 3.12
poetry env use python3.11  # or python3.12

# Install all dependencies
poetry install

# This will install:
# - Temporal SDK for workflow orchestration
# - SQLAlchemy for database ORM
# - Redis client for caching
# - Kafka client for event streaming
# - OpenTelemetry for observability
# - tokencost for LLM cost tracking
# - And 40+ other dependencies
```

Expected output:
```
Installing dependencies from lock file

Package operations: 50+ installs, 0 updates, 0 removals

  • Installing ...

Writing lock file

Installing the current project: wflo (0.1.0)
```

### Step 3: Start Infrastructure Services

```bash
# Start all Docker services in detached mode
docker compose up -d

# Services starting:
# - PostgreSQL (database)
# - Redis (caching & locks)
# - Kafka + Zookeeper (event streaming)
# - Temporal (workflow engine)
# - Temporal Web UI
# - Jaeger (tracing)
```

**Wait 30-60 seconds** for services to fully initialize, especially Temporal which needs to run database migrations.

**Verify services are running:**
```bash
docker compose ps

# Expected output (all should show "Up" or "Up (healthy)"):
# wflo-postgres      Up (healthy)
# wflo-redis         Up (healthy)
# wflo-kafka         Up (healthy)
# wflo-zookeeper     Up (healthy)
# wflo-temporal      Up (healthy)
# wflo-temporal-web  Up
# wflo-jaeger        Up
```

**Troubleshooting:**
- If Temporal shows as "Up" but not "(healthy)", wait another 30 seconds
- Check logs: `docker compose logs temporal`
- If services fail to start: `docker compose down && docker compose up -d`

### Step 4: Initialize Database

```bash
# Run Alembic migrations to create database schema
poetry run alembic upgrade head

# This creates tables for:
# - workflow_definitions
# - workflow_executions
# - workflow_history
# - task_metadata
# - sandbox_configurations
# - cost_tracking
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_add_cost_tracking
...
```

### Step 5: Verify Setup

```bash
# Run the comprehensive verification script
./scripts/verify_setup.sh
```

This checks:
- ✅ Prerequisites (Python, Poetry, Docker)
- ✅ Docker services are running
- ✅ Service connections (PostgreSQL, Redis, Kafka, Temporal)
- ✅ Python environment and dependencies
- ✅ Database tables exist
- ✅ Test suite is available

Expected output:
```
🔍 Wflo Setup Verification
==========================

📋 Checking Prerequisites...
✓ Python 3 installed: 3.11.x
✓ Poetry installed: 1.x.x
✓ Docker installed: 24.x.x
✓ Docker Compose available

🐳 Checking Docker Services...
✓ postgres is running
✓ redis is running
✓ kafka is running
✓ zookeeper is running
✓ temporal is running

🔌 Testing Service Connections...
✓ PostgreSQL connection OK
✓ Redis connection OK
✓ Kafka connection OK
✓ Temporal connection OK

🐍 Checking Python Environment...
✓ Poetry virtual environment exists
✓ Wflo package installed
✓ All dependencies installed

🗄️  Checking Database...
✓ Alembic configuration found
✓ Database tables exist

📊 Setup Summary
================
✓ All infrastructure services are running

✨ Ready to develop!
```

### Step 6: Run Tests

```bash
# Run all integration tests (requires Docker services)
./scripts/run_tests.sh integration

# This runs 100+ tests covering:
# - Database operations (15 tests)
# - Redis caching and locks (20+ tests)
# - Kafka event streaming (20+ tests)
# - Cost tracking (11 tests)
# - Temporal workflows (10+ tests)
# - Sandbox execution (30+ tests)
```

**All tests should pass.** If any fail:
1. Check Docker services: `docker compose ps`
2. Check logs: `docker compose logs <service-name>`
3. Restart services: `docker compose restart`

## Running Your First Workflow

### Terminal 1: Start Temporal Worker

```bash
# The worker processes workflow tasks
poetry run python -m wflo.temporal.worker
```

Expected output:
```
INFO:wflo.temporal.worker:Starting Temporal worker
INFO:wflo.temporal.worker:Connecting to Temporal at localhost:7233
INFO:wflo.temporal.worker:Worker started for task queue: wflo-task-queue
```

### Terminal 2: Execute a Workflow

```bash
# Run a simple example workflow
poetry run python examples/simple_workflow.py
```

The workflow will:
1. Execute in an isolated sandbox
2. Track costs automatically
3. Log all operations with structured logging
4. Create distributed traces in Jaeger
5. Emit events to Kafka

### View Workflow Execution

**Temporal Web UI:**
- Open: http://localhost:8233
- Navigate to "Workflows" to see execution history
- Click on a workflow to see detailed execution logs

**Jaeger Tracing UI:**
- Open: http://localhost:16686
- Select "wflo" service from dropdown
- View distributed traces across workflow activities

## Next Steps

### Explore the Codebase

```
wflo/
├── wflo/
│   ├── config.py              # Configuration management
│   ├── cost/                  # Cost tracking (tokencost integration)
│   ├── observability/         # Logging, tracing, metrics
│   ├── cache/                 # Redis caching & distributed locks
│   ├── events/                # Kafka event streaming
│   ├── database/              # SQLAlchemy models and ORM
│   ├── temporal/              # Workflow definitions
│   └── sandbox/               # Code execution sandboxes
├── tests/
│   ├── unit/                  # Unit tests (no Docker required)
│   └── integration/           # Integration tests (requires Docker)
├── scripts/                   # Utility scripts
└── examples/                  # Example workflows
```

### Read the Documentation

- **[README.md](README.md)** - Project overview and architecture
- **[TESTING.md](TESTING.md)** - Comprehensive testing guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Development Workflow

```bash
# 1. Start infrastructure (once)
docker compose up -d

# 2. Make code changes
# ... edit files ...

# 3. Run tests
poetry run pytest tests/unit/ -v                    # Unit tests (fast)
poetry run pytest tests/integration/test_X.py -v    # Specific integration test

# 4. Run the worker and test your workflow
poetry run python -m wflo.temporal.worker           # Terminal 1
poetry run python examples/your_workflow.py         # Terminal 2

# 5. Check traces and logs
# - Jaeger: http://localhost:16686
# - Temporal UI: http://localhost:8233

# 6. Stop services when done
docker compose down
```

## Troubleshooting

### Issue: `poetry install` fails with asyncpg compilation error

**Cause:** Using Python 3.13 (not supported)

**Solution:**
```bash
poetry env use python3.11
poetry install
```

### Issue: Temporal service won't start

**Check logs:**
```bash
docker compose logs temporal
```

**Common fixes:**
```bash
# Remove and recreate container
docker compose stop temporal
docker compose rm -f temporal
docker compose up -d temporal

# Wait 30 seconds, then verify
docker compose exec temporal tctl --address temporal:7233 cluster health
```

### Issue: Database tables not found

**Run migrations:**
```bash
poetry run alembic upgrade head
```

### Issue: Tests failing

**Ensure services are healthy:**
```bash
docker compose ps  # All should show "Up (healthy)"
./scripts/verify_setup.sh
```

**Restart services:**
```bash
docker compose restart
sleep 30
./scripts/run_tests.sh integration
```

### Issue: Port already in use

**Check what's using the port:**
```bash
# PostgreSQL (5432)
lsof -i :5432

# Redis (6379)
lsof -i :6379

# Temporal (7233)
lsof -i :7233
```

**Solution:** Stop the conflicting service or change ports in `docker-compose.yml`

## Getting Help

- **GitHub Issues**: [https://github.com/wflo-ai/wflo/issues](https://github.com/wflo-ai/wflo/issues)
- **GitHub Discussions**: [https://github.com/wflo-ai/wflo/discussions](https://github.com/wflo-ai/wflo/discussions)
- **Documentation**: [README.md](README.md), [TESTING.md](TESTING.md)

---

**You're all set!** 🎉 Start building secure AI agent workflows with Wflo.
