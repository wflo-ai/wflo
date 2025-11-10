# Database Migration Guide: Adding Foreign Key Constraints

**Status**: Migration file created, ready to apply
**Migration**: `500165e12345_add_missing_foreign_keys.py`
**Affects**: 5 database tables (will fix 21 failing integration tests)

## What This Migration Does

This migration adds missing foreign key constraints to enforce referential integrity between tables:

1. **workflow_executions.workflow_id** → workflow_definitions.id
2. **step_executions.execution_id** → workflow_executions.id
3. **state_snapshots.execution_id** → workflow_executions.id
4. **approval_requests.execution_id** → workflow_executions.id
5. **rollback_actions.execution_id** → workflow_executions.id

These foreign keys are required by SQLAlchemy's ORM relationship definitions and ensure data consistency.

## Prerequisites

- Docker services running: `docker compose ps` (all should show "Up")
- Python environment set up: `poetry install`
- Initial schema migration already applied to production database

## Step 1: Apply Migration to Production Database

The production database (`wflo`) needs the foreign key constraints:

```bash
# Apply the migration
poetry run alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 6d27a51e02d6 -> 500165e12345, add missing foreign keys
```

### Verify Production Migration

```bash
# Check current migration version
poetry run alembic current

# Should show:
# 500165e12345 (head)

# Verify foreign keys exist in database
docker compose exec -T postgres psql -U wflo_user -d wflo -c "
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('workflow_executions', 'step_executions', 'state_snapshots', 'approval_requests', 'rollback_actions')
ORDER BY tc.table_name;
"

# Should show 5 foreign key constraints
```

## Step 2: Set Up Test Database

The test database needs to be created fresh with all migrations:

### Option A: Fresh Test Database (Recommended)

```bash
# 1. Drop existing test database (if it exists)
docker compose exec -T postgres psql -U wflo_user -d postgres -c "DROP DATABASE IF EXISTS wflo_test;"

# 2. Create fresh test database
docker compose exec -T postgres psql -U wflo_user -d postgres -c "CREATE DATABASE wflo_test;"

# 3. Run ALL migrations on test database
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade -> 6d27a51e02d6, Create core tables
# INFO  [alembic.runtime.migration] Running upgrade 6d27a51e02d6 -> 500165e12345, add missing foreign keys
```

### Option B: Continue from Existing State (If test DB partially exists)

```bash
# Check current migration status
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic current

# Apply remaining migrations
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic upgrade head
```

### Verify Test Database

```bash
# Verify migration version
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo_test \
  poetry run alembic current

# Should show: 500165e12345 (head)

# Verify tables exist
docker compose exec -T postgres psql -U wflo_user -d wflo_test -c "\dt"

# Should show 6 tables:
# - workflow_definitions
# - workflow_executions
# - step_executions
# - state_snapshots
# - approval_requests
# - rollback_actions

# Verify foreign keys exist
docker compose exec -T postgres psql -U wflo_user -d wflo_test -c "
SELECT COUNT(*) as foreign_key_count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name IN ('workflow_executions', 'step_executions', 'state_snapshots', 'approval_requests', 'rollback_actions');
"

# Should show: foreign_key_count = 5
```

## Step 3: Run Database Tests

After applying migrations, the database tests should pass:

```bash
# Run database tests (should now pass)
poetry run pytest tests/integration/test_database.py -v

# Expected results:
# - 15 tests should PASS (previously 0/15)
# - Tests include: workflow creation, execution tracking, relationships, queries

# Run cost tracking tests (8 tests should now pass)
poetry run pytest tests/integration/test_cost_tracking.py -v

# Expected results:
# - 8 tests PASS (SQLAlchemy errors fixed)
# - 3 tests MAY FAIL (Decimal vs float type mismatch - separate issue)
```

## Troubleshooting

### Error: "relation does not exist"

**Problem**: Migration tries to add foreign keys to tables that don't exist yet.

**Solution**: Use Option A (fresh test database) to ensure all tables are created first.

### Error: "column referenced in foreign key constraint does not exist"

**Problem**: The source or target column doesn't exist in the table.

**Solution**:
```bash
# Check if base migration was applied
poetry run alembic history

# Should show:
# 6d27a51e02d6 -> 500165e12345 (head), add missing foreign keys
# <base> -> 6d27a51e02d6, Create core tables
```

### Error: "duplicate key value violates unique constraint"

**Problem**: Trying to run initial migration when tables already exist.

**Solution**: Check current migration status and only run `upgrade head`, not individual migrations.

### Database Tests Still Failing

If tests still fail after migration:

1. **Verify foreign keys are in place**:
   ```bash
   docker compose exec -T postgres psql -U wflo_user -d wflo_test -c "
   \d workflow_executions
   "
   # Look for "Foreign-key constraints:" section
   ```

2. **Check SQLAlchemy models match schema**:
   ```bash
   # The models in src/wflo/db/models.py should have ForeignKey() in mapped_column()
   grep -n "ForeignKey" src/wflo/db/models.py
   ```

3. **Restart test run with verbose output**:
   ```bash
   poetry run pytest tests/integration/test_database.py::test_create_workflow_definition -vv
   ```

## Expected Test Results After Migration

| Test Suite | Before | After | Notes |
|------------|--------|-------|-------|
| Database Tests | 0/15 passing | 15/15 passing | ✅ All should pass |
| Cost Tracking (DB) | 0/8 passing | 8/11 passing | ✅ FK errors fixed |
| Cost Tracking (Math) | 3/3 passing | 3/3 passing | ⚠️ Still has Decimal/float issues |

**Total Impact**: 21 additional tests passing (from 28/58 to 49/58 = 84%)

## Next Steps After Migration Success

1. **Update INTEGRATION_TEST_STATUS.md**:
   - Mark database tests as passing
   - Update test count (49/58 passing)
   - Move to next priority fixes

2. **Fix Remaining Cost Tracking Tests** (3 tests):
   - Issue: Decimal vs float type mismatch in assertions
   - Quick fix: Update test assertions to use Decimal type

3. **Address Sandbox Tests** (30 tests):
   - Build Docker runtime images
   - Fix runtime.py container error handling bug

4. **Fix Temporal Tests** (5 tests):
   - Update to Temporal SDK 1.5.0 API

5. **Fix Redis/Kafka Tests** (11 tests):
   - Event loop cleanup issues
   - Kafka consumer configuration

## Migration File Details

**Location**: `src/wflo/db/migrations/versions/500165e12345_add_missing_foreign_keys.py`

**Key Operations**:
- Creates 5 foreign key constraints with CASCADE delete behavior
- Naming convention: `fk_{source_table}_{column_name}`
- Rollback support: Drops constraints in reverse order

**Safety**:
- ✅ Non-destructive migration (only adds constraints)
- ✅ Will fail safely if referential integrity violated
- ✅ Can be rolled back with `alembic downgrade -1`

---

**Status**: Ready to apply migration
**Risk Level**: Low (non-destructive, well-tested pattern)
**Estimated Time**: 2-3 minutes per database
**Impact**: Fixes 21 failing integration tests
