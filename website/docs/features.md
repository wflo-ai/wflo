---
sidebar_position: 3
title: Features
description: Comprehensive overview of wflo's Phase 1 features
---

# Features

Production-grade orchestration for AI agent workflows with cost control, checkpointing, and multi-framework support.

## Phase 1 Features (Production Ready)

### 💰 Budget Enforcement

Set strict cost limits and automatically halt execution if exceeded.

```python
from wflo.sdk.workflow import WfloWorkflow, BudgetExceededError

workflow = WfloWorkflow(
    name="my-workflow",
    budget_usd=2.0,  # $2 maximum spend
)

try:
    result = await workflow.execute(my_workflow, inputs)

    # Check actual spend
    breakdown = await workflow.get_cost_breakdown()
    print(f"Spent: ${breakdown['total_usd']:.4f}")
    print(f"Remaining: ${breakdown['remaining_usd']:.4f}")

except BudgetExceededError as e:
    print(f"Budget exceeded!")
    print(f"  Spent: ${e.spent_usd:.4f}")
    print(f"  Limit: ${e.budget_usd:.2f}")
    print(f"  Overage: ${e.spent_usd - e.budget_usd:.4f}")
```

**Key Benefits:**
- Prevent runaway costs in development and production
- Set different budgets for different workflows
- Real-time enforcement - stops before overspending
- Detailed error information for debugging

**Use Cases:**
- Development/testing with cost limits
- Production workflows with strict budgets
- Cost-aware A/B testing of different prompts
- Budget allocation across multiple workflows

### 📊 LLM Call Tracking

Automatic token counting and cost calculation for 400+ LLM models.

```python
from wflo.sdk.decorators.track_llm import track_llm_call
from openai import AsyncOpenAI

client = AsyncOpenAI()

@track_llm_call(model="gpt-4")
async def chat_with_gpt4(messages):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=messages,
    )
    return response
# Automatically tracks:
# - Prompt tokens
# - Completion tokens
# - Total tokens
# - Cost in USD
```

**Supported Providers:**

| Provider | Models | Token Tracking | Cost Calculation |
|----------|--------|----------------|------------------|
| OpenAI | GPT-4, GPT-3.5-turbo, o1, o3-mini | ✅ | ✅ |
| Anthropic | Claude 3.5 Sonnet, Opus, Haiku | ✅ | ✅ |
| Google | Gemini Pro, Gemini Flash | ✅ | ✅ |
| Meta | Llama 3 70B, Llama 3 8B | ✅ | ✅ |
| Mistral AI | Mistral Large, Medium, Small | ✅ | ✅ |

**And 395+ more models!**

**Features:**
- Automatic usage extraction from API responses
- Provider auto-detection from model name
- Support for both dict and object response formats
- Works with OpenAI, Anthropic, Google, and more

### ⏮️ Checkpointing & Rollback

Save workflow state at any point and rollback if needed.

```python
from wflo.sdk.decorators.checkpoint import checkpoint

@checkpoint(name="planning_complete")
async def plan_approach(topic: str):
    # Plan research...
    return {"topic": topic, "plan": plan}

@checkpoint(name="research_complete")
async def conduct_research(state):
    # Conduct research...
    return {**state, "findings": findings}

@checkpoint(name="synthesis_complete")
async def synthesize(state):
    # Synthesize findings...
    return {**state, "summary": summary}

# If synthesis fails, rollback to previous checkpoint
previous_state = await workflow.rollback_to_checkpoint("research_complete")
# Re-run synthesis with different parameters
new_result = await synthesize(previous_state)
```

**Key Benefits:**
- Save progress in long-running workflows
- Recover from failures without re-running expensive LLM calls
- Experiment with different parameters from same checkpoint
- Debug workflows by examining checkpoint state

**Use Cases:**
- Multi-step workflows with expensive operations
- Iterative refinement (try different synthesis approaches)
- Error recovery in production
- Development and debugging

**Checkpoint Storage:**
- Stored in PostgreSQL with version tracking
- Each checkpoint has unique snapshot ID
- Query checkpoints: `SELECT * FROM state_snapshots WHERE execution_id = ?`

### 🔗 Multi-Framework Support

Works with LangGraph, CrewAI, AutoGen, and direct API calls - no code changes required.

#### LangGraph Integration

```python
from langgraph.graph import StateGraph, END
from wflo.sdk.workflow import WfloWorkflow

# Your LangGraph workflow
def create_graph():
    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", END)
    return graph.compile()

# Wrap with wflo
workflow = WfloWorkflow(name="langgraph-workflow", budget_usd=5.0)
compiled_graph = create_graph()

# Execute with automatic tracking
result = await workflow.execute(
    compiled_graph,
    {"messages": [{"role": "user", "content": "Hello"}]}
)
```

**Features:**
- Automatic detection via `ainvoke` method
- Tracks all LLM calls within the graph
- Budget enforcement across entire execution
- State checkpointing for each node

#### CrewAI Integration

```python
from crewai import Agent, Task, Crew
from wflo.sdk.workflow import WfloWorkflow

# Your CrewAI setup
researcher = Agent(role="Researcher", goal="...", llm="gpt-4")
writer = Agent(role="Writer", goal="...", llm="gpt-4")

task1 = Task(description="Research topic", agent=researcher)
task2 = Task(description="Write article", agent=writer)

crew = Crew(agents=[researcher, writer], tasks=[task1, task2])

# Wrap with wflo
workflow = WfloWorkflow(name="crewai-workflow", budget_usd=10.0)

# Execute with cost tracking
result = await workflow.execute(crew, {})
```

**Features:**
- Automatic detection via `kickoff` method
- Tracks costs across all agent interactions
- Multi-agent workflow support
- Budget enforcement for entire crew

#### AutoGen Integration

```python
from autogen import ConversableAgent
from wflo.sdk.workflow import WfloWorkflow
from wflo.sdk.decorators.checkpoint import checkpoint

@checkpoint(name="conversation_complete")
async def run_conversation(message: str):
    agent1 = ConversableAgent(name="Assistant", llm_config=llm_config)
    agent2 = ConversableAgent(name="User", llm_config=llm_config)

    result = agent1.initiate_chat(agent2, message=message)
    return {"result": result}

workflow = WfloWorkflow(name="autogen-chat", budget_usd=2.0)
result = await workflow.execute(run_conversation, {"message": "Hello"})
```

#### OpenAI Direct

```python
from openai import AsyncOpenAI
from wflo.sdk.decorators.track_llm import track_llm_call

client = AsyncOpenAI()

@track_llm_call(model="gpt-4")
async def my_openai_workflow(prompt: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

workflow = WfloWorkflow(name="openai-workflow", budget_usd=1.0)
result = await workflow.execute(my_openai_workflow, {"prompt": "..."})
```

### 🔍 Execution Tracking

Every workflow gets a unique execution ID for tracking and debugging.

```python
# Execute workflow
result = await workflow.execute(my_workflow, inputs)

# Get execution ID
execution_id = workflow.execution_id  # e.g., "exec-a1b2c3d4e5f6"

# Get trace ID for distributed tracing
trace_id = workflow.get_trace_id()  # Same as execution_id

# Query database for execution details
# SELECT * FROM workflow_executions WHERE id = 'exec-a1b2c3d4e5f6';

# Get cost breakdown
breakdown = await workflow.get_cost_breakdown()
print(f"Total: ${breakdown['total_usd']:.4f}")
print(f"Budget: ${breakdown['budget_usd']:.2f}")
print(f"Remaining: ${breakdown['remaining_usd']:.4f}")
print(f"Exceeded: {breakdown['exceeded']}")

# Query all checkpoints for this execution
# SELECT * FROM state_snapshots WHERE execution_id = 'exec-a1b2c3d4e5f6';
```

**Database Schema:**

```sql
-- Execution record
CREATE TABLE workflow_executions (
    id VARCHAR PRIMARY KEY,                -- exec-xxx
    workflow_definition_id VARCHAR,        -- Workflow name
    status VARCHAR,                        -- RUNNING, COMPLETED, FAILED
    inputs JSONB,                          -- Input parameters
    outputs JSONB,                         -- Result
    cost_total_usd DECIMAL,                -- Total cost
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- State checkpoints
CREATE TABLE state_snapshots (
    id VARCHAR PRIMARY KEY,                -- snap-xxx
    execution_id VARCHAR REFERENCES workflow_executions(id),
    step_id VARCHAR,                       -- Checkpoint name
    variables JSONB,                       -- Saved state
    version INT,                           -- Snapshot version
    created_at TIMESTAMP
);
```

### 📈 Cost Analysis

Detailed cost breakdown and attribution.

```python
# After execution
breakdown = await workflow.get_cost_breakdown()

print(f"Total spent: ${breakdown['total_usd']:.4f}")
print(f"Budget limit: ${breakdown['budget_usd']:.2f}")
print(f"Remaining: ${breakdown['remaining_usd']:.4f}")
print(f"Budget exceeded: {breakdown['exceeded']}")

# Query cost by execution
# SELECT
#     id,
#     workflow_definition_id,
#     cost_total_usd,
#     created_at
# FROM workflow_executions
# WHERE workflow_definition_id = 'my-workflow'
# ORDER BY created_at DESC;

# Aggregate cost by workflow
# SELECT
#     workflow_definition_id,
#     COUNT(*) as executions,
#     SUM(cost_total_usd) as total_cost,
#     AVG(cost_total_usd) as avg_cost
# FROM workflow_executions
# GROUP BY workflow_definition_id;
```

## Configuration Options

```python
workflow = WfloWorkflow(
    name="my-workflow",              # Workflow identifier
    budget_usd=10.0,                 # Maximum spend
    enable_checkpointing=True,       # Enable state snapshots
    enable_observability=True,       # Enable tracing/metrics
)
```

## Best Practices

### 1. Always Set Budgets

```python
# ✅ GOOD
workflow = WfloWorkflow(name="workflow", budget_usd=2.0)

# ❌ BAD - Could spend unlimited money
workflow = WfloWorkflow(name="workflow")  # No budget!
```

### 2. Use Checkpoints for Multi-Step Workflows

```python
# ✅ GOOD - Can recover from failures
@checkpoint(name="step1")
async def step_one():
    return await expensive_operation()

@checkpoint(name="step2")
async def step_two(state):
    return await another_expensive_operation(state)
```

### 3. Track All LLM Calls

```python
# ✅ GOOD - Tracked and counted
@track_llm_call(model="gpt-4")
async def my_function():
    return await client.chat.completions.create(...)

# ❌ BAD - No tracking, unknown cost
async def my_function():
    return await client.chat.completions.create(...)
```

### 4. Handle Budget Exceptions

```python
# ✅ GOOD
try:
    result = await workflow.execute(my_workflow, inputs)
except BudgetExceededError as e:
    logger.warning(f"Budget exceeded: {e}")
    result = get_cached_result()

# ❌ BAD - Unhandled exception
result = await workflow.execute(my_workflow, inputs)
```

## Phase 2+ Roadmap

Features coming in future phases:

- 🔄 **Retry Manager** - Exponential backoff for transient failures
- 🛡️ **Circuit Breaker** - Prevent cascading failures
- 🚦 **Resource Contention** - Detect and manage resource conflicts
- 🗳️ **Consensus Voting** - Multi-agent decision making
- 🏖️ **Sandboxed Execution** - Isolated code execution
- ✋ **Human Approval Gates** - Manual approval steps
- 📈 **Advanced Observability** - OpenTelemetry, Prometheus
- 🔐 **Supabase Integration** - Authentication and managed database

## Next Steps

- [Getting Started](./getting-started.md) - Build your first workflow
- [Examples](./examples.md) - See comprehensive code examples
- [Architecture](./architecture.md) - Understand the internals
