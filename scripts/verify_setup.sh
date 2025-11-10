#!/bin/bash
# Verify Wflo setup and infrastructure health
# Usage: ./scripts/verify_setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Wflo Setup Verification"
echo "=========================="
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print info
info() {
    echo -e "ℹ $1"
}

# Check Prerequisites
echo "📋 Checking Prerequisites..."
echo "----------------------------"

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python 3 installed: $PYTHON_VERSION"
else
    error "Python 3 not found. Install Python 3.11+"
    exit 1
fi

if command_exists poetry; then
    POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
    success "Poetry installed: $POETRY_VERSION"
else
    error "Poetry not found. Install from https://python-poetry.org"
    exit 1
fi

if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    success "Docker installed: $DOCKER_VERSION"
else
    error "Docker not found. Install Docker Desktop"
    exit 1
fi

if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    success "Docker Compose available"
else
    error "Docker Compose not found"
    exit 1
fi

echo ""

# Check Docker Services
echo "🐳 Checking Docker Services..."
echo "------------------------------"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found. Run from project root."
    exit 1
fi

# Check if services are running
COMPOSE_CMD="docker-compose"
if ! command_exists docker-compose; then
    COMPOSE_CMD="docker compose"
fi

SERVICES=("postgres" "redis" "kafka" "zookeeper" "temporal")

for service in "${SERVICES[@]}"; do
    if $COMPOSE_CMD ps "$service" 2>/dev/null | grep -q "Up"; then
        success "$service is running"
    else
        warning "$service is not running"
        info "Start with: $COMPOSE_CMD up -d $service"
    fi
done

echo ""

# Test Service Connections
echo "🔌 Testing Service Connections..."
echo "---------------------------------"

# Test PostgreSQL
if docker-compose exec -T postgres pg_isready -U wflo_user -d wflo >/dev/null 2>&1; then
    success "PostgreSQL connection OK"
else
    error "PostgreSQL connection failed"
fi

# Test Redis
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    success "Redis connection OK"
else
    error "Redis connection failed"
fi

# Test Kafka (check if topics exist)
if docker-compose exec -T kafka kafka-topics --list --bootstrap-server localhost:9092 >/dev/null 2>&1; then
    success "Kafka connection OK"
else
    warning "Kafka connection failed (may still be starting up)"
fi

# Test Temporal
if docker-compose exec -T temporal tctl cluster health >/dev/null 2>&1; then
    success "Temporal connection OK"
else
    warning "Temporal connection failed (may still be starting up)"
fi

echo ""

# Check Python Environment
echo "🐍 Checking Python Environment..."
echo "----------------------------------"

if poetry env info >/dev/null 2>&1; then
    success "Poetry virtual environment exists"

    # Check if dependencies are installed
    if poetry run python -c "import wflo" 2>/dev/null; then
        success "Wflo package installed"
    else
        warning "Wflo package not found"
        info "Run: poetry install"
    fi

    # Check key dependencies
    DEPS=("temporalio" "redis" "confluent_kafka" "sqlalchemy" "tokencost")
    for dep in "${DEPS[@]}"; do
        if poetry run python -c "import $dep" 2>/dev/null; then
            success "$dep installed"
        else
            warning "$dep not found"
        fi
    done
else
    warning "Poetry virtual environment not found"
    info "Run: poetry install"
fi

echo ""

# Check Database Migrations
echo "🗄️  Checking Database..."
echo "------------------------"

if [ -f "alembic.ini" ]; then
    success "Alembic configuration found"

    # Check if tables exist
    if docker-compose exec -T postgres psql -U wflo_user -d wflo -c "SELECT COUNT(*) FROM workflow_definitions;" >/dev/null 2>&1; then
        success "Database tables exist"
    else
        warning "Database tables not found"
        info "Run migrations: poetry run alembic upgrade head"
    fi
else
    warning "alembic.ini not found"
fi

echo ""

# Check Test Files
echo "🧪 Checking Test Suite..."
echo "-------------------------"

TEST_DIRS=("tests/unit" "tests/integration")
for test_dir in "${TEST_DIRS[@]}"; do
    if [ -d "$test_dir" ]; then
        TEST_COUNT=$(find "$test_dir" -name "test_*.py" | wc -l)
        success "$test_dir: $TEST_COUNT test files"
    else
        warning "$test_dir not found"
    fi
done

echo ""

# Summary
echo "📊 Setup Summary"
echo "================"

ALL_SERVICES_UP=true
for service in "${SERVICES[@]}"; do
    if ! $COMPOSE_CMD ps "$service" 2>/dev/null | grep -q "Up"; then
        ALL_SERVICES_UP=false
        break
    fi
done

if [ "$ALL_SERVICES_UP" = true ]; then
    success "All infrastructure services are running"
    echo ""
    echo "✨ Ready to develop!"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: poetry run pytest tests/integration/ -v"
    echo "  2. Start worker: poetry run python -m wflo.temporal.worker"
    echo "  3. Run workflow: poetry run python examples/simple_workflow.py"
    echo ""
    echo "Service UIs:"
    echo "  • Temporal: http://localhost:8233"
    echo "  • Jaeger:   http://localhost:16686"
else
    warning "Some services are not running"
    echo ""
    echo "🚀 Start services:"
    echo "   $COMPOSE_CMD up -d"
    echo ""
    echo "⏳ Wait 30-60 seconds for services to start"
    echo ""
    echo "🔄 Then run this script again:"
    echo "   ./scripts/verify_setup.sh"
fi

echo ""
