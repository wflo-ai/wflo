# Supabase Setup Guide

Complete guide to setting up wflo with Supabase for PostgreSQL database and authentication.

## Why Supabase?

Supabase provides:
- **Managed PostgreSQL** - No database administration overhead
- **Built-in authentication** - User management, OAuth, JWT
- **Connection pooling** - Optimized for serverless and high-concurrency workloads
- **Automatic backups** - Point-in-time recovery
- **Real-time capabilities** - Database change subscriptions (for future features)
- **Free tier** - 500MB database, 2GB bandwidth

## Prerequisites

1. Python 3.11 or higher
2. Supabase account (sign up at https://supabase.com)
3. Poetry or pip for package management

## Step 1: Create Supabase Project

1. Go to https://app.supabase.com
2. Click "New Project"
3. Fill in project details:
   - **Name**: `wflo-production` (or your preferred name)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
4. Click "Create new project"
5. Wait for project to finish provisioning (~2 minutes)

## Step 2: Get Database Connection Details

### Method 1: Via Supabase Dashboard

1. Navigate to **Settings** → **Database**
2. Scroll to **Connection String**
3. Select **URI** tab
4. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxxxxxxxxx.supabase.co:5432/postgres
   ```

### Method 2: Build Connection String Manually

Format:
```
postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres
```

Components:
- **Host**: `db.[PROJECT-REF].supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: Your database password from Step 1

Example:
```
postgresql://postgres:MySecurePassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

## Step 3: Configure wflo to Use Supabase

### Update Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and update `DATABASE_URL`:
   ```bash
   # Replace with your Supabase connection string
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxxxxxxxxxx.supabase.co:5432/postgres
   ```

   **Important**: Note the `+asyncpg` in the URL. wflo uses asyncpg driver.

3. Adjust connection pool settings for Supabase:
   ```bash
   # Supabase connection pool settings
   DATABASE_POOL_SIZE=10          # Lower for serverless environments
   DATABASE_MAX_OVERFLOW=5        # Conservative overflow
   ```

### Connection Pool Best Practices

Supabase has connection limits based on your plan:
- **Free tier**: 60 connections
- **Pro tier**: 200 connections
- **Team tier**: 400+ connections

Recommended settings:

#### For Serverless/Lambda:
```bash
DATABASE_POOL_SIZE=2
DATABASE_MAX_OVERFLOW=0
```

#### For Container/Server:
```bash
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5
```

#### For High-Concurrency Production:
```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

## Step 4: Run Database Migrations

wflo automatically creates tables on first run, but you can initialize the database explicitly:

```python
import asyncio
from wflo.config import get_settings
from wflo.db.engine import init_db
from wflo.db.models import Base

async def setup_database():
    """Initialize database with wflo schema."""
    settings = get_settings()
    db = init_db(settings)
    engine = db.get_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized successfully!")
    await db.close()

if __name__ == "__main__":
    asyncio.run(setup_database())
```

Save as `scripts/init_db.py` and run:
```bash
python scripts/init_db.py
```

## Step 5: Verify Connection

Create `scripts/test_supabase_connection.py`:

```python
import asyncio
from wflo.config import get_settings
from wflo.db.engine import init_db

async def test_connection():
    """Test Supabase connection."""
    settings = get_settings()
    print(f"Connecting to: {settings.database_url.host}")

    db = init_db(settings)

    try:
        # Test connection
        is_healthy = await db.health_check()
        if is_healthy:
            print("✅ Successfully connected to Supabase!")
            print(f"   Host: {settings.database_url.host}")
            print(f"   Database: {settings.database_url.path}")
        else:
            print("❌ Health check failed")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run:
```bash
python scripts/test_supabase_connection.py
```

Expected output:
```
Connecting to: db.xxxxxxxxxxxxxxxxxxxx.supabase.co
✅ Successfully connected to Supabase!
   Host: db.xxxxxxxxxxxxxxxxxxxx.supabase.co
   Database: /postgres
```

## Step 6: Run Your First Workflow

```python
import asyncio
from openai import AsyncOpenAI
from wflo.sdk.workflow import WfloWorkflow, BudgetExceededError
from wflo.sdk.decorators.track_llm import track_llm_call
from wflo.config import get_settings
from wflo.db.engine import init_db

# Initialize database
settings = get_settings()
db = init_db(settings)

client = AsyncOpenAI()

@track_llm_call(model="gpt-4")
async def simple_chat(prompt: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

async def main():
    workflow = WfloWorkflow(
        name="supabase-test-workflow",
        budget_usd=0.50,  # $0.50 budget
    )

    try:
        result = await workflow.execute(
            simple_chat,
            {"prompt": "Say hello from Supabase!"}
        )

        print(f"\n✅ Workflow completed!")
        print(f"Result: {result}")

        # Check cost
        breakdown = await workflow.get_cost_breakdown()
        print(f"\n💰 Cost: ${breakdown['total_usd']:.4f}")
        print(f"Execution ID: {workflow.execution_id}")

    except BudgetExceededError as e:
        print(f"Budget exceeded: ${e.spent_usd:.4f}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 7: Verify Data in Supabase

1. Go to Supabase dashboard → **Table Editor**
2. You should see wflo tables:
   - `workflow_definitions`
   - `workflow_executions`
   - `step_executions`
   - `state_snapshots`
   - `approval_requests`
   - `rollback_actions`

3. Click on `workflow_executions` to see your execution record

## Advanced Configuration

### SSL/TLS Configuration

Supabase enforces SSL by default. If you need to customize SSL settings:

```python
from sqlalchemy import create_async_engine

engine = create_async_engine(
    database_url,
    connect_args={
        "ssl": "require",  # or "prefer", "allow", "disable"
    }
)
```

### Connection Pooling for Serverless

For serverless environments (AWS Lambda, Vercel, etc.), use Supabase's connection pooler:

1. In Supabase Dashboard → **Settings** → **Database**
2. Find **Connection Pooling** section
3. Copy the **Transaction** pooler connection string
4. Use this URL instead of the direct connection string

Format:
```
postgresql://postgres:[PASSWORD]@[PROJECT-REF].pooler.supabase.com:5432/postgres
```

Update `.env`:
```bash
# Supabase connection pooler (for serverless)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxxxxxxxxxx.pooler.supabase.com:5432/postgres
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=0
```

### Environment-Specific Configuration

#### Development (.env.development)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db.dev-project.supabase.co:5432/postgres
DATABASE_POOL_SIZE=5
DATABASE_ECHO=true  # Enable SQL logging
```

#### Production (.env.production)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db.prod-project.pooler.supabase.com:5432/postgres
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false
```

## Troubleshooting

### Connection Refused

**Error**: `could not connect to server: Connection refused`

**Solutions**:
1. Check if project is fully provisioned (can take 2-3 minutes)
2. Verify connection string has correct project reference
3. Check firewall/network settings
4. Try using connection pooler URL instead

### Too Many Connections

**Error**: `FATAL: sorry, too many clients already`

**Solutions**:
1. Reduce `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
2. Use Supabase connection pooler (see above)
3. Upgrade Supabase plan for more connections
4. Ensure proper connection cleanup in your code

### SSL Required

**Error**: `connection requires SSL`

**Solution**: Supabase requires SSL. This is handled automatically by asyncpg, but ensure you're using the correct connection string format.

### Password Authentication Failed

**Error**: `password authentication failed for user "postgres"`

**Solutions**:
1. Verify password is correct (check your Supabase project settings)
2. Reset database password in Supabase Dashboard → Settings → Database
3. Ensure no special characters are unescaped in the connection string
4. If password has special characters, URL-encode them

## Integration Tests with Supabase

To run integration tests against Supabase:

```bash
# Set test database URL
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@db.test-project.supabase.co:5432/postgres

# Run integration tests
poetry run pytest tests/integration/ -v -m integration
```

**Recommendation**: Create a separate Supabase project for testing to avoid mixing test data with production data.

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables in production** - Not `.env` files
3. **Rotate database passwords regularly** - Every 90 days minimum
4. **Use Row Level Security (RLS)** - If exposing data to frontend
5. **Enable Point-in-Time Recovery** - For production databases
6. **Monitor connection usage** - Via Supabase dashboard
7. **Use connection pooler for serverless** - Prevents connection exhaustion

## Monitoring

### Supabase Dashboard

Monitor database health:
1. Go to **Reports** → **Database**
2. Check:
   - Active connections
   - Database size
   - Query performance
   - Slow queries

### wflo Metrics

Query workflow execution costs:

```sql
-- Total cost by workflow
SELECT
    workflow_definition_id,
    COUNT(*) as executions,
    SUM(cost_total_usd) as total_cost,
    AVG(cost_total_usd) as avg_cost
FROM workflow_executions
GROUP BY workflow_definition_id
ORDER BY total_cost DESC;

-- Recent executions
SELECT
    id,
    status,
    cost_total_usd,
    created_at
FROM workflow_executions
ORDER BY created_at DESC
LIMIT 10;
```

## Next Steps

- [Getting Started Guide](../website/docs/getting-started.md) - Build your first workflow
- [Examples](../examples/README.md) - See comprehensive examples
- [Integration Tests](../tests/integration/test_supabase.py) - Run Supabase integration tests

## Support

- **wflo Issues**: https://github.com/wflo-ai/wflo/issues
- **Supabase Docs**: https://supabase.com/docs
- **Supabase Support**: https://supabase.com/support
