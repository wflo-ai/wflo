---
layout: default
title: Getting Started
nav_order: 3
description: "Quick start guide to building your first secure AI agent workflow with Wflo"
permalink: /docs/getting-started
---

# Getting Started
{: .no_toc }

Get up and running with Wflo in minutes.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Docker** installed and running (for sandbox execution)
- **API keys** for LLM providers (OpenAI, Anthropic, etc.)
- **Git** for cloning the repository

---

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

### Verify Installation

```bash
wflo --version
# Output: wflo version 0.1.0
```

---

## Quick Start

### 1. Initialize a New Project

```bash
# Create a new workflow project
wflo init my-agent-workflow
cd my-agent-workflow
```

This creates the following structure:

```
my-agent-workflow/
├── wflo.yaml           # Workflow configuration
├── workflows/          # Workflow definitions
│   └── example.py
├── .env               # Environment variables (API keys)
└── README.md
```

### 2. Configure API Keys

Edit `.env` to add your API keys:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Wflo Configuration
WFLO_DB_URL=postgresql://localhost/wflo
WFLO_REDIS_URL=redis://localhost:6379
```

### 3. Create Your First Workflow

Create `workflows/hello_world.py`:

```python
from wflo import Workflow, step

# Define a workflow
workflow = Workflow("hello-world")

# Set basic safety controls
workflow.set_budget(max_cost_usd=1.00)

@workflow.step
async def greet(context):
    """Simple greeting step"""
    name = context.inputs.get("name", "World")
    message = f"Hello, {name}!"

    # Log the message
    context.logger.info("greeting_generated", message=message)

    return {"greeting": message}

@workflow.step(depends_on=["greet"])
async def analyze_sentiment(context):
    """Analyze sentiment of greeting"""
    greeting = context.steps["greet"].output["greeting"]

    # Call LLM (cost tracked automatically)
    result = await context.llm.complete(
        model="gpt-3.5-turbo",
        prompt=f"Analyze the sentiment of this message: {greeting}"
    )

    return {"sentiment": result.text, "cost": result.cost}

# Export the workflow
__workflow__ = workflow
```

### 4. Run the Workflow

```bash
# Run the workflow
wflo run workflows/hello_world.py --input name="Alice"
```

Output:

```
✓ Workflow started: hello-world (exec_abc123)
✓ Step completed: greet (0.1s)
  Output: {"greeting": "Hello, Alice!"}
✓ Step completed: analyze_sentiment (1.2s)
  Output: {"sentiment": "positive", "cost": 0.0005}
✓ Workflow completed (1.3s, $0.0005)
```

---

## Adding Safety Controls

### Budget Limits

Prevent runaway costs:

```python
workflow.set_budget(
    max_cost_usd=10.00,
    alert_thresholds=[0.5, 0.75, 0.9],
    action_on_exceeded="halt"
)

# Alert when budget threshold reached
@workflow.on_budget_alert
async def budget_alert(cost_info):
    print(f"⚠️ Budget alert: ${cost_info.current}/${cost_info.limit}")
```

### Approval Gates

Require human approval for critical operations:

```python
from wflo import ApprovalPolicy

@workflow.step(
    approval=ApprovalPolicy(
        required=True,
        approvers=["admin"],
        timeout_seconds=3600,
        notify=["slack://ops-channel"]
    )
)
async def delete_data(context):
    """Requires approval before execution"""
    records_to_delete = context.inputs["records"]

    # This step will pause here and wait for approval
    # User will be notified via Slack
    await context.db.delete(records_to_delete)

    return {"deleted": len(records_to_delete)}
```

### Sandbox Execution

Run workflows in isolated containers:

```python
from wflo import SandboxConfig

workflow.configure_sandbox(
    SandboxConfig(
        enabled=True,
        memory_limit="512m",
        cpu_limit="0.5",
        timeout_seconds=300,
        network_enabled=False  # Disable network access
    )
)

@workflow.step
async def process_untrusted_code(context):
    """Runs in isolated sandbox"""
    code = context.inputs["user_code"]

    # Code executes in isolated container
    # Cannot access host filesystem or network
    result = await context.sandbox.execute(code)

    return {"output": result}
```

### Rollback Capability

Enable automatic rollback on failures:

```python
@workflow.step(rollback_enabled=True)
async def update_production(context):
    """Automatic rollback on failure"""
    # Snapshot created automatically before execution
    await context.db.update(production_data)

    # If this raises an exception, state rolls back
    # to the snapshot automatically
```

---

## Example: Real-World Workflow

Here's a complete example of a data processing workflow with all safety features:

```python
from wflo import Workflow, ApprovalPolicy, SandboxConfig
from wflo.models import WorkflowInput, WorkflowOutput

workflow = Workflow(
    name="data-processor",
    version="1.0.0",
    description="Process customer data with safety controls"
)

# Configure safety controls
workflow.set_budget(max_cost_usd=25.00)
workflow.configure_sandbox(
    SandboxConfig(
        enabled=True,
        memory_limit="1g",
        cpu_limit="1.0",
        timeout_seconds=600
    )
)

# Step 1: Fetch data
@workflow.step
async def fetch_customer_data(context):
    """Fetch data from database"""
    query = context.inputs["query"]

    # Query database
    results = await context.db.query(query)

    context.logger.info(
        "data_fetched",
        record_count=len(results)
    )

    return {"customers": results}

# Step 2: Analyze with AI (in sandbox)
@workflow.step(depends_on=["fetch_customer_data"])
async def analyze_data(context):
    """Analyze customer data with LLM"""
    customers = context.steps["fetch_customer_data"].output["customers"]

    # Run analysis in sandbox for security
    analysis = await context.llm.complete(
        model="gpt-4",
        prompt=f"Analyze these customer patterns: {customers}",
        max_tokens=500
    )

    return {
        "analysis": analysis.text,
        "cost": analysis.cost
    }

# Step 3: Generate recommendations
@workflow.step(depends_on=["analyze_data"])
async def generate_recommendations(context):
    """Generate action recommendations"""
    analysis = context.steps["analyze_data"].output["analysis"]

    recommendations = await context.llm.complete(
        model="gpt-4",
        prompt=f"Based on this analysis, suggest actions: {analysis}",
        max_tokens=300
    )

    return {
        "recommendations": recommendations.text,
        "cost": recommendations.cost
    }

# Step 4: Apply changes (requires approval + rollback)
@workflow.step(
    depends_on=["generate_recommendations"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["ops-team", "data-team"],
        timeout_seconds=7200,
        notify=["slack://ops-channel", "email://ops@company.com"]
    ),
    rollback_enabled=True
)
async def apply_recommendations(context):
    """Apply recommendations to production (requires approval)"""
    recommendations = context.steps["generate_recommendations"].output

    # This pauses and waits for human approval
    # Snapshot created automatically before execution

    # Apply changes
    results = await context.db.execute(
        recommendations["recommendations"]
    )

    return {"applied": True, "results": results}

# Step 5: Notify completion
@workflow.step(depends_on=["apply_recommendations"])
async def notify_completion(context):
    """Send completion notification"""
    total_cost = sum(
        step.output.get("cost", 0)
        for step in context.steps.values()
    )

    await context.notify(
        channel="slack://ops-channel",
        message=f"✅ Data processing completed. Total cost: ${total_cost:.4f}"
    )

    return {"notified": True}

# Export workflow
__workflow__ = workflow
```

### Run the Workflow

```bash
wflo run workflows/data_processor.py \
    --input query="SELECT * FROM customers WHERE active=true" \
    --sandbox \
    --trace
```

---

## Monitoring & Debugging

### View Workflow Status

```bash
# List all workflow executions
wflo list

# Get status of specific execution
wflo status exec_abc123

# Watch execution in real-time
wflo status exec_abc123 --follow
```

### View Logs

```bash
# View logs for execution
wflo logs exec_abc123

# Follow logs in real-time
wflo logs exec_abc123 --follow

# Filter logs by level
wflo logs exec_abc123 --level error
```

### View Traces

```bash
# Show execution trace
wflo trace exec_abc123

# Export trace to file
wflo trace exec_abc123 --export trace.json

# Open trace in Jaeger UI
wflo trace exec_abc123 --ui
```

### View Cost Breakdown

```bash
# Show cost breakdown
wflo cost exec_abc123

# Output:
# Step                    | Model         | Tokens | Cost
# ----------------------- | ------------- | ------ | --------
# analyze_data           | gpt-4         | 650    | $0.0195
# generate_recommendations| gpt-4         | 450    | $0.0135
# ----------------------- | ------------- | ------ | --------
# Total                   |               | 1100   | $0.0330
```

---

## Handling Approvals

### Approve via CLI

```bash
# List pending approvals
wflo approvals

# Approve a workflow step
wflo approve exec_abc123 --step apply_recommendations

# Reject with reason
wflo reject exec_abc123 --step apply_recommendations --reason "Budget concerns"
```

### Approve via API

```bash
# Approve via HTTP API
curl -X POST https://wflo.example.com/api/v1/approvals/approve \
  -H "Authorization: Bearer $WFLO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "exec_abc123",
    "step_id": "apply_recommendations",
    "approved": true,
    "approver": "alice@company.com",
    "comment": "Looks good, approved"
  }'
```

---

## Configuration

### Workflow Configuration File

Create `wflo.yaml` in your project root:

```yaml
# Wflo Configuration
version: 1

# Default settings for all workflows
defaults:
  # Budget settings
  budget:
    max_cost_usd: 50.00
    alert_thresholds: [0.5, 0.75, 0.9]
    action_on_exceeded: halt

  # Sandbox settings
  sandbox:
    enabled: true
    memory_limit: "512m"
    cpu_limit: "0.5"
    timeout_seconds: 300
    network_enabled: false

  # Observability
  tracing:
    enabled: true
    exporter: jaeger
    endpoint: "http://localhost:14268/api/traces"
    sample_rate: 1.0

  metrics:
    enabled: true
    exporter: prometheus
    endpoint: "http://localhost:9090"

# Database configuration
database:
  url: "postgresql://localhost/wflo"
  pool_size: 10

# Cache configuration
cache:
  url: "redis://localhost:6379"
  ttl: 3600

# Notification channels
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
    default_channel: "#ops"

  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from_address: "wflo@company.com"

# Authentication
auth:
  api_keys:
    - name: "dev-key"
      key: "sk_dev_..."
      permissions: ["read", "write"]
```

---

## Next Steps

Now that you've created your first workflow, explore more advanced features:

- [Features](features) - Comprehensive feature documentation
- [Architecture](architecture) - How Wflo works under the hood
- [Examples](examples) - More workflow examples
- [API Reference](api-reference) - Complete API documentation
- [Best Practices](best-practices) - Production deployment guide

---

## Getting Help

- **Documentation**: [wflo-ai.github.io/wflo](https://wflo-ai.github.io/wflo)
- **GitHub Issues**: [github.com/wflo-ai/wflo/issues](https://github.com/wflo-ai/wflo/issues)
- **Discussions**: [github.com/wflo-ai/wflo/discussions](https://github.com/wflo-ai/wflo/discussions)
- **Discord**: Join our community (coming soon)
