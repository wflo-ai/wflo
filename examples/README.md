# wflo Examples & Tutorials

Comprehensive examples demonstrating how to use wflo with various AI frameworks and workflows.

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Framework Integrations](#framework-integrations)
- [Advanced Examples](#advanced-examples)
- [Feature Demonstrations](#feature-demonstrations)
- [Best Practices](#best-practices)

## 🚀 Quick Start

### Installation

```bash
pip install wflo
```

### Basic Usage

```python
import asyncio
from wflo.sdk.workflow import WfloWorkflow
from wflo.sdk.decorators.track_llm import track_llm_call

@track_llm_call(model="gpt-4")
async def my_llm_function(prompt: str):
    # Your LLM call here
    pass

async def main():
    workflow = WfloWorkflow(
        name="my-workflow",
        budget_usd=1.0,  # $1 budget
    )

    result = await workflow.execute(my_llm_function, {"prompt": "Hello!"})

    # Check costs
    breakdown = await workflow.get_cost_breakdown()
    print(f"Spent: ${breakdown['total_usd']:.4f}")

asyncio.run(main())
```

## 🔗 Framework Integrations

### LangGraph

**Location**: `langgraph_integration/`

LangGraph is a library for building stateful, multi-actor applications with LLMs.

**Examples:**
- `basic_graph.py` - Simple LangGraph workflow without wflo
- `wflo_wrapped_simple.py` - LangGraph with wflo budget tracking
- `wflo_wrapped_graph.py` - Advanced multi-step LangGraph workflow

**Key Features:**
- Automatic detection of LangGraph workflows (via `ainvoke` method)
- State persistence across graph nodes
- Budget enforcement across all LLM calls in the graph

**Usage:**
```python
from langgraph.graph import StateGraph
from wflo.sdk.workflow import WfloWorkflow

# Create your LangGraph
graph = StateGraph(...)
compiled_graph = graph.compile()

# Wrap with wflo
workflow = WfloWorkflow(name="my-graph", budget_usd=2.0)
result = await workflow.execute(compiled_graph, {"input": "data"})
```

**Run Example:**
```bash
poetry run python examples/langgraph_integration/wflo_wrapped_simple.py
```

### CrewAI

**Location**: `crewai_integration/`

CrewAI enables orchestration of role-playing, autonomous AI agents.

**Examples:**
- `basic_crew.py` - CrewAI crew without wflo
- `wflo_wrapped_crew.py` - CrewAI with wflo orchestration

**Key Features:**
- Automatic detection of CrewAI crews (via `kickoff` method)
- Budget tracking across all agent interactions
- Checkpoint support for multi-agent workflows

**Usage:**
```python
from crewai import Agent, Task, Crew
from wflo.sdk.workflow import WfloWorkflow

# Create your crew
crew = Crew(agents=[...], tasks=[...])

# Wrap with wflo
workflow = WfloWorkflow(name="my-crew", budget_usd=5.0)
result = await workflow.execute(crew, {})
```

**Run Example:**
```bash
poetry run python examples/crewai_integration/wflo_wrapped_crew.py
```

### OpenAI Direct

**Location**: `openai_direct/`

Direct integration with OpenAI's API for function calling and chat completions.

**Examples:**
- `basic_function_calling.py` - OpenAI function calling without wflo
- `wflo_wrapped_function_calling.py` - Function calling with wflo tracking
- `wflo_wrapped_simple.py` - Simple chat completion with wflo

**Key Features:**
- Automatic token counting for all OpenAI models
- Cost calculation using latest pricing
- Support for GPT-4, GPT-3.5, o1, and other models

**Run Example:**
```bash
export OPENAI_API_KEY=your-key-here
poetry run python examples/openai_direct/wflo_wrapped_simple.py
```

### Anthropic Claude

**Location**: `anthropic_direct/`

Direct integration with Anthropic's Claude API for tool use and chat.

**Examples:**
- `basic_claude_tool_use.py` - Claude tool calling without wflo

**Key Features:**
- Support for Claude 3.5 Sonnet, Opus, and Haiku
- Automatic token tracking for Anthropic models
- Tool use / function calling support

### AutoGen (Microsoft)

**Location**: `autogen_integration/`

AutoGen enables creation of conversational AI agents that can work together.

**Examples:**
- `basic_conversation.py` - Simple AutoGen conversation without wflo
- `wflo_wrapped_conversation.py` - AutoGen with wflo orchestration

**Key Features:**
- Track costs across multi-agent conversations
- Budget enforcement for agent interactions
- Checkpoint support for conversation states

**Run Example:**
```bash
export OPENAI_API_KEY=your-key-here
poetry run python examples/autogen_integration/wflo_wrapped_conversation.py
```

## 🎯 Advanced Examples

### Multi-Step Research Workflow

**Location**: `advanced/multi_step_research_workflow.py`

A comprehensive example demonstrating all Phase 1 SDK features in a realistic multi-step workflow.

**Features Demonstrated:**
- ✅ Multi-step workflow orchestration
- ✅ Checkpoint creation at each step
- ✅ Budget enforcement across steps
- ✅ LLM call tracking and cost analysis
- ✅ Rollback capability
- ✅ Execution tracing

**Workflow Steps:**
1. **Planning** - Plan research approach (checkpoint: `research_planning`)
2. **Execution** - Conduct research on key areas (checkpoint: `research_execution`)
3. **Synthesis** - Synthesize findings into summary (checkpoint: `synthesis`)

**Run Example:**
```bash
export OPENAI_API_KEY=your-key-here
poetry run python examples/advanced/multi_step_research_workflow.py
```

## 🎨 Feature Demonstrations

### 1. Budget Enforcement

**What it does:** Prevents workflows from exceeding cost limits.

**Example:**
```python
workflow = WfloWorkflow(
    name="budget-demo",
    budget_usd=0.10,  # Very low budget
)

try:
    result = await workflow.execute(expensive_llm_workflow, inputs)
except BudgetExceededError as e:
    print(f"Budget exceeded! Spent: ${e.spent_usd:.4f}, Limit: ${e.budget_usd:.2f}")
```

### 2. LLM Call Tracking

**What it does:** Automatically tracks tokens and costs for 400+ LLM models.

**Example:**
```python
from wflo.sdk.decorators.track_llm import track_llm_call

@track_llm_call(model="gpt-4")
async def my_llm_call(prompt: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response
# Tokens and cost automatically tracked!
```

### 3. Checkpointing & Rollback

**What it does:** Save workflow state at any point and rollback if needed.

**Example:**
```python
from wflo.sdk.decorators.checkpoint import checkpoint

@checkpoint(name="data_processing")
async def process_data(data):
    # Process data
    return processed_data

# Later, if analysis has issues:
previous_state = await workflow.rollback_to_checkpoint("data_processing")
```

## 📖 Best Practices

### 1. Always Set Budgets

```python
# ✅ GOOD: Explicit budget
workflow = WfloWorkflow(name="workflow", budget_usd=2.0)
```

### 2. Use Checkpoints for Multi-Step Workflows

```python
@checkpoint(name="step1")
async def step_one():
    return await expensive_operation()

@checkpoint(name="step2")
async def step_two(state):
    return await another_expensive_operation(state)
```

### 3. Track All LLM Calls

```python
@track_llm_call(model="gpt-4")
async def my_function():
    response = await client.chat.completions.create(...)
    return response
```

## 🔧 Environment Setup

### Required Environment Variables

```bash
# OpenAI (for OpenAI, LangGraph, AutoGen examples)
export OPENAI_API_KEY=your-openai-api-key

# Anthropic (for Claude examples)
export ANTHROPIC_API_KEY=your-anthropic-api-key

# Database (for checkpoint persistence)
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/wflo
```

## 📚 Additional Resources

- **Documentation**: https://docs.wflo.ai
- **GitHub**: https://github.com/wflo-ai/wflo
- **Discord Community**: https://discord.gg/wflo

---

*Last Updated: 2025-11-11*
