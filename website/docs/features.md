---
sidebar_position: 3
title: Features
description: Comprehensive overview of Wflo's core features
---

# Features

Production-grade infrastructure for running AI agents safely and reliably.

## Sandboxed Execution

Every workflow runs in an isolated container environment with strict resource limits.

```python
workflow.configure_sandbox(
    memory_limit="512m",
    cpu_limit="0.5",
    network_enabled=False,
    timeout_seconds=300
)
```

**Benefits:**
- Process isolation
- Resource limits
- Network controls
- Filesystem isolation

## Human Approval Gates

Pause workflows at critical checkpoints and require human approval.

```python
@workflow.step(
    approval=ApprovalPolicy(
        required=True,
        approvers=["ops-team"],
        notify=["slack://ops-channel"]
    )
)
async def delete_production_data(context):
    # Execution pauses here for approval
    await context.db.execute("DELETE FROM ...")
```

**Features:**
- Configurable approvers
- Timeout policies
- Escalation chains
- Complete audit trails

## Cost Governance

Real-time cost tracking with automatic budget enforcement.

```python
workflow.set_budget(
    max_cost_usd=50.00,
    alert_thresholds=[0.5, 0.75, 0.9],
    action_on_exceeded="halt"
)
```

**Capabilities:**
- Multi-provider tracking
- Budget alerts
- Cost attribution
- Automatic halts

## Rollback & Recovery

Automatic state snapshots and recovery mechanisms.

```python
@workflow.step(rollback_enabled=True)
async def update_database(context):
    # Snapshot created automatically
    await context.db.update(records)
    # Auto-rollback on failure
```

**Features:**
- Automatic snapshots
- Point-in-time recovery
- Compensating transactions
- Manual rollback API

## Full Observability

Complete visibility into agent behavior.

```python
# Every operation is traced:
- Workflow execution timeline
- LLM API calls with costs
- Database queries
- Error details and stack traces
```

**Stack:**
- OpenTelemetry tracing
- Prometheus metrics
- Structured logging
- Correlation IDs

## Policy Engine

Define complex policies for approval routing and controls.

```python
workflow.add_policy(
    Policy(
        name="high_cost_approval",
        condition=Condition("estimated_cost > 100"),
        actions=[
            RequireApproval(approvers=["finance-team"]),
            Notify("slack://finance-channel")
        ]
    )
)
```

## Next Steps

- [Getting Started](./getting-started.md) - Set up your first workflow
- [Examples](./examples.md) - See code examples
- [Architecture](./architecture.md) - Technical details
