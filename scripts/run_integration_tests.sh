#!/bin/bash
# Run integration tests with proper setup

set -e

echo "🧪 Running Wflo integration tests..."
echo ""

# Check if test database exists
if ! docker compose exec -T postgres psql -U wflo_user -lqt | cut -d \| -f 1 | grep -qw wflo_test; then
    echo "❌ Test database 'wflo_test' does not exist"
    echo "   Run: ./scripts/setup_test_db.sh"
    exit 1
fi

echo "✅ Test database exists"

# Set test database URL
export TEST_DATABASE_URL="postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test"

# Run integration tests
echo "🏃 Running integration tests..."
echo ""

poetry run pytest tests/integration/ -v --tb=short "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All integration tests passed!"
else
    echo ""
    echo "❌ Some integration tests failed (exit code: $exit_code)"
fi

exit $exit_code
