---
layout: default
title: Examples
description: "Code examples and tutorials for building workflows with Wflo"
---

<div class="container" style="margin-top: 3rem;">

# Examples

Practical code examples to help you build production-ready AI agent workflows.

---

## Basic Examples

### Hello World

The simplest possible workflow:

```python
from wflo import Workflow

workflow = Workflow("hello-world")

@workflow.step
async def greet(context):
    name = context.inputs.get("name", "World")
    return {"message": f"Hello, {name}!"}

__workflow__ = workflow
```

Run it:

```bash
wflo run hello.py --input name="Alice"
# Output: {"message": "Hello, Alice!"}
```

---

### Multi-Step Workflow

Workflow with dependencies:

```python
from wflo import Workflow

workflow = Workflow("multi-step")

@workflow.step
async def step_one(context):
    """First step"""
    return {"data": "processed by step 1"}

@workflow.step(depends_on=["step_one"])
async def step_two(context):
    """Second step depends on first"""
    data = context.steps["step_one"].output["data"]
    return {"result": f"{data} + step 2"}

@workflow.step(depends_on=["step_two"])
async def step_three(context):
    """Third step depends on second"""
    result = context.steps["step_two"].output["result"]
    return {"final": f"{result} + step 3"}

__workflow__ = workflow
```

---

### Parallel Execution

Steps that can run in parallel:

```python
from wflo import Workflow

workflow = Workflow("parallel-processing")

@workflow.step
async def fetch_data_source_1(context):
    """Fetch from source 1"""
    data = await context.api.fetch("https://api1.example.com/data")
    return {"data": data}

@workflow.step  # No depends_on, can run in parallel
async def fetch_data_source_2(context):
    """Fetch from source 2"""
    data = await context.api.fetch("https://api2.example.com/data")
    return {"data": data}

@workflow.step(depends_on=["fetch_data_source_1", "fetch_data_source_2"])
async def merge_data(context):
    """Merge data from both sources"""
    data1 = context.steps["fetch_data_source_1"].output["data"]
    data2 = context.steps["fetch_data_source_2"].output["data"]
    return {"merged": data1 + data2}

__workflow__ = workflow
```

---

## LLM Integration Examples

### Simple LLM Call

Using LLMs with automatic cost tracking:

```python
from wflo import Workflow

workflow = Workflow("llm-example")
workflow.set_budget(max_cost_usd=1.00)

@workflow.step
async def analyze_sentiment(context):
    """Analyze sentiment with GPT"""
    text = context.inputs["text"]

    result = await context.llm.complete(
        model="gpt-3.5-turbo",
        prompt=f"Analyze the sentiment of: {text}",
        max_tokens=50
    )

    return {
        "sentiment": result.text,
        "cost": result.cost,
        "tokens": result.tokens
    }

__workflow__ = workflow
```

---

### Streaming LLM Responses

Stream responses for better UX:

```python
from wflo import Workflow

workflow = Workflow("streaming-llm")

@workflow.step
async def generate_essay(context):
    """Generate essay with streaming"""
    topic = context.inputs["topic"]

    essay_parts = []
    total_cost = 0

    async for chunk in context.llm.stream(
        model="gpt-4",
        prompt=f"Write a detailed essay about: {topic}",
        max_tokens=1000
    ):
        essay_parts.append(chunk.text)
        total_cost += chunk.cost

        # Log progress
        context.logger.info(
            "essay_chunk",
            length=len(chunk.text),
            total_length=sum(len(p) for p in essay_parts)
        )

    return {
        "essay": "".join(essay_parts),
        "cost": total_cost
    }

__workflow__ = workflow
```

---

### Multi-Model Comparison

Compare outputs from different models:

```python
from wflo import Workflow

workflow = Workflow("model-comparison")

@workflow.step
async def query_gpt4(context):
    """Query GPT-4"""
    question = context.inputs["question"]

    result = await context.llm.complete(
        model="gpt-4",
        prompt=question
    )

    return {"answer": result.text, "cost": result.cost}

@workflow.step
async def query_claude(context):
    """Query Claude"""
    question = context.inputs["question"]

    result = await context.llm.complete(
        model="claude-3-opus",
        prompt=question
    )

    return {"answer": result.text, "cost": result.cost}

@workflow.step(depends_on=["query_gpt4", "query_claude"])
async def compare_answers(context):
    """Compare both answers"""
    gpt4 = context.steps["query_gpt4"].output
    claude = context.steps["query_claude"].output

    comparison = await context.llm.complete(
        model="gpt-3.5-turbo",
        prompt=f"""
        Compare these two answers:
        GPT-4: {gpt4['answer']}
        Claude: {claude['answer']}

        Which is better and why?
        """
    )

    return {
        "gpt4": gpt4,
        "claude": claude,
        "comparison": comparison.text,
        "total_cost": gpt4["cost"] + claude["cost"] + comparison.cost
    }

__workflow__ = workflow
```

---

## Safety Control Examples

### Budget Limits with Alerts

```python
from wflo import Workflow

workflow = Workflow("budget-controlled")

# Set budget with multiple alert thresholds
workflow.set_budget(
    max_cost_usd=10.00,
    alert_thresholds=[0.5, 0.75, 0.9],
    action_on_exceeded="halt"
)

# Alert handler
@workflow.on_budget_alert
async def budget_alert(cost_info):
    await context.notify(
        channel="slack://ops",
        message=f"⚠️ Budget at {cost_info.percent}%: ${cost_info.current}/${cost_info.limit}"
    )

# Exceeded handler
@workflow.on_budget_exceeded
async def budget_exceeded(cost_info):
    await context.notify(
        channel="pagerduty://ops",
        message=f"🚨 Budget exceeded: ${cost_info.current}/${cost_info.limit}"
    )
    # Workflow halts automatically

@workflow.step
async def expensive_operation(context):
    """Operation that might exceed budget"""
    # Cost is tracked automatically
    result = await context.llm.complete(
        model="gpt-4",
        prompt=context.inputs["prompt"],
        max_tokens=2000
    )

    return {"result": result.text}

__workflow__ = workflow
```

---

### Approval Gates

```python
from wflo import Workflow, ApprovalPolicy

workflow = Workflow("approval-example")

@workflow.step
async def prepare_data(context):
    """Prepare data for deletion"""
    records = await context.db.query(
        "SELECT * FROM records WHERE created_at < NOW() - INTERVAL '1 year'"
    )

    return {
        "record_count": len(records),
        "records": records
    }

@workflow.step(
    depends_on=["prepare_data"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["admin", "data-team"],
        timeout_seconds=7200,  # 2 hours
        escalation=["cto"],
        notify=[
            "slack://data-team",
            "email://data-team@company.com"
        ]
    )
)
async def delete_old_records(context):
    """Delete records (requires approval)"""
    records = context.steps["prepare_data"].output["records"]

    # Execution pauses here until approved
    # If timeout, escalates to CTO
    # If rejected, workflow terminates

    deleted = await context.db.bulk_delete(records)

    return {"deleted_count": deleted}

__workflow__ = workflow
```

---

### Rollback on Failure

```python
from wflo import Workflow

workflow = Workflow("rollback-example")

@workflow.step(rollback_enabled=True)
async def update_production_database(context):
    """Update production data with automatic rollback"""

    # Snapshot created automatically here
    updates = context.inputs["updates"]

    try:
        # Apply updates
        await context.db.bulk_update(updates)

        # Validate updates worked
        validation = await context.db.validate_data_integrity()

        if not validation.passed:
            raise ValueError(f"Data integrity check failed: {validation.errors}")

        return {"updated": len(updates)}

    except Exception as e:
        # Automatically rolls back to snapshot
        context.logger.error("update_failed", error=str(e))
        raise

__workflow__ = workflow
```

---

### Compensating Transactions

For operations that can't be rolled back directly:

```python
from wflo import Workflow, CompensatingAction

workflow = Workflow("compensating-actions")

@workflow.step
async def send_promotional_emails(context):
    """Send promotional emails to customers"""
    customers = context.inputs["customers"]

    # Send emails
    sent = await context.email.send_bulk(
        recipients=customers,
        subject="Special Offer!",
        body=context.inputs["email_body"]
    )

    # Define compensating action
    context.add_compensating_action(
        CompensatingAction(
            name="send_apology_email",
            handler=lambda: context.email.send_bulk(
                recipients=customers,
                subject="Apology",
                body="Please disregard our previous email."
            ),
            metadata={"sent_count": len(sent)}
        )
    )

    return {"sent": len(sent)}

@workflow.step(depends_on=["send_promotional_emails"])
async def update_campaign_stats(context):
    """Update campaign statistics"""
    sent = context.steps["send_promotional_emails"].output["sent"]

    try:
        await context.db.execute(
            "UPDATE campaigns SET emails_sent = emails_sent + ?",
            sent
        )
    except Exception as e:
        # If this fails, execute compensating action
        await context.execute_compensating_actions()
        raise

    return {"updated": True}

__workflow__ = workflow
```

---

## Sandbox Examples

### Basic Sandbox Execution

```python
from wflo import Workflow, SandboxConfig

workflow = Workflow("sandbox-example")

workflow.configure_sandbox(
    SandboxConfig(
        enabled=True,
        memory_limit="512m",
        cpu_limit="0.5",
        timeout_seconds=300,
        network_enabled=False
    )
)

@workflow.step
async def run_untrusted_code(context):
    """Execute user-provided code in sandbox"""
    user_code = context.inputs["code"]

    # Code executes in isolated container
    # Cannot access host filesystem
    # Cannot make network requests
    # Limited CPU/memory
    result = await context.sandbox.execute(
        code=user_code,
        language="python"
    )

    return {
        "output": result.stdout,
        "errors": result.stderr,
        "exit_code": result.exit_code
    }

__workflow__ = workflow
```

---

### Sandbox with Network Access

```python
from wflo import Workflow, SandboxConfig

workflow = Workflow("sandbox-with-network")

workflow.configure_sandbox(
    SandboxConfig(
        enabled=True,
        network_enabled=True,
        allowed_domains=["api.example.com"],  # Whitelist
        blocked_domains=["evil.com"]  # Blacklist
    )
)

@workflow.step
async def fetch_external_data(context):
    """Fetch data from external API in sandbox"""
    result = await context.sandbox.execute(
        code="""
        import requests
        response = requests.get('https://api.example.com/data')
        print(response.json())
        """,
        language="python"
    )

    return {"data": result.stdout}

__workflow__ = workflow
```

---

## Advanced Examples

### Conditional Execution

```python
from wflo import Workflow, Condition

workflow = Workflow("conditional-execution")

@workflow.step
async def analyze_data(context):
    """Analyze data quality"""
    data = context.inputs["data"]

    quality_score = await context.llm.evaluate(
        data=data,
        criteria="Data quality score 0-100"
    )

    return {"quality_score": int(quality_score.text)}

@workflow.step(
    depends_on=["analyze_data"],
    condition=Condition("context.steps['analyze_data'].output['quality_score'] > 80")
)
async def process_high_quality_data(context):
    """Only runs if quality > 80"""
    return {"processed": "high quality path"}

@workflow.step(
    depends_on=["analyze_data"],
    condition=Condition("context.steps['analyze_data'].output['quality_score'] <= 80")
)
async def improve_data_quality(context):
    """Only runs if quality <= 80"""
    return {"processed": "quality improvement path"}

__workflow__ = workflow
```

---

### Dynamic Workflow Generation

```python
from wflo import Workflow

async def create_dynamic_workflow(num_steps: int):
    """Create workflow with dynamic number of steps"""
    workflow = Workflow("dynamic-workflow")

    previous_step = None

    for i in range(num_steps):
        step_name = f"step_{i}"

        @workflow.step(
            name=step_name,
            depends_on=[previous_step] if previous_step else []
        )
        async def dynamic_step(context, step_num=i):
            """Dynamically created step"""
            result = await context.llm.complete(
                model="gpt-3.5-turbo",
                prompt=f"Process step {step_num}"
            )
            return {"step": step_num, "result": result.text}

        previous_step = step_name

    return workflow

# Create workflow with 5 steps
workflow = await create_dynamic_workflow(5)
```

---

### Error Handling and Retry

```python
from wflo import Workflow, RetryPolicy

workflow = Workflow("retry-example")

@workflow.step(
    retry=RetryPolicy(
        max_attempts=3,
        backoff_multiplier=2,
        initial_delay=1,
        max_delay=10
    )
)
async def flaky_api_call(context):
    """API call with automatic retry"""
    try:
        result = await context.api.fetch("https://flaky-api.example.com/data")
        return {"data": result}

    except Exception as e:
        context.logger.warning(
            "api_call_failed",
            error=str(e),
            attempt=context.retry_count
        )
        raise  # Will retry automatically

__workflow__ = workflow
```

---

### State Persistence

```python
from wflo import Workflow

workflow = Workflow("stateful-workflow")

@workflow.step
async def initialize_state(context):
    """Initialize workflow state"""
    context.state["counter"] = 0
    context.state["results"] = []

    return {"initialized": True}

@workflow.step(depends_on=["initialize_state"])
async def process_batch_1(context):
    """Process first batch"""
    result = await process_data(context.inputs["batch1"])

    # Update state
    context.state["counter"] += 1
    context.state["results"].append(result)

    return {"batch": 1, "result": result}

@workflow.step(depends_on=["process_batch_1"])
async def process_batch_2(context):
    """Process second batch"""
    result = await process_data(context.inputs["batch2"])

    # Access previous state
    context.state["counter"] += 1
    context.state["results"].append(result)

    return {
        "batch": 2,
        "result": result,
        "total_batches": context.state["counter"],
        "all_results": context.state["results"]
    }

__workflow__ = workflow
```

---

### Integration with External Tools

```python
from wflo import Workflow

workflow = Workflow("integration-example")

@workflow.step
async def fetch_from_database(context):
    """Fetch data from PostgreSQL"""
    result = await context.db.query(
        "SELECT * FROM users WHERE active = true"
    )
    return {"users": result}

@workflow.step(depends_on=["fetch_from_database"])
async def cache_results(context):
    """Cache in Redis"""
    users = context.steps["fetch_from_database"].output["users"]

    await context.cache.set(
        key="active_users",
        value=users,
        ttl=3600
    )
    return {"cached": True}

@workflow.step(depends_on=["cache_results"])
async def publish_event(context):
    """Publish to message queue"""
    await context.queue.publish(
        topic="users.updated",
        message={
            "event": "active_users_cached",
            "count": len(context.steps["fetch_from_database"].output["users"])
        }
    )
    return {"published": True}

@workflow.step(depends_on=["publish_event"])
async def notify_slack(context):
    """Notify Slack channel"""
    await context.notify(
        channel="slack://data-team",
        message="✅ User cache updated successfully"
    )
    return {"notified": True}

__workflow__ = workflow
```

---

## Testing Workflows

### Unit Testing

```python
import pytest
from wflo.testing import WorkflowTestContext

@pytest.mark.asyncio
async def test_workflow():
    """Test a workflow"""
    from workflows.example import workflow

    # Create test context
    context = WorkflowTestContext(
        inputs={"name": "Test User"}
    )

    # Run workflow
    result = await workflow.run(context)

    # Assert results
    assert result.status == "completed"
    assert "greeting" in result.outputs
    assert result.outputs["greeting"] == "Hello, Test User!"
    assert result.cost < 0.01

@pytest.mark.asyncio
async def test_approval_workflow():
    """Test workflow with approval"""
    from workflows.approval_example import workflow

    context = WorkflowTestContext(
        inputs={"data": [1, 2, 3]},
        auto_approve=True  # Auto-approve for testing
    )

    result = await workflow.run(context)

    assert result.status == "completed"
```

---

## Next Steps

- [Features](features) - Explore all features in detail
- [API Reference](api-reference) - Complete API documentation
- [Use Cases](use-cases) - Real-world applications
- [Best Practices](best-practices) - Production deployment tips
</div>
