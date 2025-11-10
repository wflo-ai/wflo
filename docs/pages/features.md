---
layout: default
title: Features
description: "Comprehensive overview of Wflo's core features for secure AI agent orchestration"
---

<div class="container" style="margin-top: 3rem;">

# Features

Production-grade infrastructure for running AI agents safely and reliably.

## Sandboxed Execution

Wflo runs every AI agent workflow in an isolated container environment, ensuring security and resource control.

### Key Capabilities

- **Container Isolation**: Each workflow runs in its own Docker container with strict isolation
- **Resource Limits**: Configure CPU, memory, and network limits per workflow
- **Filesystem Controls**: Read-only root filesystem with writable temp directories
- **Network Policies**: Network access disabled by default, opt-in for specific workflows
- **Security Profiles**: Seccomp and AppArmor profiles for defense-in-depth

### Example Configuration

```python
from wflo import Workflow, SandboxConfig

workflow = Workflow("secure-processor")

workflow.configure_sandbox(
    SandboxConfig(
        memory_limit="512m",
        cpu_limit="0.5",
        network_enabled=False,
        timeout_seconds=300,
        readonly_root=True
    )
)
```

### Security Benefits

| Feature | Benefit |
|:--------|:--------|
| Process isolation | Malicious code cannot escape container |
| Resource limits | Prevent DoS from runaway processes |
| Network controls | Prevent data exfiltration |
| Filesystem isolation | Protect host system files |

---

## Approval Gates

Human-in-the-loop checkpoints ensure critical operations require explicit approval before execution.

### Approval Workflow

1. **Workflow reaches approval gate**: Execution pauses automatically
2. **Notification sent**: Alert sent via configured channels (Slack, email, webhook)
3. **Human reviews**: Reviewer examines context and proposed action
4. **Decision made**: Approve to continue or reject to halt workflow
5. **Audit logged**: Complete record of who approved/rejected and when

### Configuration Options

```python
from wflo import ApprovalPolicy

@workflow.step(
    approval=ApprovalPolicy(
        required=True,
        approvers=["admin", "ops-team"],
        timeout_seconds=3600,
        escalation=["manager"],
        notify=["slack://ops-channel", "email://ops@company.com"]
    )
)
async def delete_production_data(context):
    """Requires approval before execution"""
    await context.db.execute("DELETE FROM production_table WHERE ...")
```

### Risk-Based Routing

Automatically route approvals based on risk level:

```python
workflow.set_approval_rules([
    # High-risk: require manual approval
    ApprovalRule(
        condition="cost > 100 OR operation == 'delete'",
        require_approval=True,
        approvers=["senior-ops"]
    ),
    # Medium-risk: auto-approve with logging
    ApprovalRule(
        condition="cost > 10",
        require_approval=False,
        audit_log=True
    ),
    # Low-risk: auto-approve
    ApprovalRule(
        condition="*",
        require_approval=False
    )
])
```

### Timeout & Escalation

- **Timeout Policies**: Automatically reject or escalate after configured time
- **Escalation Chain**: Route to higher authority if not approved in time
- **Approval Expiry**: Approvals expire after set duration for stale workflows

---

## Cost Governance

Real-time cost tracking and budget enforcement prevent runaway spending on LLM APIs.

### Cost Tracking

Wflo automatically tracks costs from:

- **OpenAI**: GPT-4, GPT-3.5, embeddings
- **Anthropic**: Claude 3 models
- **Cohere**: Command, Embed models
- **Google**: PaLM, Gemini
- **Custom**: Define your own pricing models

### Budget Limits

```python
from wflo import BudgetPolicy

workflow.set_budget(
    BudgetPolicy(
        max_cost_usd=50.00,
        alert_thresholds=[0.5, 0.75, 0.9],  # Alert at 50%, 75%, 90%
        action_on_exceeded="halt",  # halt, alert, or ignore
        reset_period="daily"  # daily, weekly, monthly, or none
    )
)
```

### Cost Attribution

Track costs at multiple levels:

- **Per workflow**: Total cost for a workflow execution
- **Per step**: Cost breakdown by individual steps
- **Per user**: Aggregate costs by user or team
- **Per time period**: Daily, weekly, monthly spending

### Budget Alerts

```python
workflow.on_budget_alert(
    threshold=0.75,
    handler=lambda cost: notify_slack(
        f"⚠️ Workflow at 75% of budget: ${cost.current}/${cost.limit}"
    )
)

workflow.on_budget_exceeded(
    handler=lambda cost: [
        notify_pagerduty("Budget exceeded!"),
        workflow.halt()
    ]
)
```

### Cost Optimization

- **Model routing**: Automatically use cheaper models when possible
- **Caching**: Cache LLM responses to avoid duplicate API calls
- **Cost estimation**: Estimate costs before workflow execution
- **Provider comparison**: Compare costs across different LLM providers

---

## Rollback & Recovery

State snapshots and compensating transactions enable recovery from failures and mistakes.

### Automatic Snapshots

```python
@workflow.step(rollback_enabled=True)
async def update_database(context):
    """Automatic snapshot created before execution"""
    # Snapshot created here automatically
    await context.db.update(records)
    # On failure, automatically rolls back to snapshot
```

### Manual Snapshots

```python
async def complex_operation(context):
    # Create snapshot at specific point
    snapshot = await context.create_snapshot("before-critical-op")

    try:
        await perform_risky_operation()
    except Exception:
        # Restore to snapshot
        await context.restore_snapshot(snapshot.id)
        raise
```

### Compensating Transactions

For operations that can't be rolled back (external APIs, emails sent), define compensating actions:

```python
from wflo import CompensatingAction

@workflow.step
async def send_email_campaign(context):
    # Send emails
    result = await email_service.send_bulk(recipients, message)

    # Define how to undo this operation
    context.add_compensating_action(
        CompensatingAction(
            name="unsend_emails",
            handler=lambda: email_service.send_bulk(
                recipients,
                "Please disregard previous email"
            )
        )
    )

    return result

# Later, if workflow fails:
await context.execute_compensating_actions()  # Sends correction emails
```

### Point-in-Time Recovery

```python
# List available snapshots
snapshots = await workflow.list_snapshots()

# Restore to specific snapshot
await workflow.restore_to_snapshot(snapshots[0].id)

# Restore to specific timestamp
await workflow.restore_to_time("2025-01-15T10:30:00Z")
```

---

## Observability

Complete visibility into agent behavior with distributed tracing, metrics, and structured logging.

### Distributed Tracing

Wflo uses OpenTelemetry for distributed tracing:

```python
from wflo import TracingConfig

workflow.configure_tracing(
    TracingConfig(
        enabled=True,
        exporter="jaeger",  # jaeger, zipkin, otlp
        endpoint="http://jaeger:14268/api/traces",
        sample_rate=1.0  # Trace 100% of workflows
    )
)
```

**Trace information includes:**
- Workflow execution timeline
- Step-by-step execution
- LLM API calls with tokens and costs
- Database queries
- External API calls
- Error details and stack traces

### Metrics

Key metrics exported to Prometheus:

```python
# Workflow metrics
wflo_workflow_executions_total{status="success|failed"}
wflo_workflow_duration_seconds{workflow_name}
wflo_workflow_cost_usd{workflow_name}

# Approval metrics
wflo_approval_requests_total{status="approved|rejected|timeout"}
wflo_approval_latency_seconds

# Sandbox metrics
wflo_sandbox_creation_duration_seconds
wflo_sandbox_cpu_usage_percent{sandbox_id}
wflo_sandbox_memory_usage_bytes{sandbox_id}

# Cost metrics
wflo_llm_api_calls_total{provider, model}
wflo_llm_tokens_total{provider, model, type="input|output"}
wflo_budget_exceeded_total{workflow_name}
```

### Structured Logging

All logs use structured JSON format:

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "info",
  "message": "workflow_started",
  "workflow_id": "wf_abc123",
  "execution_id": "exec_xyz789",
  "user_id": "user_123",
  "trace_id": "trace_456",
  "span_id": "span_789"
}
```

### Correlation IDs

Every request gets a unique correlation ID that flows through all logs, traces, and metrics:

```python
# All related events share the same trace_id
logger.info("step_started", trace_id="abc123", step="process_data")
logger.info("llm_call", trace_id="abc123", model="gpt-4", tokens=150)
logger.info("step_completed", trace_id="abc123", step="process_data", duration=2.5)
```

### Debugging

Debug workflow executions with full context:

```bash
# View workflow execution details
wflo debug exec_xyz789

# Show execution trace
wflo trace exec_xyz789

# View logs for specific execution
wflo logs exec_xyz789 --follow

# Export trace to file
wflo trace exec_xyz789 --export trace.json
```

---

## Policy Engine

Define complex policies for approval routing, cost limits, and execution controls.

### Policy Examples

```python
from wflo import Policy, Condition

# Require approval for high-cost operations
high_cost_policy = Policy(
    name="high_cost_approval",
    condition=Condition("estimated_cost > 100"),
    actions=[
        RequireApproval(approvers=["finance-team"]),
        Notify("slack://finance-channel")
    ]
)

# Limit workflow execution time
timeout_policy = Policy(
    name="execution_timeout",
    condition=Condition("execution_time > 600"),
    actions=[
        HaltExecution(),
        Notify("pagerduty://ops")
    ]
)

# Restrict network access
network_policy = Policy(
    name="no_network_default",
    condition=Condition("workflow.network_enabled == true"),
    actions=[
        RequireApproval(approvers=["security-team"]),
        AuditLog(severity="high")
    ]
)

workflow.add_policies([
    high_cost_policy,
    timeout_policy,
    network_policy
])
```

---

## Integration

Wflo integrates with popular tools and services:

### Observability Tools

- **Jaeger / Zipkin**: Distributed tracing
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Datadog / New Relic**: APM platforms
- **Sentry**: Error tracking

### Notification Channels

- **Slack**: Approval requests and alerts
- **Email**: SMTP-based notifications
- **PagerDuty**: Incident management
- **Webhooks**: Custom integrations
- **SMS**: Twilio integration

### Storage Backends

- **PostgreSQL**: Workflow state and metadata
- **Redis**: Caching and session state
- **S3**: Artifact storage
- **MinIO**: Self-hosted object storage

### Authentication

- **API Keys**: Simple token-based auth
- **OAuth 2.0**: Social login and SSO
- **LDAP**: Enterprise directory integration
- **Custom**: Plug in your own auth provider

---

## Next Steps

- [Getting Started Guide](getting-started) - Set up your first workflow
- [Architecture](architecture) - Understand how Wflo works
- [Examples](examples) - More code examples

</div>
