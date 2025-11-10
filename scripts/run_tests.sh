#!/bin/bash
# Run Wflo tests with various configurations
# Usage: ./scripts/run_tests.sh [unit|integration|all|coverage]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get test type from argument (default: all)
TEST_TYPE=${1:-all}

echo -e "${BLUE}🧪 Wflo Test Runner${NC}"
echo "===================="
echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests...${NC}"
    poetry run pytest tests/unit/ -v --tb=short
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"
    echo ""
    echo "⚠️  Integration tests require Docker services to be running:"
    echo "   - PostgreSQL (port 5432)"
    echo "   - Redis (port 6379)"
    echo "   - Kafka (port 9092)"
    echo "   - Temporal (port 7233)"
    echo ""
    read -p "Are services running? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Start services with: docker-compose up -d"
        exit 1
    fi

    echo ""
    poetry run pytest tests/integration/ -v --tb=short
}

# Function to run all tests with coverage
run_coverage() {
    echo -e "${YELLOW}Running all tests with coverage...${NC}"
    poetry run pytest tests/ \
        --cov=wflo \
        --cov-report=html \
        --cov-report=term-missing \
        -v

    echo ""
    echo -e "${GREEN}Coverage report generated:${NC} htmlcov/index.html"
}

# Main test execution
case $TEST_TYPE in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    coverage)
        run_coverage
        ;;
    all)
        echo -e "${BLUE}Running all tests...${NC}"
        echo ""
        run_unit_tests
        echo ""
        echo "---"
        echo ""
        run_integration_tests
        ;;
    *)
        echo "Usage: $0 [unit|integration|all|coverage]"
        echo ""
        echo "Options:"
        echo "  unit         - Run only unit tests (fast, no Docker)"
        echo "  integration  - Run only integration tests (requires Docker)"
        echo "  all          - Run both unit and integration tests"
        echo "  coverage     - Run all tests with coverage report"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Tests completed!${NC}"
