# Getting Started with Wflo

This guide will walk you through setting up Wflo locally and running your first workflow.

## Prerequisites

### Required Software

- **Docker Desktop** (v24.0+)
- **Python** (3.11 or higher)
- **Poetry** (Python dependency manager)

### Install Prerequisites

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop
open -a Docker
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin
```

#### Windows
```powershell
# Install Python 3.11 from python.org
# Download from: https://www.python.org/downloads/

# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/wflo-ai/wflo.git
cd wflo
```

### 2. Install Python Dependencies

```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional)
nano .env
```

Default `.env` configuration:
```env
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Temporal
TEMPORAL_HOST=localhost:7233

# Observability
OPENTELEMETRY_ENABLED=true
OPENTELEMETRY_OTLP_ENDPOINT=localhost:4317
LOG_JSON_OUTPUT=false
```

## Starting Infrastructure Services

### 1. Start All Services

```bash
# Start PostgreSQL, Redis, Kafka, Temporal, and Jaeger
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

Expected output:
```
NAME                STATUS                   PORTS
wflo-postgres       Up (healthy)            0.0.0.0:5432->5432/tcp
wflo-redis          Up (healthy)            0.0.0.0:6379->6379/tcp
wflo-kafka          Up (healthy)            0.0.0.0:9092->9092/tcp
wflo-zookeeper      Up (healthy)            0.0.0.0:2181->2181/tcp
wflo-temporal       Up (healthy)            0.0.0.0:7233->7233/tcp
wflo-temporal-web   Up                      0.0.0.0:8233->8080/tcp
wflo-jaeger         Up                      0.0.0.0:16686->16686/tcp
```

### 2. Verify Services

```bash
# Test PostgreSQL
docker-compose exec postgres pg_isready -U wflo_user

# Test Redis
docker-compose exec redis redis-cli ping

# Test Kafka
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Test Temporal
docker-compose exec temporal tctl cluster health
```

### 3. View Service UIs

- **Temporal Web UI**: http://localhost:8233
- **Jaeger Tracing**: http://localhost:16686

## Database Setup

### 1. Run Migrations

```bash
# Apply database migrations
poetry run alembic upgrade head
```

### 2. Verify Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U wflo_user -d wflo

# List tables
\dt

# Expected tables:
# - workflow_definitions
# - workflow_executions
# - execution_steps
# - approval_requests
# - state_snapshots
# - cost_tracking

# Exit psql
\q
```

## Running Tests

### Unit Tests (No Docker Required)

```bash
# Run unit tests (fast, no external dependencies)
poetry run pytest tests/unit/ -v
```

### Integration Tests (Requires Docker)

```bash
# Ensure Docker services are running
docker-compose ps

# Run all integration tests
poetry run pytest tests/integration/ -v

# Run specific test files
poetry run pytest tests/integration/test_database.py -v
poetry run pytest tests/integration/test_redis.py -v
poetry run pytest tests/integration/test_kafka.py -v
poetry run pytest tests/integration/test_temporal.py -v
poetry run pytest tests/integration/test_sandbox.py -v
poetry run pytest tests/integration/test_cost_tracking.py -v

# Run with coverage
poetry run pytest tests/integration/ --cov=wflo --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Test Results Summary

After running integration tests, you should see:

```
tests/integration/test_database.py .............           [15 passed]
tests/integration/test_redis.py ....................       [20 passed]
tests/integration/test_kafka.py .................          [17 passed]
tests/integration/test_temporal.py ..........              [10 passed]
tests/integration/test_sandbox.py ........................ [30+ passed]
tests/integration/test_cost_tracking.py ...........        [11 passed]

======================== 100+ passed in 45.23s =========================
```

## Running Your First Workflow

### 1. Start Temporal Worker

```bash
# Terminal 1: Start the Temporal worker
poetry run python -m wflo.temporal.worker
```

You should see:
```
INFO:wflo.temporal.worker:Starting Temporal worker...
INFO:wflo.temporal.worker:Worker started on task queue: wflo-tasks
```

### 2. Execute a Workflow

```bash
# Terminal 2: Run example workflow
poetry run python examples/simple_workflow.py
```

### 3. View Workflow in Temporal UI

1. Open http://localhost:8233
2. Click on your workflow execution
3. View execution history, events, and results

## Monitoring & Observability

### Structured Logging

View logs with structured output:

```bash
# Follow Temporal worker logs
poetry run python -m wflo.temporal.worker

# Logs are in JSON format (production) or colored format (development)
```

Example log output:
```json
{
  "event": "workflow_started",
  "workflow_id": "data-pipeline",
  "execution_id": "exec-123",
  "timestamp": "2025-01-15T10:30:00Z",
  "trace_id": "550e8400e29b41d4a716446655440000",
  "span_id": "a716446655440000"
}
```

### Distributed Tracing

View traces in Jaeger UI:

1. Open http://localhost:16686
2. Select service: `wflo`
3. View traces for workflow executions
4. See database queries, Redis calls, Kafka messages

### Kafka Event Streaming

Monitor events in Kafka:

```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume workflow events
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic wflo.workflows \
  --from-beginning

# Consume cost events
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic wflo.costs \
  --from-beginning
```

### Redis Cache Monitoring

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View cached LLM responses
KEYS llm_cache:*

# View distributed locks
KEYS lock:*

# Monitor cache hit rate
INFO stats

# Exit Redis CLI
exit
```

## Common Tasks

### Reset Database

```bash
# Drop all tables and re-run migrations
docker-compose exec postgres psql -U wflo_user -d wflo -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
poetry run alembic upgrade head
```

### Clear Redis Cache

```bash
# Flush all Redis data
docker-compose exec redis redis-cli FLUSHALL
```

### View Kafka Topics

```bash
# Create topic manually
docker-compose exec kafka kafka-topics --create \
  --topic wflo.custom \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

# Describe topic
docker-compose exec kafka kafka-topics --describe \
  --topic wflo.workflows \
  --bootstrap-server localhost:9092
```

### Stop All Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (destroys data)
docker-compose down -v
```

## Troubleshooting

### Docker Services Won't Start

**Problem**: `Error response from daemon: Ports are not available`

**Solution**:
```bash
# Check what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9092  # Kafka

# Kill the process or change port in docker-compose.yml
```

### Database Connection Error

**Problem**: `asyncpg.exceptions.ConnectionDoesNotExistError`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Refused

**Problem**: `redis.exceptions.ConnectionError: Connection refused`

**Solution**:
```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Kafka Connection Error

**Problem**: `confluent_kafka.KafkaException: Failed to connect`

**Solution**:
```bash
# Kafka depends on Zookeeper - check both
docker-compose ps zookeeper kafka

# Restart Kafka stack
docker-compose restart zookeeper
docker-compose restart kafka
```

### Temporal Worker Won't Connect

**Problem**: `temporalio.service.RPCError: failed to dial`

**Solution**:
```bash
# Check Temporal health
docker-compose exec temporal tctl cluster health

# Restart Temporal
docker-compose restart temporal

# Wait 30 seconds for startup
sleep 30
```

### Integration Tests Fail

**Problem**: Tests fail with connection errors

**Solution**:
```bash
# Ensure all services are healthy
docker-compose ps

# Wait for health checks to pass
docker-compose up -d
sleep 30

# Run tests again
poetry run pytest tests/integration/ -v
```

## Next Steps

- **Read the Documentation**: Explore `/docs` for detailed guides
- **Try Example Workflows**: Check `/examples` directory
- **Explore the API**: Review code in `/src/wflo`
- **Join the Community**: GitHub Discussions and Discord

## Development Workflow

### Code Quality Checks

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# Run all checks
poetry run black src/ tests/ && poetry run ruff check src/ tests/ && poetry run mypy src/
```

### Creating Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Add new table"

# Review migration file in alembic/versions/

# Apply migration
poetry run alembic upgrade head
```

### Adding Dependencies

```bash
# Add runtime dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update lock file
poetry lock
```

## Additional Resources

- **Documentation**: https://docs.wflo.ai
- **GitHub**: https://github.com/wflo-ai/wflo
- **Issues**: https://github.com/wflo-ai/wflo/issues
- **Discussions**: https://github.com/wflo-ai/wflo/discussions

---

**Need Help?** Open an issue on GitHub or join our community discussions!
