---
sidebar_position: 1
title: Introduction
description: Welcome to wflo - Production orchestration for AI agent workflows
---

# Introduction

Welcome to **wflo** - production orchestration for AI agent workflows.

## What is wflo?

wflo provides production-ready orchestration infrastructure for AI agent workflows. It's designed to solve the critical problems that prevent AI agents from being deployed in production environments:

- **Runaway costs** - Budget controls and real-time cost tracking across 400+ LLM models
- **No visibility** - Complete execution tracking, cost breakdown, and observability
- **Lost progress** - Checkpoint and rollback capabilities for long-running workflows
- **Framework lock-in** - Works with LangGraph, CrewAI, AutoGen, OpenAI, Anthropic, and more
- **Cost attribution** - Track exactly how much each workflow execution costs

## Key Features (Phase 1 - Production Ready)

### 💰 Budget Enforcement

Set strict cost limits for workflows. Execution automatically halts if budget is exceeded.

```python
from wflo.sdk.workflow import WfloWorkflow, BudgetExceededError

workflow = WfloWorkflow(
    name="my-workflow",
    budget_usd=2.0,  # $2 maximum
)

try:
    result = await workflow.execute(my_agent_workflow, inputs)
except BudgetExceededError as e:
    print(f"Budget exceeded: ${e.spent_usd:.4f} > ${e.budget_usd:.2f}")
```

### 📊 LLM Call Tracking

Automatic token counting and cost calculation for 400+ models across all major providers.

```python
from wflo.sdk.decorators.track_llm import track_llm_call

@track_llm_call(model="gpt-4")
async def my_llm_function(prompt: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response
# Tokens and cost automatically tracked!
```

**Supported Providers:**
- OpenAI (GPT-4, GPT-3.5, o1, o3-mini)
- Anthropic (Claude 3.5 Sonnet, Opus, Haiku)
- Google (Gemini Pro, Flash)
- Meta (Llama 3)
- Mistral AI
- And 400+ more models

### ⏮️ Checkpointing & Rollback

Save workflow state at any point and rollback if needed. Perfect for long-running workflows.

```python
from wflo.sdk.decorators.checkpoint import checkpoint

@checkpoint(name="data_processed")
async def process_data(data):
    # Process data...
    return processed_data

@checkpoint(name="analysis_complete")
async def analyze_data(processed_data):
    # Analyze...
    return analysis

# If analysis has issues, rollback to previous state
previous_state = await workflow.rollback_to_checkpoint("data_processed")
```

### 🔗 Multi-Framework Support

Works seamlessly with popular AI frameworks - no code changes required.

```python
# LangGraph
from langgraph.graph import StateGraph

graph = StateGraph(...)
compiled_graph = graph.compile()

workflow = WfloWorkflow(name="langgraph-workflow", budget_usd=5.0)
result = await workflow.execute(compiled_graph, {"input": "data"})
# Automatically detects LangGraph, tracks all LLM calls, enforces budget

# CrewAI
from crewai import Agent, Task, Crew

crew = Crew(agents=[...], tasks=[...])

workflow = WfloWorkflow(name="crewai-workflow", budget_usd=10.0)
result = await workflow.execute(crew, {})
# Automatically detects CrewAI crew, tracks costs

# OpenAI Direct
async def my_openai_workflow(inputs):
    # Your OpenAI calls...
    pass

workflow = WfloWorkflow(name="openai-workflow", budget_usd=1.0)
result = await workflow.execute(my_openai_workflow, {"prompt": "..."})
```

### 🔍 Execution Tracking

Every workflow execution gets a unique ID for tracking and debugging.

```python
result = await workflow.execute(my_workflow, inputs)

# Get execution ID
execution_id = workflow.execution_id  # e.g., "exec-a1b2c3d4e5f6"

# Get cost breakdown
breakdown = await workflow.get_cost_breakdown()
print(f"Total: ${breakdown['total_usd']:.4f}")
print(f"Budget: ${breakdown['budget_usd']:.2f}")
print(f"Remaining: ${breakdown['remaining_usd']:.4f}")

# Query database for full execution details
# SELECT * FROM workflow_executions WHERE id = execution_id;
```

## Why wflo?

AI agents are powerful, but running them in production requires careful cost management and observability. wflo provides:

- **Production-ready** - Fully tested with 133 unit tests (100% pass rate)
- **Framework agnostic** - Works with LangGraph, CrewAI, AutoGen, and direct API calls
- **Cost control** - Never exceed your budget, with real-time tracking
- **Observable** - Know exactly what your agents are doing and how much it costs
- **Recoverable** - Checkpoint and rollback for long-running workflows

## Quick Start

```bash
# Install wflo
pip install wflo

# Set up database (PostgreSQL)
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/wflo

# Run example
export OPENAI_API_KEY=your-key-here
python examples/openai_direct/wflo_wrapped_simple.py
```

## Phase 1 Features (✅ Production Ready)

- ✅ Budget enforcement with `BudgetExceededError`
- ✅ LLM call tracking for 400+ models
- ✅ Cost calculation across all major providers
- ✅ Checkpoint/rollback capability
- ✅ Multi-framework support (LangGraph, CrewAI, AutoGen, OpenAI, Anthropic)
- ✅ Execution tracking and tracing
- ✅ PostgreSQL state persistence
- ✅ Async/await throughout
- ✅ Comprehensive testing (133 tests passing)

## Upcoming Features (Phase 2+)

- 🔄 Retry manager with exponential backoff
- 🛡️ Circuit breaker for tool failures
- 🚦 Resource contention detection
- 🗳️ Consensus voting for multi-agent decisions
- 🏖️ Sandboxed code execution
- ✋ Human approval gates
- 📈 Advanced observability (OpenTelemetry, Prometheus)
- 🔐 Supabase integration for authentication

## Status

wflo Phase 1 SDK is **production-ready** and fully tested. The core features for cost management, tracking, and checkpointing are stable and ready for use.

## Next Steps

- [Getting Started](./getting-started.md) - Build your first wflo workflow
- [Features](./features/overview.md) - Explore all Phase 1 features
- [Examples](./examples.md) - See comprehensive code examples
- [Architecture](./architecture/overview.md) - Understand how it works
