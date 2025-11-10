---
layout: default
title: Architecture
description: "Technical architecture and design decisions for Wflo"
---

<div class="container" style="margin-top: 3rem;">

# Architecture

Technical architecture for the secure AI agent runtime.

---

## Overview

Wflo is designed as a multi-layered orchestration platform that provides production-grade safety controls for AI agent workflows. The architecture prioritizes security, observability, and fault tolerance.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Python SDK   │  │   CLI Tool   │  │  REST API    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestration Engine                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Workflow Execution Layer                   │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │  Workflow   │ │   State     │ │   Event     │      │ │
│  │  │   Manager   │ │   Manager   │ │   Bus       │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                Safety & Governance Layer                │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │  Approval   │ │    Cost     │ │   Policy    │      │ │
│  │  │   Gates     │ │   Manager   │ │   Engine    │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │               Observability Layer                       │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │   Tracing   │ │   Metrics   │ │   Logging   │      │ │
│  │  │  (OTel)     │ │ (Prometheus)│ │  (Structured)│     │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Execution Runtime                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Sandbox 1  │  │  Sandbox 2  │  │  Sandbox N  │         │
│  │  (Docker)   │  │  (Docker)   │  │  (Docker)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Storage    │  │   Message   │  │    Cache    │         │
│  │  (Postgres) │  │   Queue     │  │   (Redis)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Workflow Manager

**Responsibilities:**
- Parse and validate workflow definitions
- Schedule workflow execution
- Manage workflow lifecycle (pending, running, completed, failed)
- Handle workflow versioning

**Key Design Decisions:**
- Workflows are defined as directed acyclic graphs (DAGs)
- Support for both synchronous and asynchronous execution
- Workflow definitions stored as YAML/Python code
- Immutable workflow versions for reproducibility

[See full details in ARCHITECTURE.md](https://github.com/wflo-ai/wflo/blob/main/docs/ARCHITECTURE.md#1-workflow-manager)

---

### 2. State Manager

**Responsibilities:**
- Maintain workflow execution state
- Provide state snapshots for rollback
- Handle state persistence and recovery
- Support distributed state coordination

**State Model:**
```python
@dataclass
class WorkflowState:
    workflow_id: str
    execution_id: str
    status: ExecutionStatus
    current_step: Optional[str]
    variables: Dict[str, Any]
    snapshots: List[StateSnapshot]
    created_at: datetime
    updated_at: datetime
```

**Snapshot Strategy:**
- Create snapshots before each critical step
- Configurable snapshot frequency (every step, key steps only)
- Automatic cleanup of old snapshots (retention policy)

---

### 3. Approval Gates

**Responsibilities:**
- Pause workflow execution at designated checkpoints
- Route approval requests to appropriate handlers
- Track approval status and audit trail
- Handle timeout and escalation policies

**Approval Flow:**
```
1. Workflow reaches approval gate
2. System pauses execution
3. Approval request sent to handler (webhook, UI, Slack)
4. Human reviews and approves/rejects
5. Workflow resumes or terminates based on decision
```

[See approval policy configuration →](features#approval-gates)

---

### 4. Cost Manager

**Responsibilities:**
- Track costs per workflow execution
- Enforce budget limits
- Provide cost estimates before execution
- Support multiple pricing providers

**Cost Tracking:**
- Real-time cost tracking for all LLM API calls
- Support for OpenAI, Anthropic, Cohere, Google
- Per-workflow and per-step cost attribution
- Historical cost analysis and trends

**Budget Enforcement:**
- Pre-execution cost estimation
- Real-time budget checking during execution
- Circuit breaker pattern to halt execution when budget exceeded
- Cost alerts at configurable thresholds (50%, 75%, 90%, 100%)

[See cost governance features →](features#cost-governance)

---

### 5. Sandbox Runtime

**Responsibilities:**
- Provide isolated execution environments
- Enforce resource limits
- Manage container lifecycle
- Handle file I/O safely

**Integration Options:**
- **Docker** - Standard container runtime (Phase 1)
- **E2B** - Specialized AI code execution sandboxes (Phase 2)
- **gVisor** - Enhanced container security (Phase 3)

**Security Features:**
- No network access by default (opt-in)
- Read-only filesystem with writable temp dir
- Resource limits enforced by container runtime
- Seccomp and AppArmor profiles

[See sandbox examples →](examples#sandbox-examples)

---

### 6. Observability System

**Responsibilities:**
- Collect traces for all workflow executions
- Emit metrics for monitoring and alerting
- Provide structured logging
- Support debugging and troubleshooting

**Tracing:**
- OpenTelemetry for distributed tracing
- Spans for each workflow step
- Correlation IDs across all components
- Export to Jaeger, Zipkin, or cloud providers

**Key Metrics:**
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
```

[See observability features →](features#observability)

---

### 7. Rollback System

**Responsibilities:**
- Create state snapshots at key points
- Restore previous states on failure or request
- Implement compensating transactions for external operations
- Provide rollback API for manual recovery

**Rollback Strategies:**

1. **State Rollback** (Internal) - Automatic snapshot before each step
2. **Compensating Transactions** (External) - Define undo operations for irreversible actions

[See rollback examples →](examples#rollback-on-failure)

---

## Data Models

### Workflow Definition

```python
@dataclass
class WorkflowDefinition:
    """Definition of a workflow."""
    name: str
    version: str
    steps: List[WorkflowStep]
    policies: WorkflowPolicies
    metadata: Dict[str, Any]

@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str
    type: StepType  # agent, tool, approval, condition
    config: Dict[str, Any]
    depends_on: List[str]  # Previous step IDs
    approval_required: bool = False
    rollback_enabled: bool = False
```

### Execution State

```python
@dataclass
class WorkflowExecution:
    """Running instance of a workflow."""
    id: str
    workflow_id: str
    status: ExecutionStatus
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    state: WorkflowState
    cost: CostSummary
    trace_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

---

## Technology Stack

### Core Platform
- **Language**: Python 3.11+
- **Async Framework**: asyncio + aiohttp
- **Type System**: mypy strict mode
- **Testing**: pytest + pytest-asyncio

### Infrastructure
- **Database**: PostgreSQL (workflow metadata, state)
- **Cache**: Redis (session state, locks)
- **Message Queue**: Redis Streams or RabbitMQ
- **Container Runtime**: Docker / containerd

### Observability
- **Tracing**: OpenTelemetry
- **Metrics**: Prometheus
- **Logging**: structlog + JSON formatting
- **APM**: Jaeger / Tempo

### Development
- **Package Manager**: Poetry
- **Code Quality**: ruff, black, mypy
- **CI/CD**: GitHub Actions
- **Documentation**: MkDocs Material

---

## Security Considerations

### 1. Sandbox Isolation
- No network access by default (opt-in)
- Read-only filesystem with writable temp dir
- Resource limits enforced by container runtime
- Seccomp and AppArmor profiles

### 2. Authentication & Authorization
- API key authentication for SDK/CLI
- OAuth 2.0 for web interface
- Role-based access control (RBAC)
- Audit logging for all operations

### 3. Data Protection
- Encryption at rest for sensitive data
- TLS for all network communication
- Secret management via environment variables
- PII scrubbing in logs

### 4. Supply Chain Security
- Dependency scanning with Dependabot
- SBOM generation
- Signed container images
- Reproducible builds

---

## Scalability Design

### Horizontal Scaling
- Stateless orchestration engine (scale workers)
- Distributed state via Redis
- Load balancing across sandbox runners
- Workflow execution queue for backpressure

### Performance Targets
- Workflow submission: < 100ms p99
- Sandbox creation: < 2s p99
- Approval gate latency: < 500ms p99 (notification delivery)
- Support 1000 concurrent workflow executions

---

## Future Enhancements

### Phase 2
- Multi-agent collaboration protocols
- Workflow marketplace and templates
- Visual workflow designer (web UI)
- Advanced cost optimization (model routing)

### Phase 3
- Federated workflow execution (multi-region)
- On-premise deployment option
- Compliance certifications (SOC2, HIPAA)
- Enterprise SSO integration

---

## Architecture Decision Records

For detailed rationale on specific design decisions, see:
- [ADR-001: Choice of Python over Go](https://github.com/wflo-ai/wflo/blob/main/docs/adr/001-python-language.md) (coming soon)
- [ADR-002: PostgreSQL for state storage](https://github.com/wflo-ai/wflo/blob/main/docs/adr/002-postgres-state.md) (coming soon)
- [ADR-003: OpenTelemetry for observability](https://github.com/wflo-ai/wflo/blob/main/docs/adr/003-otel.md) (coming soon)

---

## Additional Resources

- [Full Architecture Document](https://github.com/wflo-ai/wflo/blob/main/docs/ARCHITECTURE.md)
- [Features Documentation](features)
- [Getting Started Guide](getting-started)
- [Examples](examples)

---

**Last Updated**: 2025-11-09
**Status**: Living Document - Updated as architecture evolves
</div>
