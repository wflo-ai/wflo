# Wflo - Minimum Development Requirements

**Last Updated**: 2025-11-09

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+, Debian 11+, or any modern Linux distribution
- **macOS**: macOS 12 (Monterey) or later
- **Windows**: Windows 10/11 with WSL2 (Windows Subsystem for Linux)

### Hardware
- **CPU**: 4+ cores recommended (2 cores minimum)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 20GB free space minimum (for Docker images and dependencies)
- **Network**: Internet connection for package downloads and Kafka communication

---

## Software Requirements

### 1. Python
- **Version**: Python 3.11 or later (3.11, 3.12, 3.13)
- **Installation**:
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3-pip

  # macOS (using Homebrew)
  brew install python@3.11

  # Verify installation
  python3.11 --version
  ```

### 2. Docker
- **Version**: Docker Engine 24.0+ or Docker Desktop 4.20+
- **Required for**: Running PostgreSQL, Redis, Kafka, and sandbox containers
- **Installation**:

  **Linux**:
  ```bash
  # Ubuntu/Debian
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  # Log out and back in for group changes to take effect

  # Verify
  docker --version
  docker compose version
  ```

  **macOS**:
  ```bash
  # Download and install Docker Desktop from:
  # https://www.docker.com/products/docker-desktop

  # Verify
  docker --version
  docker compose version
  ```

  **Windows (WSL2)**:
  ```powershell
  # Install Docker Desktop for Windows with WSL2 backend
  # https://docs.docker.com/desktop/install/windows-install/
  ```

### 3. Docker Compose
- **Version**: Docker Compose v2.20+ (usually bundled with Docker Desktop)
- **Verification**:
  ```bash
  docker compose version
  # Should output: Docker Compose version v2.20.0 or later
  ```

### 4. Poetry
- **Version**: Poetry 1.7.0+
- **Required for**: Python dependency management and packaging
- **Installation**:
  ```bash
  # Official installer (recommended)
  curl -sSL https://install.python-poetry.org | python3 -

  # Add to PATH (Linux/macOS)
  export PATH="$HOME/.local/bin:$PATH"

  # Or using pipx
  pipx install poetry

  # Verify
  poetry --version
  ```

### 5. Git
- **Version**: Git 2.30+
- **Installation**:
  ```bash
  # Ubuntu/Debian
  sudo apt install git

  # macOS
  brew install git

  # Verify
  git --version
  ```

---

## Development Infrastructure (via Docker Compose)

These services run in Docker containers for local development:

### 1. PostgreSQL
- **Version**: PostgreSQL 15+
- **Purpose**: Workflow metadata, state persistence
- **Container**: `postgres:15-alpine`
- **Port**: 5432
- **Configuration**:
  - Database: `wflo`
  - User: `wflo_user`
  - Password: Configured in `.env`

### 2. Redis
- **Version**: Redis 7+
- **Purpose**: Caching, distributed locks, session state
- **Container**: `redis:7-alpine`
- **Port**: 6379

### 3. Apache Kafka
- **Version**: Kafka 3.6+
- **Purpose**: Event streaming, workflow events
- **Container**: `confluentinc/cp-kafka:7.5.0`
- **Port**: 9092 (broker), 9093 (controller)
- **Dependencies**: Requires Zookeeper or KRaft mode

### 4. Temporal Server
- **Version**: Temporal 1.22+
- **Purpose**: Workflow orchestration engine
- **Container**: `temporalio/auto-setup:latest`
- **Ports**:
  - 7233 (gRPC)
  - 8233 (Web UI)
- **Dependencies**: PostgreSQL for persistence

### Docker Compose Services Summary
```yaml
services:
  - postgres (PostgreSQL 15)
  - redis (Redis 7)
  - zookeeper (for Kafka)
  - kafka (Confluent Platform 7.5)
  - temporal (Temporal Server)
  - temporal-web (Temporal Web UI)
```

---

## Optional but Recommended

### 1. IDE / Code Editor
**Recommended**:
- **VS Code** with extensions:
  - Python
  - Pylance
  - Docker
  - YAML
  - GitLens
- **PyCharm Professional** (has built-in Docker, database tools)

### 2. Database Client
- **DBeaver** (free, cross-platform)
- **pgAdmin** (PostgreSQL-specific)
- **TablePlus** (macOS/Windows, paid)
- Or use VS Code extension: PostgreSQL

### 3. Kafka Client / UI
- **Confluent Control Center** (enterprise)
- **Kafka UI** (open-source, web-based)
- **kafkacat/kcat** (CLI tool)

### 4. Redis Client
- **RedisInsight** (official, free)
- **redis-cli** (command-line, bundled with Redis)

---

## Environment Setup Checklist

Before starting development, ensure you have:

- [ ] Python 3.11+ installed and available in PATH
- [ ] Docker and Docker Compose installed and running
- [ ] Poetry installed for dependency management
- [ ] Git configured with your identity:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```
- [ ] Docker daemon running (test with `docker ps`)
- [ ] Sufficient disk space (20GB+ free)
- [ ] IDE or code editor installed

---

## Quick Verification Script

Run this script to verify all requirements:

```bash
#!/bin/bash

echo "=== Wflo Development Environment Check ==="
echo

# Python
echo "Checking Python..."
python3 --version || echo "❌ Python 3.11+ not found"
echo

# Docker
echo "Checking Docker..."
docker --version || echo "❌ Docker not found"
docker ps >/dev/null 2>&1 && echo "✅ Docker daemon running" || echo "❌ Docker daemon not running"
echo

# Docker Compose
echo "Checking Docker Compose..."
docker compose version || echo "❌ Docker Compose not found"
echo

# Poetry
echo "Checking Poetry..."
poetry --version || echo "❌ Poetry not found"
echo

# Git
echo "Checking Git..."
git --version || echo "❌ Git not found"
echo

# Disk space
echo "Checking disk space..."
df -h . | tail -1 | awk '{print "Available: " $4}'
echo

echo "=== Check Complete ==="
```

Save as `check_requirements.sh`, make executable with `chmod +x check_requirements.sh`, and run with `./check_requirements.sh`.

---

## Resource Allocation

### Docker Resource Recommendations

**Docker Desktop Settings**:
- **CPUs**: Allocate 4 CPUs (minimum 2)
- **Memory**: Allocate 8GB RAM (minimum 6GB)
- **Swap**: 2GB
- **Disk Image Size**: 64GB+

**Linux** (Docker Engine):
No specific configuration needed; uses host resources directly.

---

## Network Ports

Ensure these ports are available on your local machine:

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database connections |
| Redis | 6379 | Cache/session storage |
| Kafka Broker | 9092 | Kafka client connections |
| Zookeeper | 2181 | Kafka coordination |
| Temporal gRPC | 7233 | Temporal client connections |
| Temporal Web UI | 8233 | Temporal dashboard |

**Port Conflict Resolution**:
If any port is already in use, modify the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead of 5432
```

---

## Development Workflow

### Initial Setup (One-time)
```bash
# 1. Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# 2. Install Python dependencies
poetry install

# 3. Start infrastructure services
docker compose up -d

# 4. Copy environment template
cp .env.example .env

# 5. Run database migrations
poetry run alembic upgrade head

# 6. Run tests to verify setup
poetry run pytest
```

### Daily Development
```bash
# Start services
docker compose up -d

# Activate virtual environment
poetry shell

# Run application
poetry run python -m wflo

# Run tests
poetry run pytest

# Stop services
docker compose down
```

---

## Troubleshooting

### Docker Issues

**Problem**: Docker daemon not running
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Start Docker Desktop application
```

**Problem**: Permission denied when running Docker
```bash
# Linux only
sudo usermod -aG docker $USER
# Log out and log back in
```

### Port Conflicts

**Problem**: Port already in use
```bash
# Find process using port (Linux/macOS)
sudo lsof -i :5432

# Kill process or change port in docker-compose.yml
```

### Python Environment Issues

**Problem**: Poetry not found after installation
```bash
# Add to shell profile (~/.bashrc, ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

**Problem**: Wrong Python version
```bash
# Tell Poetry which Python to use
poetry env use python3.11

# Or use pyenv to manage multiple Python versions
```

---

## Next Steps

Once all requirements are met:
1. Proceed to `plan/DEVELOPMENT_PLAN.md` for the detailed build roadmap
2. Review `plan/TODO.md` for task breakdown
3. Start with project initialization: `poetry init`

---

## Additional Resources

- [Docker Installation Docs](https://docs.docker.com/engine/install/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python 3.11 Downloads](https://www.python.org/downloads/)
- [Temporal Getting Started](https://docs.temporal.io/getting_started)
- [Kafka Quickstart](https://kafka.apache.org/quickstart)
