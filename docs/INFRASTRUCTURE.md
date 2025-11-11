# Infrastructure Setup Guide

**Complete guide for setting up and managing Wflo's development infrastructure**

## Overview

Wflo uses Docker Compose to orchestrate 7 infrastructure services required for development and testing. This guide covers setup, verification, troubleshooting, and management of these services.

### Services Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│          (wflo Python code, tests, workflows)                │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↓ ↓
┌──────────────┬──────────────┬──────────────┬─────────────┐
│  PostgreSQL  │    Redis     │    Kafka     │  Temporal   │
│   :5432      │    :6379     │    :9092     │   :7233     │
└──────────────┴──────────────┴──────────────┴─────────────┘
                                    ↓
                            ┌──────────────┐
                            │  Zookeeper   │
                            │    :2181     │
                            └──────────────┘

┌──────────────┬──────────────┐
│ Temporal Web │    Jaeger    │
│   :8233      │   :16686     │
└──────────────┴──────────────┘
```

## Quick Start

```bash
# 1. Start all services
docker compose up -d

# 2. Verify all services are healthy (wait 30-60 seconds)
docker compose ps

# 3. Apply database migrations
poetry run alembic upgrade head

# 4. Create test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# 5. Verify setup
poetry run pytest tests/unit/ -v  # Should pass without infrastructure
# With infrastructure running:
poetry run pytest tests/integration/test_redis.py::TestRedisClient::test_redis_health_check -v
```

---

## Service Details

### 1. PostgreSQL - Database

**Purpose**: Stores workflow definitions, execution history, cost tracking, state snapshots, and approval requests.

**Container**: `wflo-postgres`
**Image**: `postgres:15-alpine`
**Port**: `5432`

#### Configuration

```yaml
Environment:
  POSTGRES_DB: wflo
  POSTGRES_USER: wflo_user
  POSTGRES_PASSWORD: wflo_password

Connection URL:
  postgresql://wflo_user:wflo_password@localhost:5432/wflo
```

#### Verify Setup

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Connect to database
docker compose exec postgres psql -U wflo_user -d wflo

# Inside psql:
\dt              # List tables
\q               # Quit

# Test connection from host
psql postgresql://wflo_user:wflo_password@localhost:5432/wflo -c "SELECT version();"
```

#### Create Test Database

```bash
# Create test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"

# Apply migrations to test database
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# Verify test database
docker compose exec -T postgres psql -U wflo_user -d wflo_test -c "\dt"
```

#### Common Issues

**Error**: `psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused`

**Solution**:
```bash
# Check if PostgreSQL container is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

**Error**: `FATAL: database "wflo_test" does not exist`

**Solution**:
```bash
# Create the test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
```

#### Reset Database

```bash
# Drop and recreate production database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "DROP DATABASE IF EXISTS wflo;"
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo;"
poetry run alembic upgrade head

# Drop and recreate test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "DROP DATABASE IF EXISTS wflo_test;"
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head
```

---

### 2. Redis - Caching & Locking

**Purpose**: Distributed locks for workflow deduplication, LLM response caching, session state.

**Container**: `wflo-redis`
**Image**: `redis:7-alpine`
**Port**: `6379`

#### Configuration

```yaml
Command: redis-server --appendonly yes
Persistence: AOF (Append-Only File) for durability

Connection URL:
  redis://localhost:6379/0
```

#### Verify Setup

```bash
# Check Redis is running
docker compose ps redis

# Test Redis CLI
docker compose exec redis redis-cli ping
# Expected: PONG

# Test from host
redis-cli -h localhost -p 6379 ping
# Or using Python
poetry run python -c "
import asyncio
from wflo.cache import check_redis_health
print('Redis healthy:', asyncio.run(check_redis_health()))
"
```

#### Monitor Redis

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Inside redis-cli:
INFO stats           # Statistics
DBSIZE               # Number of keys
KEYS lock:*          # List all locks
KEYS llm:cache:*     # List cached LLM responses
MONITOR              # Watch all commands in real-time (Ctrl+C to exit)
FLUSHALL             # ⚠️ Clear ALL data (use with caution)
```

#### Common Issues

**Error**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solution**:
```bash
# Check Redis container
docker compose ps redis
docker compose logs redis

# Restart Redis
docker compose restart redis
```

**Error**: `Event loop is closed` (in tests)

**Solution**: Already fixed with `reset_redis_pool` fixture in `tests/conftest.py`. If you see this, ensure you're using latest test code.

#### Reset Redis

```bash
# Clear all Redis data
docker compose exec redis redis-cli FLUSHALL

# Or restart container (preserves AOF data)
docker compose restart redis
```

---

### 3. Kafka - Event Streaming

**Purpose**: Event streaming for workflow events, cost tracking events, audit logs, real-time notifications.

**Container**: `wflo-kafka`
**Image**: `confluentinc/cp-kafka:7.5.0`
**Port**: `9092`
**Dependencies**: Requires Zookeeper

#### Configuration

```yaml
Broker ID: 1
Zookeeper: zookeeper:2181
Advertised Listeners: PLAINTEXT://localhost:9092
Auto Create Topics: Enabled

Connection:
  localhost:9092
```

#### Verify Setup

```bash
# Check Kafka is running and healthy
docker compose ps kafka

# List topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create test topic
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic test-topic \
  --partitions 1 \
  --replication-factor 1

# Produce test message
echo "Hello Kafka" | docker compose exec -T kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic test-topic

# Consume test message
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --from-beginning \
  --timeout-ms 5000
```

#### Monitor Kafka

```bash
# List topics with details
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe

# Consumer groups
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Check consumer lag
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group wflo-cost-consumer
```

#### Common Issues

**Error**: `kafka.errors.NoBrokersAvailable: NoBrokersAvailable`

**Solution**:
```bash
# Check Kafka container
docker compose ps kafka

# Check Zookeeper is running (required dependency)
docker compose ps zookeeper

# Check logs
docker compose logs kafka
docker compose logs zookeeper

# Restart Kafka (and Zookeeper if needed)
docker compose restart zookeeper
sleep 10
docker compose restart kafka
```

**Error**: `confluent_kafka.KafkaException: KafkaError{code=_INVALID_ARG}`

**Solution**: Configuration property name error. Check `src/wflo/events/consumer.py` and `producer.py` for correct property names (e.g., `fetch.wait.max.ms` not `fetch.max.wait.ms`).

#### Reset Kafka

```bash
# Delete all topics
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list | grep -v "^__" | xargs -I {} docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --delete \
  --topic {}

# Or remove data volume and restart
docker compose down
docker volume rm wflo_kafka_data
docker compose up -d kafka
```

---

### 4. Zookeeper - Kafka Coordination

**Purpose**: Required for Kafka broker coordination, topic management, and consumer group tracking.

**Container**: `wflo-zookeeper`
**Image**: `confluentinc/cp-zookeeper:7.5.0`
**Port**: `2181`

#### Configuration

```yaml
Client Port: 2181
Tick Time: 2000ms
```

#### Verify Setup

```bash
# Check Zookeeper is running
docker compose ps zookeeper

# Test connection
docker compose exec zookeeper bash -c "echo ruok | nc localhost 2181"
# Expected: imok

# Check Zookeeper logs
docker compose logs zookeeper
```

#### Common Issues

**Error**: Zookeeper fails to start

**Solution**:
```bash
# Check logs
docker compose logs zookeeper

# Remove data and restart
docker compose down
docker volume rm wflo_zookeeper_data wflo_zookeeper_logs
docker compose up -d zookeeper
```

---

### 5. Temporal - Workflow Orchestration

**Purpose**: Durable workflow execution, activity scheduling, automatic retries, state management.

**Container**: `wflo-temporal`
**Image**: `temporalio/auto-setup:1.22.0`
**Port**: `7233` (gRPC)
**Dependencies**: Requires PostgreSQL

#### Configuration

```yaml
Database: PostgreSQL
DB Host: postgres:5432
DB User: wflo_user
DB Password: wflo_password

gRPC Endpoint: localhost:7233
```

#### Verify Setup

```bash
# Check Temporal is running
docker compose ps temporal

# Test using tctl (Temporal CLI inside container)
docker compose exec temporal tctl --address temporal:7233 cluster health

# List namespaces
docker compose exec temporal tctl --address temporal:7233 namespace list

# Create test namespace (if needed)
docker compose exec temporal tctl --address temporal:7233 namespace register --namespace test
```

#### Temporal Web UI

Access the Temporal Web UI at: **http://localhost:8233**

Features:
- View all workflows
- Inspect workflow history
- See active workers
- Monitor task queues
- Search and filter executions

#### Common Issues

**Error**: `rpc error: code = Unavailable desc = connection error`

**Solution**:
```bash
# Check Temporal container
docker compose ps temporal

# Check PostgreSQL is running (dependency)
docker compose ps postgres

# Restart Temporal
docker compose restart temporal

# Wait 30 seconds for initialization
sleep 30

# Verify health
docker compose exec temporal tctl --address temporal:7233 cluster health
```

**Error**: Temporal fails to connect to database

**Solution**:
```bash
# Check PostgreSQL is accessible
docker compose exec temporal psql -h postgres -U wflo_user -d wflo -c "SELECT 1;"

# If fails, restart both services
docker compose restart postgres
sleep 10
docker compose restart temporal
```

#### Reset Temporal

```bash
# Stop Temporal
docker compose stop temporal

# Drop Temporal schema from PostgreSQL
docker compose exec -T postgres psql -U wflo_user -d wflo -c "DROP SCHEMA IF EXISTS temporal CASCADE;"

# Restart Temporal (auto-setup will recreate schema)
docker compose up -d temporal
```

---

### 6. Temporal Web UI

**Purpose**: Web-based dashboard for monitoring workflows, viewing execution history, debugging.

**Container**: `wflo-temporal-web`
**Image**: `temporalio/ui:2.21.0`
**Port**: `8080` → Host `8233`
**Dependencies**: Requires Temporal

#### Access

Open in browser: **http://localhost:8233**

#### Features

- **Workflows**: View all workflow executions
- **History**: Inspect detailed execution history
- **Workers**: Monitor active workflow workers
- **Task Queues**: See pending and completed tasks
- **Search**: Filter by workflow ID, type, status
- **Retry**: Manually retry failed workflows

#### Verify Setup

```bash
# Check Web UI is running
docker compose ps temporal-web

# Test accessibility
curl -s http://localhost:8233 | grep -q "Temporal" && echo "Web UI accessible" || echo "Web UI not accessible"
```

---

### 7. Jaeger - Distributed Tracing

**Purpose**: Collect and visualize distributed traces across workflow executions, activity calls, database queries.

**Container**: `wflo-jaeger`
**Image**: `jaegertracing/all-in-one:1.51`
**Ports**:
- `16686` - Web UI
- `4317` - OTLP gRPC (OpenTelemetry)
- `4318` - OTLP HTTP

#### Access

Open in browser: **http://localhost:16686**

#### Features

- **Trace Search**: Find traces by service, operation, tags
- **Trace Visualization**: See complete request flow across services
- **Service Dependencies**: View service interaction graph
- **Performance Analysis**: Identify slow operations

#### Verify Setup

```bash
# Check Jaeger is running
docker compose ps jaeger

# Test Web UI
curl -s http://localhost:16686 | grep -q "Jaeger" && echo "Jaeger accessible" || echo "Jaeger not accessible"

# Test OTLP endpoint
curl -s http://localhost:4318/v1/traces -o /dev/null && echo "OTLP HTTP ready" || echo "OTLP HTTP not ready"
```

#### View Traces

1. Open http://localhost:16686
2. Select service: `wflo`
3. Select operation: e.g., `execute_workflow`, `track_cost`
4. Click "Find Traces"
5. Click a trace to see detailed timeline

---

## Complete Setup Workflow

### First Time Setup

```bash
# 1. Clone repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# 2. Install Python dependencies
poetry install

# 3. Start all infrastructure services
docker compose up -d

# 4. Wait for health checks (30-60 seconds)
echo "Waiting for services to be healthy..."
sleep 30

# 5. Verify all services are up
docker compose ps

# All should show "Up (healthy)" status

# 6. Apply database migrations to production database
poetry run alembic upgrade head

# 7. Create and setup test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# 8. Verify setup with tests
poetry run pytest tests/unit/ -v                    # Should pass (no infrastructure needed)
poetry run pytest tests/integration/test_redis.py::TestRedisClient::test_redis_health_check -v
poetry run pytest tests/integration/test_database.py::TestWorkflowDefinition::test_create_workflow_definition -v

# 9. Access Web UIs
echo "Temporal UI: http://localhost:8233"
echo "Jaeger UI: http://localhost:16686"
```

### Daily Development Workflow

```bash
# Start infrastructure (if not running)
docker compose up -d

# Verify services are healthy
docker compose ps

# Run tests
poetry run pytest tests/integration/test_database.py -v

# Stop infrastructure (when done for the day)
docker compose down
```

### After Pulling New Code

```bash
# 1. Pull latest code
git pull origin main

# 2. Update dependencies
poetry install

# 3. Apply new database migrations
poetry run alembic upgrade head

# For test database:
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# 4. Run tests to verify
poetry run pytest tests/integration/ -v
```

---

## Troubleshooting

### All Services

#### Check Overall Status

```bash
# View all services
docker compose ps

# Expected: All services show "Up (healthy)"
# If any show "Up" without "(healthy)", wait 30-60 seconds

# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs postgres
docker compose logs redis
docker compose logs kafka
```

#### Restart All Services

```bash
# Restart everything
docker compose restart

# Or stop and start (slower but more thorough)
docker compose down
docker compose up -d
```

#### Clean Slate Reset

```bash
# ⚠️ This will DELETE ALL DATA

# 1. Stop all containers
docker compose down

# 2. Remove volumes (deletes all data)
docker volume rm wflo_postgres_data wflo_redis_data wflo_kafka_data wflo_zookeeper_data wflo_zookeeper_logs wflo_temporal_data

# 3. Start fresh
docker compose up -d

# 4. Wait for services
sleep 30

# 5. Setup databases
poetry run alembic upgrade head
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head
```

### Port Conflicts

**Error**: `bind: address already in use`

**Solution**:
```bash
# Find what's using the port (example: port 5432)
lsof -i :5432
# Or on Linux:
sudo netstat -tulpn | grep 5432

# Kill the process or change wflo's port in docker-compose.yml
# Example: Change PostgreSQL port
# ports:
#   - "15432:5432"  # Host:Container

# Connection string would become:
# postgresql://wflo_user:wflo_password@localhost:15432/wflo
```

### Disk Space Issues

**Error**: `no space left on device`

**Solution**:
```bash
# Check Docker disk usage
docker system df

# Remove unused images, containers, volumes
docker system prune -a --volumes

# Or selectively remove old images
docker image prune -a
```

### Network Issues

**Error**: Services can't communicate with each other

**Solution**:
```bash
# Recreate network
docker compose down
docker network rm wflo-network
docker compose up -d

# Verify network
docker network inspect wflo-network
```

### Container Crashes

**Solution**:
```bash
# View crash logs
docker compose logs <service-name>

# Restart specific service
docker compose restart <service-name>

# Recreate container
docker compose up -d --force-recreate <service-name>
```

---

## Performance Tuning

### PostgreSQL

```bash
# For development, increase connection pool size
# In docker-compose.yml, add:
# command: postgres -c max_connections=200

# Monitor connections
docker compose exec postgres psql -U wflo_user -d wflo -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis

```bash
# Monitor memory usage
docker compose exec redis redis-cli INFO memory

# Set maxmemory policy (e.g., 512MB)
docker compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Kafka

```bash
# Increase partitions for better parallelism
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --alter \
  --topic workflow.events \
  --partitions 4
```

---

## Monitoring

### Health Check Script

Create `scripts/check_health.sh`:

```bash
#!/bin/bash
set -e

echo "Checking Wflo infrastructure health..."

# PostgreSQL
echo -n "PostgreSQL: "
docker compose exec -T postgres pg_isready -U wflo_user && echo "✓" || echo "✗"

# Redis
echo -n "Redis: "
docker compose exec -T redis redis-cli ping > /dev/null && echo "✓" || echo "✗"

# Kafka
echo -n "Kafka: "
docker compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo "✓" || echo "✗"

# Temporal
echo -n "Temporal: "
docker compose exec -T temporal tctl --address temporal:7233 cluster health > /dev/null 2>&1 && echo "✓" || echo "✗"

echo "Health check complete!"
```

```bash
chmod +x scripts/check_health.sh
./scripts/check_health.sh
```

### Log Monitoring

```bash
# Follow logs in real-time
docker compose logs -f

# Follow specific service
docker compose logs -f postgres

# View last 100 lines
docker compose logs --tail=100 kafka
```

---

## Integration with Tests

### Test Database Setup

Tests use a separate `wflo_test` database to avoid interfering with development data.

```bash
# Setup (do this once)
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# Run tests
poetry run pytest tests/integration/test_database.py -v

# Reset test database (if needed)
docker compose exec -T postgres psql -U wflo_user -d postgres -c "DROP DATABASE wflo_test;"
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head
```

### Running Integration Tests

```bash
# All integration tests (requires all services)
poetry run pytest tests/integration/ -v

# Individual test suites
poetry run pytest tests/integration/test_redis.py -v       # Requires Redis
poetry run pytest tests/integration/test_kafka.py -v       # Requires Kafka + Zookeeper
poetry run pytest tests/integration/test_database.py -v    # Requires PostgreSQL
poetry run pytest tests/integration/test_cost_tracking.py -v  # Requires PostgreSQL
poetry run pytest tests/integration/test_temporal.py -v    # Requires Temporal + PostgreSQL

# Unit tests (no infrastructure required)
poetry run pytest tests/unit/ -v
```

---

## Docker Compose Reference

### Common Commands

```bash
# Start services
docker compose up -d              # Detached mode
docker compose up                 # Foreground (see logs)

# Stop services
docker compose down               # Stop and remove containers
docker compose down -v            # Also remove volumes (⚠️ deletes data)
docker compose stop               # Stop without removing

# View status
docker compose ps                 # List containers
docker compose ps -a              # Include stopped containers

# Logs
docker compose logs               # All services
docker compose logs -f            # Follow logs
docker compose logs postgres      # Specific service

# Restart
docker compose restart            # All services
docker compose restart postgres   # Specific service

# Execute commands
docker compose exec postgres psql -U wflo_user -d wflo
docker compose exec redis redis-cli
docker compose exec kafka bash

# Rebuild containers
docker compose build              # Rebuild images
docker compose up -d --build      # Rebuild and start

# Remove everything
docker compose down -v            # Containers, networks, volumes
docker compose rm -f -v           # Force remove containers and volumes
```

### Service Dependencies

Understanding startup order:

1. **PostgreSQL** - Starts first (no dependencies)
2. **Redis** - Starts first (no dependencies)
3. **Zookeeper** - Starts first (no dependencies)
4. **Kafka** - Waits for Zookeeper health check
5. **Temporal** - Waits for PostgreSQL health check
6. **Temporal Web** - Waits for Temporal health check
7. **Jaeger** - Starts independently

---

## Environment Variables

### Override Defaults

Create `.env` file in repo root:

```bash
# Database
POSTGRES_USER=custom_user
POSTGRES_PASSWORD=custom_password
POSTGRES_DB=custom_db

# Redis
REDIS_PASSWORD=custom_redis_password

# Application
DATABASE_URL=postgresql://custom_user:custom_password@localhost:5432/custom_db
REDIS_URL=redis://:custom_redis_password@localhost:6379/0
```

### Test-Specific Variables

```bash
# tests/conftest.py uses TEST_DATABASE_URL if set
export TEST_DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test

# Run tests with custom DB
poetry run pytest tests/integration/test_database.py -v
```

---

## Security Considerations

### Development Environment

The default configuration is for **local development only**:

- Default passwords are insecure
- No SSL/TLS encryption
- All ports exposed to localhost
- No authentication on Redis/Kafka

### Production Deployment

For production:

1. **Use strong passwords** - Generate random passwords
2. **Enable SSL/TLS** - Encrypt connections
3. **Restrict network access** - Don't expose ports publicly
4. **Enable authentication** - Redis AUTH, Kafka SASL
5. **Use secrets management** - Vault, AWS Secrets Manager
6. **Regular updates** - Keep images up to date
7. **Backup data** - Regular PostgreSQL backups

---

## Backup and Restore

### PostgreSQL Backup

```bash
# Backup database
docker compose exec -T postgres pg_dump -U wflo_user wflo > backup_$(date +%Y%m%d).sql

# Restore database
docker compose exec -T postgres psql -U wflo_user -d wflo < backup_20250111.sql
```

### Redis Backup

```bash
# Trigger save
docker compose exec redis redis-cli SAVE

# Copy RDB file
docker compose cp redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb

# Restore (stop Redis, replace file, start Redis)
docker compose stop redis
docker compose cp ./redis_backup.rdb redis:/data/dump.rdb
docker compose start redis
```

---

## Additional Resources

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Docs**: https://redis.io/documentation
- **Kafka Docs**: https://kafka.apache.org/documentation/
- **Temporal Docs**: https://docs.temporal.io/
- **Jaeger Docs**: https://www.jaegertracing.io/docs/

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check service logs: `docker compose logs <service-name>`
2. Search [GitHub Issues](https://github.com/wflo-ai/wflo/issues)
3. Ask in [GitHub Discussions](https://github.com/wflo-ai/wflo/discussions)
4. Review the [TESTING.md](TESTING.md) guide

---

**Last Updated**: 2025-11-11
**Version**: 1.0
**Maintainers**: Wflo AI Team
