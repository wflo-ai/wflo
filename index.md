---
layout: default
title: Home
nav_order: 1
description: "Wflo - The secure runtime for AI agents. Production-ready infrastructure for running AI agents safely with sandboxed execution, cost governance, and human approval gates."
permalink: /
---

# Wflo
{: .fs-9 }

The secure runtime for AI agents
{: .fs-6 .fw-300 }

Production-ready infrastructure for running AI agents safely: sandboxed execution, human approval gates, cost governance, rollback capabilities, and full observability.
{: .fs-5 .fw-300 }

[Get Started](#quick-start){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/wflo-ai/wflo){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Why Wflo?

AI agents are powerful, but running them in production is risky:

| Problem | Impact |
|:--------|:-------|
| 💸 **Runaway costs** | One misconfigured agent can burn thousands in API fees |
| 🔒 **Security concerns** | Agents executing arbitrary code without isolation |
| 🚫 **Irreversible actions** | No way to undo agent mistakes |
| 📊 **Poor observability** | Can't debug what agents actually did |
| ⚖️ **Compliance gaps** | No audit trails for regulated industries |

**Wflo solves these problems.**

---

## Core Features

### 🛡️ Sandboxed Execution

- Isolated container environments for each agent workflow
- Resource limits (CPU, memory, network)
- Filesystem isolation and security policies
- Based on proven container isolation technology

[Learn more →](docs/features#sandboxed-execution)

### ✋ Human Approval Gates

- Configurable checkpoints before critical operations
- Risk-based approval routing (auto-approve low-risk, require human for high-risk)
- Approval timeout policies and escalation
- Complete audit trail of all approvals/rejections

[Learn more →](docs/features#approval-gates)

### 💰 Cost Governance

- Budget limits per workflow, agent, or time period
- Real-time cost tracking and alerts
- Circuit breakers when budgets exceeded
- Multi-provider cost attribution and optimization

[Learn more →](docs/features#cost-governance)

### ⏮️ Rollback & Recovery

- State snapshots before critical operations
- Automatic rollback on failures
- Compensating transactions for external APIs
- Point-in-time recovery capabilities

[Learn more →](docs/features#rollback-recovery)

### 📈 Full Observability

- Complete execution traces for every agent action
- Real-time metrics: latency, cost, token usage
- Structured logs with correlation IDs
- Integration with popular observability tools

[Learn more →](docs/features#observability)

---

## Quick Start

```bash
# Install Wflo CLI
pip install wflo

# Initialize a new workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 --require-approval
```

[Full getting started guide →](docs/getting-started)

---

## Example: Safe Agent Workflow

```python
from wflo import Workflow, ApprovalGate, CostLimit

# Define a workflow with built-in safety
workflow = Workflow("data-processor")

# Set cost budget
workflow.set_budget(max_cost_usd=50.00)

# Add approval gate before destructive operations
@workflow.step(approval_required=True)
async def delete_old_records(context):
    """This will pause and wait for human approval"""
    await context.db.execute("DELETE FROM records WHERE age > 365")

# Add rollback capability
@workflow.step(rollback_enabled=True)
async def update_production_data(context):
    """Automatic rollback on failure"""
    snapshot = await context.db.snapshot()
    try:
        await context.db.bulk_update(records)
    except Exception:
        await context.db.restore(snapshot)
        raise

# Run with observability
result = await workflow.run(
    sandbox=True,           # Run in isolated container
    trace=True,            # Full execution tracing
    notify="slack://prod"  # Alert on approval needed
)
```

[See more examples →](docs/examples)

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         Wflo Orchestration Engine           │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Workflow │  │  Policy  │  │   Cost   │ │
│  │  Engine  │  │  Engine  │  │  Manager │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Observability Layer              │  │
│  │  (Traces, Metrics, Logs, Audit)      │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │  Sandbox 1  │  │  Sandbox 2  │
    │   (Agent)   │  │   (Agent)   │
    └─────────────┘  └─────────────┘
```

[Full architecture documentation →](docs/architecture)

---

## Use Cases

- **Financial Services**: Run fraud detection agents with mandatory approval gates
- **Healthcare**: HIPAA-compliant agent workflows with full audit trails
- **E-commerce**: Customer service automation with cost controls
- **Data Processing**: ETL agents with rollback on failures
- **DevOps**: Infrastructure automation with human oversight

[Explore use cases →](docs/use-cases)

---

## Roadmap

### Phase 1: Foundation (Current)
- [x] Project setup and architecture design
- [ ] Core workflow engine
- [ ] Sandbox execution (Docker/E2B integration)
- [ ] Basic observability (traces, logs)
- [ ] Python SDK

### Phase 2: Safety & Governance
- [ ] Human approval gates (API + UI)
- [ ] Cost tracking and budget enforcement
- [ ] Policy engine (define approval rules)
- [ ] Rollback for state operations

### Phase 3: Production Ready
- [ ] Multi-agent orchestration
- [ ] Advanced observability (OpenTelemetry)
- [ ] Compliance features (SOC2, HIPAA audit logs)
- [ ] TypeScript/JavaScript SDK
- [ ] Cloud platform (hosted service)

---

## Philosophy

We believe AI agents should be:

- **Safe by default** - Not bolted on as an afterthought
- **Production-ready** - Not just demos and prototypes
- **Observable** - You should know exactly what agents are doing
- **Governable** - Compliance and cost controls from day one
- **Recoverable** - Mistakes should be fixable, not fatal

---

## Community

- **GitHub Discussions**: [Share ideas and ask questions](https://github.com/wflo-ai/wflo/discussions)
- **Issues**: [Report bugs or request features](https://github.com/wflo-ai/wflo/issues)
- **Discord**: Join our community (coming soon)
- **Twitter**: [@wflo_ai](https://twitter.com/wflo_ai) (coming soon)

---

## Contributing

We welcome contributions! Wflo is open-source and community-driven.

[Read the contributing guide →](docs/contributing)

---

## Status

🚧 **Early Development** - Not production ready yet

We're actively building in public. Star the repo to follow our progress!

---

## License

Apache 2.0 - See [LICENSE](https://github.com/wflo-ai/wflo/blob/main/LICENSE) for details.

---

## Acknowledgments

Built with inspiration from:
- **Kubernetes** - Container orchestration patterns
- **Temporal** - Durable workflow execution
- **LangChain/LangGraph** - Agent framework ecosystem
- **E2B** - Secure code execution sandboxes
