#!/bin/bash
# Cleanup test database

set -e

echo "🧹 Cleaning up test database..."

# Check if PostgreSQL container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running"
    exit 1
fi

# Drop test database
echo "📝 Dropping test database 'wflo_test'..."
docker compose exec -T postgres psql -U wflo_user -d postgres <<EOF
DROP DATABASE IF EXISTS wflo_test;
EOF

echo "✅ Test database cleaned up"
