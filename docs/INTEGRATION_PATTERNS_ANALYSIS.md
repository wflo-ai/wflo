# Integration Patterns Analysis: Real-World Requirements for Wflo

This document analyzes integration patterns from real-world AI agent frameworks to determine what wflo actually needs to implement.

## Executive Summary

After creating examples for **LangGraph, CrewAI, OpenAI Direct, and Anthropic Claude**, we identified **8 core integration patterns** that wflo must support.

## 📊 Integration Pattern Matrix

### Pattern 1: LLM Call Wrapping

**Found in**: All frameworks (LangGraph, CrewAI, OpenAI, Anthropic)

**What it needs**:
```python
@track_llm_call(model="gpt-4")
async def call_llm(messages):
    response = await client.chat.completions.create(...)
    # Wflo automatically tracks:
    # - Input/output tokens
    # - Cost in USD
    # - Latency
    # - Model used
    return response
```

**Required wflo features**:
- [x] ✅ Cost tracking (EXISTS in `src/wflo/cost/`)
- [ ] ❌ Decorator for wrapping LLM calls
- [ ] ❌ Token counting integration
- [ ] ❌ Per-call metrics collection

---

### Pattern 2: Budget Enforcement

**Found in**: All frameworks

**What users need**:
```python
# Total budget for workflow
wflo = WfloWorkflow(budget_usd=10.00)

# Per-agent budgets (CrewAI pattern)
wflo = WfloWorkflow(
    budget_usd=10.00,
    per_agent_budgets={
        "researcher": 2.00,
        "writer": 3.00,
        "editor": 1.50
    }
)
```

**Required wflo features**:
- [x] ✅ Budget tracking (EXISTS)
- [ ] ❌ Budget enforcement decorator
- [ ] ❌ Per-agent budget tracking
- [ ] ❌ Real-time budget checking
- [ ] ❌ Budget exceeded exceptions

---

### Pattern 3: Automatic Checkpointing

**Found in**: LangGraph (after each node), CrewAI (after each agent), OpenAI (after each tool call)

**What users need**:
```python
# LangGraph: Checkpoint after each node
@checkpoint
async def plan_research(state):
    # ... do work ...
    return state  # Auto-saved

# CrewAI: Checkpoint after each agent
checkpoint_after_agent(task, agent_name="researcher")

# OpenAI: Checkpoint after each tool call
await wflo.checkpoint(f"iteration_{i}_tool_{name}", state)
```

**Required wflo features**:
- [x] ✅ State snapshots (DB schema EXISTS)
- [ ] ❌ Checkpoint decorator
- [ ] ❌ Auto-checkpoint after framework events
- [ ] ❌ Checkpoint listing/browsing
- [ ] ❌ Rollback to checkpoint API

---

### Pattern 4: Circuit Breakers

**Found in**: All frameworks (protect against API failures, infinite loops)

**What users need**:
```python
# Per-component circuit breakers
@circuit_breaker(
    name="research-planner",
    token_budget=10000,
    error_threshold=0.5
)
async def plan_research():
    # Automatically opens circuit if:
    # - Error rate > 50%
    # - Token budget exceeded
    # - Too many failures
```

**Required wflo features**:
- [ ] ❌ Circuit breaker service
- [ ] ❌ Per-component circuit tracking
- [ ] ❌ Token budget circuit breakers
- [ ] ❌ Error rate circuit breakers
- [ ] ❌ Circuit state management (Redis)
- [ ] ❌ Auto-recovery after cooldown

---

### Pattern 5: Automatic Retry with Backoff

**Found in**: All frameworks (handle transient API failures)

**What users need**:
```python
@with_retry(
    max_attempts=3,
    backoff="exponential",
    initial_delay_ms=100,
    max_delay_ms=30000,
    jitter=True
)
async def call_api():
    # Automatically retries on failure
    # with exponential backoff + jitter
```

**Required wflo features**:
- [ ] ❌ Retry manager service
- [ ] ❌ Retry decorator
- [ ] ❌ Exponential backoff calculation
- [ ] ❌ Jitter support
- [ ] ❌ Retry attempt tracking
- [ ] ❌ Dead letter queue for failed retries

---

### Pattern 6: Infinite Loop Detection

**Found in**: OpenAI Direct (agents can get stuck calling same tool repeatedly)

**What users need**:
```python
@detect_infinite_loop(
    max_iterations=10,
    similarity_threshold=0.9
)
async def run_agent_loop():
    # Detects if agent repeats same actions
    # Raises InfiniteLoopDetectedError
```

**Required wflo features**:
- [ ] ❌ Loop detection service
- [ ] ❌ Action similarity comparison
- [ ] ❌ Pattern detection algorithm
- [ ] ❌ Loop detection decorator
- [ ] ❌ Configurable thresholds

---

### Pattern 7: Multi-Agent Coordination

**Found in**: CrewAI, LangGraph (multi-agent systems)

**What users need**:
```python
# Track costs per agent
@track_agent_cost(agent_name="researcher", budget_usd=2.00)

# Consensus voting for decisions
consensus = await wflo.consensus_vote(
    agents=["agent1", "agent2", "agent3"],
    strategy="majority",
    quorum=0.6
)

# Get cost breakdown by agent
breakdown = wflo.get_cost_breakdown_by_agent()
# {
#   "researcher": {"cost_usd": 1.23, "budget_usd": 2.00, ...},
#   "writer": {"cost_usd": 2.45, "budget_usd": 3.00, ...}
# }
```

**Required wflo features**:
- [ ] ❌ Per-agent cost tracking
- [ ] ❌ Consensus voting service
- [ ] ❌ Agent state synchronization
- [ ] ❌ Multi-agent observability
- [ ] ❌ Agent-to-agent communication tracking

---

### Pattern 8: Tool/Function Call Tracking

**Found in**: OpenAI, Anthropic (function/tool calling)

**What users need**:
```python
@track_tool_call(tool_name="search_web")
def search_web(query: str):
    # Tracks:
    # - Tool invocation count
    # - Tool execution time
    # - Tool success/failure rate
    return results
```

**Required wflo features**:
- [ ] ❌ Tool call tracking
- [ ] ❌ Tool metrics (count, latency, success rate)
- [ ] ❌ Tool cost attribution (if tool calls LLMs)
- [ ] ❌ Tool call history

---

## 🎯 Priority Matrix: What to Build First

Based on frequency across frameworks and user pain points:

### Priority 0 (Critical - Build First)

These patterns appear in ALL frameworks and solve major pain points:

| Feature | Frameworks | Pain Point | Effort |
|---------|-----------|------------|--------|
| **LLM Call Wrapping** | All 4 | No cost visibility | Medium |
| **Budget Enforcement** | All 4 | Runaway costs | Medium |
| **Circuit Breakers** | All 4 | API failure cascades | High |
| **Automatic Retry** | All 4 | Manual retry code | Medium |
| **Checkpointing** | All 4 | Lost progress on errors | High |

### Priority 1 (Important - Build Second)

These solve specific but common use cases:

| Feature | Frameworks | Pain Point | Effort |
|---------|-----------|------------|--------|
| **Infinite Loop Detection** | OpenAI, Claude | Agents get stuck | Medium |
| **Tool Call Tracking** | OpenAI, Claude | No tool observability | Low |
| **Multi-Agent Cost Tracking** | CrewAI, LangGraph | Can't attribute costs | Medium |

### Priority 2 (Nice to Have - Build Third)

These are valuable but less critical:

| Feature | Frameworks | Pain Point | Effort |
|---------|-----------|------------|--------|
| **Consensus Voting** | CrewAI, LangGraph | Multi-agent decisions | High |
| **Agent Synchronization** | CrewAI | Race conditions | High |

---

## 📦 Phased Implementation Plan

### Phase 1: Core Wrapping (2 weeks)

**Goal**: Make wflo usable with any framework for basic cost tracking and budgets

**Deliverables**:
1. `@track_llm_call` decorator
2. `WfloWorkflow` context manager
3. Budget enforcement
4. Basic checkpointing decorator

**Success metric**: Run LangGraph example with cost tracking

---

### Phase 2: Reliability (2 weeks)

**Goal**: Add retry and circuit breakers for production resilience

**Deliverables**:
1. `@with_retry` decorator
2. Circuit breaker service
3. `@circuit_breaker` decorator
4. Error tracking

**Success metric**: OpenAI function calling handles transient failures

---

### Phase 3: Advanced Features (3 weeks)

**Goal**: Multi-agent support and loop detection

**Deliverables**:
1. Per-agent cost tracking
2. Infinite loop detection
3. Tool call tracking
4. Multi-agent coordination

**Success metric**: CrewAI example tracks cost per agent

---

### Phase 4: Production Hardening (2 weeks)

**Goal**: Make production-ready with API and SDK

**Deliverables**:
1. REST API for execution tracking
2. Python SDK
3. Integration tests with all frameworks
4. Documentation

**Success metric**: All 4 framework examples work end-to-end

---

## 🧪 Integration Test Requirements

For each framework, we need integration tests that verify:

### LangGraph Tests

```python
def test_langgraph_with_wflo():
    """Test LangGraph workflow with wflo tracking."""
    # 1. Create LangGraph workflow
    # 2. Wrap with wflo
    # 3. Execute workflow
    # 4. Verify:
    #    - Cost tracked per node
    #    - Budget enforced
    #    - Checkpoints saved
    #    - Can rollback
```

### CrewAI Tests

```python
def test_crewai_with_wflo():
    """Test CrewAI crew with per-agent budgets."""
    # 1. Create CrewAI crew (3 agents)
    # 2. Set per-agent budgets
    # 3. Execute crew
    # 4. Verify:
    #    - Cost tracked per agent
    #    - Per-agent budgets enforced
    #    - Checkpoints after each agent
    #    - Cost breakdown available
```

### OpenAI Tests

```python
def test_openai_function_calling_with_wflo():
    """Test OpenAI function calling with loop detection."""
    # 1. Create agent with tools
    # 2. Wrap with wflo
    # 3. Execute agent loop
    # 4. Verify:
    #    - Cost tracked per iteration
    #    - Tool calls tracked
    #    - Infinite loop detected
    #    - Auto-retry on failures
```

### Anthropic Tests

```python
def test_anthropic_claude_with_wflo():
    """Test Claude tool use with cost tracking."""
    # 1. Create Claude agent
    # 2. Wrap with wflo
    # 3. Execute tool use workflow
    # 4. Verify:
    #    - Cost tracked (Claude pricing)
    #    - Budget enforced
    #    - Tool calls tracked
```

---

## 🔑 Key Insights from Examples

### 1. Decorator Pattern is King

Users want simple decorators, not complex API calls:

```python
# Good (what users want)
@track_llm_call(model="gpt-4")
@with_retry(max_attempts=3)
@checkpoint
async def my_function():
    ...

# Bad (too complex)
async with wflo.track_cost():
    async with wflo.retry():
        async with wflo.checkpoint():
            ...
```

### 2. Framework-Agnostic Wrapping

Wflo should NOT require modifying framework code. It should wrap existing workflows:

```python
# Good (wrap existing code)
workflow = create_langgraph_workflow()  # Unchanged
wflo_workflow = wflo.wrap(workflow)  # Wrap it
result = await wflo_workflow.execute()

# Bad (require framework changes)
workflow = create_wflo_langgraph_workflow()  # Specialized
```

### 3. Observability is Non-Negotiable

Every example showed users need to know:
- How much did this cost?
- Which agent/step used most tokens?
- Where can I see the trace?
- What checkpoints exist?

### 4. Rollback is Critical

Users need confidence they can undo mistakes:
- LangGraph: Rollback to previous node
- CrewAI: Rollback to previous agent
- OpenAI: Rollback to before tool call
- All: Rollback on budget exceeded

---

## 📝 Next Steps

1. ✅ Create examples for each framework
2. ✅ Analyze integration patterns
3. ⏭️ **Build Phase 1** (Core Wrapping)
4. ⏭️ Write integration tests
5. ⏭️ Build Phase 2 (Reliability)
6. ⏭️ Write more integration tests
7. ⏭️ Build Phase 3 (Advanced Features)
8. ⏭️ Final integration testing with all frameworks

---

**Last Updated**: 2025-01-11
**Status**: Ready for Phase 1 Implementation
