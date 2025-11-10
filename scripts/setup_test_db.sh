#!/bin/bash
# Setup test database for integration tests

set -e

echo "🗄️  Setting up test database for Wflo integration tests..."

# Check if PostgreSQL container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running"
    echo "   Run: docker compose up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL container is running"

# Create test database
echo "📝 Creating test database 'wflo_test'..."
docker compose exec -T postgres psql -U wflo_user -d postgres <<EOF
-- Drop existing test database if it exists
DROP DATABASE IF EXISTS wflo_test;

-- Create test database
CREATE DATABASE wflo_test;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wflo_test TO wflo_user;

\c wflo_test

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO wflo_user;
EOF

echo "✅ Test database 'wflo_test' created successfully"

# Run migrations on test database
echo "📝 Running migrations on test database..."
export DATABASE_URL="postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test"
poetry run alembic upgrade head

echo "✅ Migrations completed"
echo ""
echo "🎉 Test database setup complete!"
echo ""
echo "To run integration tests:"
echo "  pytest tests/integration/ -v"
echo ""
echo "To connect to test database:"
echo "  docker compose exec postgres psql -U wflo_user -d wflo_test"
