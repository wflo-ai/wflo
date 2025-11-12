---
sidebar_position: 2
title: Getting Started
description: Quick start guide to building your first wflo workflow with budget controls
---

# Getting Started

Get up and running with wflo in minutes. Build AI agent workflows with production-ready cost controls and observability.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (local or Supabase)
- API keys for LLM providers (OpenAI, Anthropic, etc.)
- Git

## Installation

### From PyPI (Coming Soon)

```bash
pip install wflo
```

### From Source (Current)

```bash
# Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install with Poetry
poetry install

# Or with pip
pip install -e ".[dev]"
```

## Database Setup

wflo requires PostgreSQL for state persistence and checkpointing.

### Option 1: Supabase (Recommended)

Supabase provides managed PostgreSQL with authentication and is ideal for production.

1. **Create Supabase Project**
   - Sign up at https://supabase.com
   - Create new project
   - Save your database password

2. **Get Connection String**
   - Go to Settings → Database
   - Copy the connection URI
   - Format: \`postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres\`

3. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env and set:
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxxxxxxxxxx.supabase.co:5432/postgres
   ```

4. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

5. **Test Connection**
   ```bash
   python scripts/test_supabase_connection.py
   ```

**See [Supabase Setup Guide](./supabase-setup.md) for detailed instructions.**

### Option 2: Local PostgreSQL

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql

   # Ubuntu/Debian
   sudo apt-get install postgresql
   sudo systemctl start postgresql
   ```

2. **Create Database**
   ```bash
   createdb wflo
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env

   # Edit .env:
   DATABASE_URL=postgresql+asyncpg://localhost:5432/wflo
   ```

4. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

## Set Up API Keys

```bash
# Edit .env and add your API keys:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Your First Workflow

Create \`examples/my_first_workflow.py\`:

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

@track_llm_call(model="gpt-3.5-turbo")
async def generate_greeting(name: str):
    """Generate a personalized greeting using GPT-3.5."""
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Generate a friendly greeting for {name}"}
        ],
        max_tokens=50,
    )
    return response.choices[0].message.content

async def main():
    # Create workflow with budget
    workflow = WfloWorkflow(
        name="hello-world",
        budget_usd=0.10,  # \$0.10 maximum spend
    )

    try:
        # Execute workflow
        result = await workflow.execute(
            generate_greeting,
            {"name": "Alice"}
        )

        print(f"\n✅ Workflow completed!")
        print(f"Result: {result}")

        # Check costs
        breakdown = await workflow.get_cost_breakdown()
        print(f"\n💰 Cost Analysis:")
        print(f"  Total: \${breakdown['total_usd']:.4f}")
        print(f"  Budget: \${breakdown['budget_usd']:.2f}")
        print(f"  Remaining: \${breakdown['remaining_usd']:.4f}")

        # Execution tracking
        print(f"\n🔍 Execution ID: {workflow.execution_id}")

    except BudgetExceededError as e:
        print(f"❌ Budget exceeded!")
        print(f"  Spent: \${e.spent_usd:.4f}")
        print(f"  Budget: \${e.budget_usd:.2f}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export OPENAI_API_KEY=sk-...
python examples/my_first_workflow.py
```

Expected output:
```
✅ Workflow completed!
Result: Hello Alice! Hope you're having a wonderful day!

💰 Cost Analysis:
  Total: \$0.0008
  Budget: \$0.10
  Remaining: \$0.0992

🔍 Execution ID: exec-a1b2c3d4e5f6
```

## Next Steps

- **[Features](./features.md)** - Explore all Phase 1 features
- **[Examples](./examples.md)** - See comprehensive examples
- **[Supabase Setup](./supabase-setup.md)** - Detailed Supabase guide
- **[Architecture](./architecture.md)** - Understand how wflo works

## Troubleshooting

### Database Connection Issues

If you see connection errors:

1. **Check DATABASE_URL format**
   ```bash
   # Should have +asyncpg driver
   postgresql+asyncpg://user:pass@host:5432/db
   ```

2. **Verify database exists**
   ```bash
   python scripts/test_supabase_connection.py
   ```

3. **Initialize database tables**
   ```bash
   python scripts/init_db.py
   ```

### API Key Issues

If you see authentication errors:

1. **Verify API keys are set**
   ```bash
   echo \$OPENAI_API_KEY
   ```

2. **Check .env file**
   ```bash
   cat .env | grep API_KEY
   ```

### Budget Exceeded Errors

If workflows fail with \`BudgetExceededError\`:

1. **Increase budget** in \`WfloWorkflow\` initialization
2. **Use cheaper models** (gpt-3.5-turbo instead of gpt-4)
3. **Reduce max_tokens** in LLM calls

## Getting Help

- **GitHub Issues**: https://github.com/wflo-ai/wflo/issues
- **Documentation**: https://docs.wflo.ai
- **Examples**: Check \`examples/\` directory in the repository
