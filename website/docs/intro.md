---
sidebar_position: 1
title: Introduction
description: Welcome to Wflo - The secure runtime for AI agents
---

# Introduction

Welcome to **Wflo** - the secure runtime for AI agents.

## What is Wflo?

Wflo provides production-ready infrastructure for running AI agents safely. It's designed to solve the critical problems that prevent AI agents from being deployed in production environments:

- **Runaway costs** - Budget controls and real-time cost tracking
- **Security concerns** - Sandboxed execution with resource limits
- **Irreversible actions** - Rollback capabilities and state snapshots
- **Poor observability** - Complete traces, metrics, and logs
- **Compliance gaps** - Audit trails and human approval gates

## Key Features

### 🛡️ Sandboxed Execution
Every workflow runs in an isolated container environment with strict resource limits. No agent can access your host system or escape its sandbox.

### ✋ Human Approval Gates
Pause workflows at critical checkpoints and require human approval before proceeding. Define who can approve, set timeouts, and configure escalation policies.

### 💰 Cost Governance
Real-time cost tracking across all LLM providers with automatic budget enforcement. Set spending limits and get alerted before you exceed them.

### ⏮️ Rollback & Recovery
Automatic state snapshots before critical operations. Roll back to any previous state if something goes wrong.

### 📈 Full Observability
Distributed tracing, metrics, and structured logging for every workflow execution. Know exactly what your agents are doing.

## Why Wflo?

AI agents are powerful, but running them in production is risky. Wflo is built from the ground up with safety as the primary concern:

- **Safe by default** - Not bolted on as an afterthought
- **Production-ready** - Not just demos and prototypes
- **Observable** - You know exactly what agents are doing
- **Governable** - Compliance and cost controls from day one
- **Recoverable** - Mistakes are fixable, not fatal

## Quick Example

```python
from wflo import Workflow, ApprovalPolicy

workflow = Workflow("data-processor")
workflow.set_budget(max_cost_usd=25.00)

@workflow.step(approval=ApprovalPolicy(required=True))
async def delete_data(context):
    """Requires approval before execution"""
    await context.db.execute("DELETE FROM ...")

# Run with safety controls
result = await workflow.run(
    sandbox=True,
    trace=True,
    notify="slack://ops"
)
```

## Status

:::caution Early Development

Wflo is in active development and not production-ready yet. We're building in public - star the repo to follow our progress!

:::

## Next Steps

- [Get Started](./getting-started.md) - Set up your first workflow
- [Features](./features.md) - Explore all features
- [Examples](./examples.md) - See more code examples
- [Architecture](./architecture.md) - Understand how it works
