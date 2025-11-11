# Simple LLM Agent Example

A complete, working example demonstrating Wflo's core capabilities with OpenAI integration.

## What This Example Demonstrates

✅ **End-to-End Workflow**: From request to result with full observability
✅ **OpenAI Integration**: Call GPT-4 API with automatic token counting
✅ **Cost Tracking**: Real-time cost calculation and budget enforcement
✅ **Database Persistence**: Execution history stored in PostgreSQL
✅ **Event Streaming**: Workflow events published to Kafka
✅ **Error Handling**: Graceful failure with detailed logging
✅ **Observability**: Structured logs, traces, and metrics

## Architecture

```
User Request
     │
     ▼
┌─────────────────┐
│   run.py (CLI)  │ ← Entry point
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ WfloWorkflow    │ ← Temporal orchestration
│  (Temporal)     │
└─────────────────┘
     │
     ├─► save_workflow_execution (Activity)
     │   └─► PostgreSQL: Store execution
     │
     ├─► execute_llm_step (Activity)
     │   ├─► OpenAI API: Call GPT-4
     │   ├─► CostTracker: Calculate cost
     │   └─► PostgreSQL: Store step result
     │
     ├─► track_cost (Activity)
     │   └─► PostgreSQL: Update cost totals
     │
     └─► update_workflow_status (Activity)
         └─► PostgreSQL: Mark complete

All activities publish events to Kafka ──► Kafka Topics
All activities emit traces ──► Jaeger
All activities log ──► Stdout (JSON)
```

## Prerequisites

### 1. OpenAI API Key

Get your API key from https://platform.openai.com/api-keys

```bash
export OPENAI_API_KEY="sk-..."
```

### 2. Infrastructure Running

Start all services:

```bash
cd /path/to/wflo
docker compose up -d
```

Verify health:

```bash
docker compose ps
# All services should show "Up (healthy)"
```

### 3. Database Migrations

Apply database schema:

```bash
poetry run alembic upgrade head
```

### 4. Python Dependencies

Install Wflo and dependencies:

```bash
poetry install
```

## Quick Start

### Basic Usage

```bash
poetry run python examples/simple_llm_agent/run.py \
  --prompt "What is 2+2?" \
  --budget 1.0
```

### Expected Output

```
🚀 Starting Wflo Simple LLM Agent Example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Configuration:
   Prompt: What is 2+2?
   Budget: $1.00
   Model: gpt-4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Connecting to Temporal...
✓ Workflow started (execution_id: abc-123-def-456)
✓ Calling OpenAI GPT-4...
✓ Response received (123 tokens)
✓ Cost tracked: $0.002
✓ Execution saved to database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Result:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2+2 equals 4. This is a basic arithmetic operation where
we add two identical numbers together.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Execution ID:    abc-123-def-456
Status:          COMPLETED
Duration:        1.23 seconds
Cost:            $0.002 USD
Budget Used:     0.2%
Tokens:          123 (prompt: 10, completion: 113)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Workflow completed successfully!

💡 Next Steps:
   - View in Temporal UI: http://localhost:8233
   - Check logs: docker compose logs -f temporal
   - View traces: http://localhost:16686 (Jaeger)
```

## Usage Examples

### 1. Simple Question

```bash
poetry run python examples/simple_llm_agent/run.py \
  --prompt "What is the capital of France?"
```

### 2. With Budget Limit

```bash
poetry run python examples/simple_llm_agent/run.py \
  --prompt "Explain quantum computing" \
  --budget 0.50
```

### 3. Custom Model

```bash
poetry run python examples/simple_llm_agent/run.py \
  --prompt "Write a haiku about AI" \
  --model "gpt-3.5-turbo"
```

### 4. Verbose Logging

```bash
export LOG_LEVEL=DEBUG
poetry run python examples/simple_llm_agent/run.py \
  --prompt "Hello, Wflo!"
```

## Code Walkthrough

### 1. Entry Point: `run.py`

```python
import asyncio
import click
from wflo.temporal.client import create_temporal_client
from examples.simple_llm_agent.workflow import execute_llm_workflow

@click.command()
@click.option("--prompt", required=True, help="Question for the LLM")
@click.option("--budget", default=1.0, help="Max cost in USD")
async def main(prompt: str, budget: float):
    # Create Temporal client
    client = await create_temporal_client()

    # Execute workflow
    result = await execute_llm_workflow(
        client=client,
        prompt=prompt,
        max_cost_usd=budget
    )

    # Display results
    print(f"Result: {result['output']}")
    print(f"Cost: ${result['cost']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Workflow Definition: `workflow.py`

```python
from temporalio import workflow
from wflo.temporal.activities import (
    save_workflow_execution,
    execute_llm_step,
    track_cost,
    update_workflow_status
)

@workflow.defn
class SimpleLLMWorkflow:
    @workflow.run
    async def run(self, prompt: str, max_cost_usd: float) -> dict:
        # 1. Save execution to database
        execution_id = await workflow.execute_activity(
            save_workflow_execution, ...
        )

        # 2. Call OpenAI
        llm_result = await workflow.execute_activity(
            execute_llm_step,
            args=[prompt, "gpt-4"],
            ...
        )

        # 3. Track cost
        await workflow.execute_activity(
            track_cost,
            args=[execution_id, llm_result.cost],
            ...
        )

        # 4. Update status
        await workflow.execute_activity(
            update_workflow_status,
            args=[execution_id, "COMPLETED"],
            ...
        )

        return llm_result
```

### 3. LLM Activity: `activities.py` (new)

```python
from temporalio import activity
from openai import AsyncOpenAI
from wflo.cost.tracker import CostTracker

@activity.defn
async def execute_llm_step(prompt: str, model: str) -> dict:
    # Call OpenAI
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Calculate cost
    tracker = CostTracker()
    cost = tracker.calculate_cost(
        model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens
    )

    return {
        "output": response.choices[0].message.content,
        "cost": float(cost),
        "tokens": response.usage.total_tokens
    }
```

## Monitoring & Debugging

### View Workflow in Temporal UI

1. Open http://localhost:8233
2. Find your workflow by execution ID
3. View timeline, events, and results

### Check Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f temporal

# Wflo application logs
docker compose logs -f temporal | grep "wflo"
```

### View Traces in Jaeger

1. Open http://localhost:16686
2. Select service: "wflo-temporal"
3. Find traces by execution ID
4. View detailed trace timeline

### Query Database

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U wflo_user -d wflo

# View executions
SELECT id, status, cost_total_usd, created_at
FROM workflow_executions
ORDER BY created_at DESC
LIMIT 10;

# View cost events
SELECT execution_id, cost_usd, model_name, created_at
FROM cost_events
ORDER BY created_at DESC
LIMIT 10;
```

### Check Kafka Events

```bash
# List topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume workflow events
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic wflo.workflows \
  --from-beginning
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500

# Wflo
DATABASE_URL=postgresql://wflo_user:wflo_password@localhost:5432/wflo
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
TEMPORAL_HOST=localhost:7233

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Load with:

```bash
source .env
poetry run python examples/simple_llm_agent/run.py --prompt "Hello"
```

## Error Handling

### Budget Exceeded

```bash
$ poetry run python examples/simple_llm_agent/run.py \
    --prompt "Write a 10,000 word essay" \
    --budget 0.01

❌ Error: Budget exceeded
   Requested: $0.05
   Budget: $0.01

   Tip: Increase budget or reduce request size
```

### API Key Missing

```bash
$ poetry run python examples/simple_llm_agent/run.py --prompt "Hello"

❌ Error: OPENAI_API_KEY environment variable not set

   Set your API key:
   export OPENAI_API_KEY="sk-..."

   Get API key: https://platform.openai.com/api-keys
```

### Infrastructure Not Running

```bash
$ poetry run python examples/simple_llm_agent/run.py --prompt "Hello"

❌ Error: Cannot connect to Temporal

   Start infrastructure:
   docker compose up -d

   Check status:
   docker compose ps
```

## Cost Estimates

Approximate costs for common prompts (GPT-4):

| Prompt Type | Example | Est. Cost |
|-------------|---------|-----------|
| Simple question | "What is 2+2?" | $0.001 |
| Short explanation | "Explain photosynthesis" | $0.005 |
| Code generation | "Write a Python function" | $0.010 |
| Long response | "Write an essay" | $0.050+ |

Actual costs depend on:
- Model selected (GPT-4 vs GPT-3.5)
- Prompt length
- Response length
- Current OpenAI pricing

## Troubleshooting

### Issue: "Workflow execution failed"

**Solution**: Check Temporal logs

```bash
docker compose logs temporal | grep ERROR
```

### Issue: "Database connection error"

**Solution**: Verify PostgreSQL is healthy

```bash
docker compose ps postgres
docker compose logs postgres
```

### Issue: "Cost tracking not working"

**Solution**: Verify migrations applied

```bash
poetry run alembic current
poetry run alembic upgrade head
```

### Issue: "OpenAI rate limit"

**Solution**: Add retry logic or reduce request rate

```python
# In workflow.py, increase retry attempts
retry_policy=RetryPolicy(
    maximum_attempts=5,  # Increase from 3
    initial_interval=timedelta(seconds=2),
)
```

## Next Steps

After running this example:

1. **Explore Variations**:
   - Try different prompts
   - Experiment with models (GPT-3.5 vs GPT-4)
   - Test budget limits

2. **View Monitoring**:
   - Temporal UI: http://localhost:8233
   - Jaeger tracing: http://localhost:16686
   - Check database records

3. **Modify Code**:
   - Add custom error handling
   - Implement response caching
   - Add additional workflow steps

4. **Next Examples**:
   - Multi-step agent (coming soon)
   - Sandbox execution (coming soon)
   - Human approval gates (coming soon)

## Related Documentation

- [Wflo Main Documentation](../../docs/)
- [Temporal Workflows Guide](../../docs/TEMPORAL.md)
- [Cost Tracking Guide](../../docs/phases/PHASE_1_COST_TRACKING.md)
- [Observability Guide](../../docs/phases/PHASE_2_OBSERVABILITY.md)

## Support

Questions or issues:
- Open an issue on GitHub
- Check documentation in `docs/`
- Review comprehensive assessment in `docs/COMPREHENSIVE_ASSESSMENT.md`

---

*Example Version: 1.0*
*Last Updated: 2025-11-11*
*Tested With: OpenAI API v1.3.0, Wflo v0.1.0*
