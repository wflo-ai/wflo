---
layout: default
title: Home
description: "Wflo - The secure runtime for AI agents. Production-ready infrastructure for running AI agents safely."
---

<div class="hero">
  <div class="container">
    <h1>wflo</h1>
    <p class="tagline">The secure runtime for AI agents</p>
    <p class="subtitle">Production-ready infrastructure for running AI agents safely with sandboxed execution, human approval gates, cost governance, and full observability.</p>
    <div class="cta-buttons">
      <a href="#quick-start" class="btn btn-primary">Get Started</a>
      <a href="https://github.com/wflo-ai/wflo" class="btn btn-secondary">View on GitHub</a>
    </div>
  </div>
</div>

<section>
  <div class="container">
    <h2>The Problem</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-icon">💸</div>
        <h3>Runaway Costs</h3>
        <p>One misconfigured agent can burn thousands in API fees before you notice.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <h3>Security Risks</h3>
        <p>Agents executing arbitrary code without isolation puts your systems at risk.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🚫</div>
        <h3>Irreversible Actions</h3>
        <p>No way to undo mistakes when agents make wrong decisions.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>No Visibility</h3>
        <p>Can't debug what agents actually did or why they made certain decisions.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">⚖️</div>
        <h3>Compliance Gaps</h3>
        <p>No audit trails or approval workflows for regulated industries.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <h3>The Solution</h3>
        <p>Wflo provides enterprise-grade safety controls for production AI workflows.</p>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <h2>Core Features</h2>

    <h3>🛡️ Sandboxed Execution</h3>
    <p>Every workflow runs in an isolated container environment with strict resource limits. No agent can access your host system or escape its sandbox.</p>

```python
workflow.configure_sandbox(
    memory_limit="512m",
    cpu_limit="0.5",
    network_enabled=False,
    timeout_seconds=300
)
```

    <h3>✋ Human Approval Gates</h3>
    <p>Pause workflows at critical checkpoints and require human approval before proceeding. Define who can approve, set timeouts, and configure escalation policies.</p>

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

    <h3>💰 Cost Governance</h3>
    <p>Real-time cost tracking across all LLM providers with automatic budget enforcement. Set spending limits and get alerted before you exceed them.</p>

```python
workflow.set_budget(
    max_cost_usd=50.00,
    alert_thresholds=[0.5, 0.75, 0.9],
    action_on_exceeded="halt"
)
```

    <h3>⏮️ Rollback & Recovery</h3>
    <p>Automatic state snapshots before critical operations. Roll back to any previous state if something goes wrong.</p>

```python
@workflow.step(rollback_enabled=True)
async def update_database(context):
    # Snapshot created automatically
    await context.db.update(records)
    # Auto-rollback on failure
```

    <h3>📈 Full Observability</h3>
    <p>Distributed tracing, metrics, and structured logging for every workflow execution. Know exactly what your agents are doing.</p>

```python
# Every operation is traced
- Workflow execution timeline
- LLM API calls with costs
- Database queries
- Error details and stack traces
```

  </div>
</section>

<section id="quick-start">
  <div class="container">
    <h2>Quick Start</h2>

```bash
# Install
pip install wflo

# Create workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 --require-approval
```

    <h3>Example Workflow</h3>

```python
from wflo import Workflow

workflow = Workflow("data-processor")
workflow.set_budget(max_cost_usd=25.00)

@workflow.step
async def fetch_data(context):
    """Fetch data from database"""
    results = await context.db.query(context.inputs["query"])
    return {"data": results}

@workflow.step(depends_on=["fetch_data"])
async def analyze_with_ai(context):
    """Analyze with LLM"""
    data = context.steps["fetch_data"].output["data"]

    analysis = await context.llm.complete(
        model="gpt-4",
        prompt=f"Analyze: {data}"
    )

    return {"analysis": analysis.text, "cost": analysis.cost}

@workflow.step(
    depends_on=["analyze_with_ai"],
    approval=ApprovalPolicy(required=True),
    rollback_enabled=True
)
async def apply_changes(context):
    """Apply changes (requires approval + rollback)"""
    # Execution pauses for approval
    # Auto-rollback if fails
    await context.db.execute(changes)
    return {"applied": True}
```

  </div>
</section>

<section>
  <div class="container">
    <h2>Architecture</h2>

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
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │  Sandbox 1  │  │  Sandbox 2  │
    │   (Agent)   │  │   (Agent)   │
    └─────────────┘  └─────────────┘
```

  </div>
</section>

<section>
  <div class="container">
    <h2>Use Cases</h2>

    <table>
      <thead>
        <tr>
          <th>Industry</th>
          <th>Use Case</th>
          <th>Key Feature</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Financial Services</td>
          <td>Fraud detection with approval gates</td>
          <td>Human review before blocking accounts</td>
        </tr>
        <tr>
          <td>Healthcare</td>
          <td>Clinical decision support</td>
          <td>HIPAA-compliant audit trails</td>
        </tr>
        <tr>
          <td>E-commerce</td>
          <td>Customer service automation</td>
          <td>Approval required for refunds</td>
        </tr>
        <tr>
          <td>Data Engineering</td>
          <td>ETL pipelines</td>
          <td>Rollback on data quality issues</td>
        </tr>
        <tr>
          <td>DevOps</td>
          <td>Infrastructure automation</td>
          <td>Approval gates for prod changes</td>
        </tr>
      </tbody>
    </table>

    <p style="text-align: center; margin-top: 2rem;">
      <a href="{{ '/docs/use-cases' | relative_url }}" class="btn btn-secondary">View All Use Cases →</a>
    </p>
  </div>
</section>

<section>
  <div class="container">
    <h2>Roadmap</h2>

    <h3>Phase 1: Foundation (Current)</h3>
    <ul>
      <li>✅ Project setup and architecture design</li>
      <li>Core workflow engine</li>
      <li>Sandbox execution</li>
      <li>Basic observability</li>
      <li>Python SDK</li>
    </ul>

    <h3>Phase 2: Safety & Governance</h3>
    <ul>
      <li>Human approval gates</li>
      <li>Cost tracking and budget enforcement</li>
      <li>Policy engine</li>
      <li>Rollback capabilities</li>
    </ul>

    <h3>Phase 3: Production Ready</h3>
    <ul>
      <li>Multi-agent orchestration</li>
      <li>Advanced observability</li>
      <li>Compliance features (SOC2, HIPAA)</li>
      <li>TypeScript/JavaScript SDK</li>
      <li>Hosted cloud platform</li>
    </ul>

    <div class="status-badge">Early Development - Not production ready yet</div>
  </div>
</section>

<section>
  <div class="container">
    <h2>Community</h2>

    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-icon">💬</div>
        <h3>Discussions</h3>
        <p><a href="https://github.com/wflo-ai/wflo/discussions">Share ideas and ask questions</a></p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🐛</div>
        <h3>Issues</h3>
        <p><a href="https://github.com/wflo-ai/wflo/issues">Report bugs or request features</a></p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🤝</div>
        <h3>Contributing</h3>
        <p><a href="{{ '/docs/contributing' | relative_url }}">Help build the future of AI safety</a></p>
      </div>
    </div>
  </div>
</section>
