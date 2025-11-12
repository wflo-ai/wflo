# Wflo Implementation Plan v2.0
## Based on Real-World Integration Patterns

This plan is driven by **actual integration examples** with LangGraph, CrewAI, OpenAI, and Anthropic Claude.

---

## 🎯 Vision

Enable developers to add production-grade orchestration to ANY AI agent framework with minimal code changes.

**One-line integration**:
```python
from wflo.sdk import WfloWorkflow

# Wrap any framework
wflo = WfloWorkflow(budget_usd=10.00)
result = await wflo.execute(my_langgraph_workflow, inputs)
```

---

## 📊 What We're Building

Based on integration pattern analysis, here's what wflo needs:

| Component | Priority | Effort | Value |
|-----------|----------|--------|-------|
| LLM Call Tracking Decorator | P0 | 1 week | HIGH |
| Budget Enforcement | P0 | 1 week | HIGH |
| Checkpoint Decorator | P0 | 1 week | HIGH |
| Circuit Breaker Service | P0 | 1.5 weeks | HIGH |
| Retry Manager | P0 | 1 week | HIGH |
| REST API | P0 | 1 week | MEDIUM |
| Python SDK | P0 | 1 week | MEDIUM |
| Loop Detection | P1 | 1 week | MEDIUM |
| Multi-Agent Tracking | P1 | 1.5 weeks | MEDIUM |
| Tool Call Tracking | P1 | 0.5 weeks | LOW |

**Total**: ~10 weeks for full implementation

---

## 🚀 Phase 1: Core Wrapping (Weeks 1-2)

### Goal
Make wflo usable with LangGraph and OpenAI for basic cost tracking and budgets.

### Features to Build

#### 1.1 LLM Call Tracking Decorator

**File**: `src/wflo/sdk/decorators/track_llm.py`

```python
from functools import wraps
from wflo.cost import CostTracker
from wflo.observability import get_logger, track_metric

def track_llm_call(model: str):
    """
    Decorator to track LLM API calls.

    Automatically tracks:
    - Input/output tokens
    - Cost in USD
    - Latency
    - Model used

    Usage:
        @track_llm_call(model="gpt-4")
        async def call_openai(messages):
            return await client.chat.completions.create(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger()
            cost_tracker = get_cost_tracker()

            # Start tracking
            start_time = time.time()

            try:
                # Execute LLM call
                response = await func(*args, **kwargs)

                # Extract token usage
                usage = response.usage if hasattr(response, 'usage') else None

                if usage:
                    # Track cost
                    cost_usd = await cost_tracker.track_llm_call(
                        provider=model.split("-")[0],  # "gpt-4" -> "gpt"
                        model=model,
                        tokens_in=usage.prompt_tokens,
                        tokens_out=usage.completion_tokens
                    )

                    # Track metrics
                    latency_ms = (time.time() - start_time) * 1000
                    track_metric("llm_call_duration_ms", latency_ms)
                    track_metric("llm_call_tokens_total", usage.total_tokens)
                    track_metric("llm_call_cost_usd", cost_usd)

                    # Log
                    logger.info(
                        "llm_call_completed",
                        model=model,
                        tokens=usage.total_tokens,
                        cost_usd=cost_usd,
                        latency_ms=latency_ms
                    )

                return response

            except Exception as e:
                track_metric("llm_call_errors_total", 1)
                raise

        return wrapper
    return decorator
```

**Integration Tests**:
- [ ] Test with OpenAI API
- [ ] Test with Anthropic Claude
- [ ] Test cost calculation accuracy
- [ ] Test error handling

---

#### 1.2 Budget Enforcement

**File**: `src/wflo/sdk/workflow.py`

```python
class WfloWorkflow:
    """Main wflo workflow wrapper."""

    def __init__(
        self,
        name: str,
        budget_usd: float,
        per_agent_budgets: Optional[Dict[str, float]] = None,
        enable_checkpointing: bool = True,
        enable_observability: bool = True
    ):
        self.name = name
        self.budget_usd = budget_usd
        self.per_agent_budgets = per_agent_budgets or {}
        self.execution_id = None
        self.cost_tracker = CostTracker()

    async def execute(self, workflow, inputs: dict):
        """Execute workflow with wflo orchestration."""
        # Allocate execution ID
        self.execution_id = await coordinator.allocate_execution_id(
            workflow_id=self.name,
            inputs=inputs
        )

        try:
            # Execute with budget checking
            result = await self._execute_with_budget_check(workflow, inputs)
            return result

        except BudgetExceededError as e:
            # Rollback and notify
            await self.rollback_to_last_checkpoint()
            raise

    async def _execute_with_budget_check(self, workflow, inputs):
        """Execute with real-time budget checking."""
        # Check budget before each step
        # This hooks into framework-specific events

        if hasattr(workflow, '__ainvoke__'):  # LangGraph
            return await self._execute_langgraph(workflow, inputs)
        elif hasattr(workflow, 'kickoff'):  # CrewAI
            return await self._execute_crewai(workflow)
        else:
            # Generic execution
            return await workflow(inputs)

    async def check_budget(self):
        """Check if budget exceeded."""
        total_cost = await self.cost_tracker.get_total_cost(self.execution_id)

        if total_cost > self.budget_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${total_cost:.4f} > ${self.budget_usd:.2f}"
            )
```

**Integration Tests**:
- [ ] Test budget enforcement with LangGraph
- [ ] Test budget enforcement with OpenAI function calling
- [ ] Test per-agent budgets with CrewAI
- [ ] Test budget exceeded exception handling

---

#### 1.3 Checkpoint Decorator

**File**: `src/wflo/sdk/decorators/checkpoint.py`

```python
def checkpoint(func):
    """
    Decorator to automatically checkpoint after function execution.

    Usage:
        @checkpoint
        async def process_step(state):
            # do work
            return new_state
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Execute function
        result = await func(*args, **kwargs)

        # Save checkpoint
        checkpoint_service = get_checkpoint_service()
        execution_id = get_current_execution_id()

        await checkpoint_service.save(
            execution_id=execution_id,
            checkpoint_name=func.__name__,
            state=result if isinstance(result, dict) else {"result": result}
        )

        logger.info(
            "checkpoint_saved",
            execution_id=execution_id,
            checkpoint=func.__name__
        )

        return result

    return wrapper
```

**Integration Tests**:
- [ ] Test checkpoint after LangGraph node
- [ ] Test checkpoint after CrewAI agent
- [ ] Test checkpoint after OpenAI tool call
- [ ] Test rollback to checkpoint

---

### Phase 1 Deliverables

**Code**:
- `src/wflo/sdk/decorators/track_llm.py` (150 lines)
- `src/wflo/sdk/decorators/checkpoint.py` (100 lines)
- `src/wflo/sdk/workflow.py` (300 lines)
- `src/wflo/sdk/__init__.py` (exports)

**Tests**:
- `tests/integration/test_langgraph_integration.py` (200 lines)
- `tests/integration/test_openai_integration.py` (200 lines)
- `tests/unit/test_track_llm_decorator.py` (150 lines)
- `tests/unit/test_checkpoint_decorator.py` (150 lines)

**Examples Working**:
- ✅ `examples/langgraph_integration/wflo_wrapped_graph.py`
- ✅ `examples/openai_direct/wflo_wrapped_function_calling.py`

**Success Criteria**:
- [ ] Can track cost of LangGraph workflow
- [ ] Can enforce budget on OpenAI function calling
- [ ] Can checkpoint and rollback
- [ ] All integration tests passing

---

## 🔄 Phase 2: Reliability (Weeks 3-4)

### Goal
Add retry and circuit breakers for production resilience.

### Features to Build

#### 2.1 Retry Manager Service

**File**: `src/wflo/services/retry/manager.py`

```python
class RetryManager:
    """Automatic retry with exponential backoff."""

    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig
    ) -> Any:
        """Execute function with automatic retry."""
        attempt = 0

        while attempt < config.max_attempts:
            try:
                result = await func()
                await self._track_success(execution_id, attempt)
                return result

            except config.retry_on as e:
                attempt += 1

                if attempt >= config.max_attempts:
                    await self._send_to_dlq(execution_id, e)
                    raise

                delay_ms = self._calculate_backoff(...)
                await asyncio.sleep(delay_ms / 1000.0)
```

**Integration Tests**:
- [ ] Test retry on transient OpenAI API error
- [ ] Test exponential backoff calculation
- [ ] Test dead letter queue for permanent failures

---

#### 2.2 Circuit Breaker Service

**File**: `src/wflo/services/circuit_breaker/service.py`

(See detailed implementation from earlier)

**Integration Tests**:
- [ ] Test circuit opens on error threshold
- [ ] Test circuit opens on token budget
- [ ] Test circuit recovery (half-open -> closed)
- [ ] Test per-component circuit isolation

---

### Phase 2 Deliverables

**Code**:
- `src/wflo/services/retry/` (500 lines)
- `src/wflo/services/circuit_breaker/` (600 lines)
- `src/wflo/sdk/decorators/retry.py` (100 lines)
- `src/wflo/sdk/decorators/circuit_breaker.py` (100 lines)

**Tests**:
- `tests/integration/test_retry_manager.py` (200 lines)
- `tests/integration/test_circuit_breaker.py` (250 lines)

**Examples Working**:
- ✅ OpenAI example handles transient API failures
- ✅ LangGraph example has circuit breakers per node

**Success Criteria**:
- [ ] Auto-retry works on API failures
- [ ] Circuit breaker prevents cascading failures
- [ ] Can recover from circuit open state
- [ ] Integration tests passing

---

## 🎨 Phase 3: Advanced Features (Weeks 5-7)

### Goal
Multi-agent support, loop detection, and tool tracking.

### Features to Build

#### 3.1 Multi-Agent Cost Tracking

**File**: `src/wflo/sdk/multi_agent.py`

```python
@track_agent_cost(agent_name="researcher", budget_usd=2.00)
class ResearchAgent:
    async def execute(self):
        # Cost automatically tracked per agent
        ...

# Get cost breakdown
breakdown = wflo.get_cost_breakdown_by_agent()
# {
#   "researcher": {"cost_usd": 1.23, "remaining": 0.77},
#   "writer": {"cost_usd": 2.45, "remaining": 0.55}
# }
```

**Integration Tests**:
- [ ] Test per-agent cost tracking with CrewAI
- [ ] Test per-agent budget enforcement
- [ ] Test cost breakdown reporting

---

#### 3.2 Infinite Loop Detection

**File**: `src/wflo/services/loop_detection.py`

```python
@detect_infinite_loop(max_iterations=10, similarity_threshold=0.9)
async def run_agent_loop():
    # Automatically detects repeating patterns
    # Raises InfiniteLoopDetectedError
    ...
```

**Integration Tests**:
- [ ] Test loop detection in OpenAI function calling
- [ ] Test similarity threshold tuning
- [ ] Test false positive rate

---

#### 3.3 Tool Call Tracking

**File**: `src/wflo/sdk/decorators/track_tool.py`

```python
@track_tool_call(tool_name="search_web")
def search_web(query: str):
    # Tracks invocation count, latency, success rate
    ...
```

**Integration Tests**:
- [ ] Test tool call metrics collection
- [ ] Test tool call history
- [ ] Test tool success rate tracking

---

### Phase 3 Deliverables

**Code**:
- `src/wflo/sdk/multi_agent.py` (400 lines)
- `src/wflo/services/loop_detection.py` (300 lines)
- `src/wflo/sdk/decorators/track_tool.py` (150 lines)

**Tests**:
- `tests/integration/test_crewai_integration.py` (250 lines)
- `tests/integration/test_loop_detection.py` (150 lines)

**Examples Working**:
- ✅ `examples/crewai_integration/wflo_wrapped_crew.py`
- ✅ OpenAI example detects infinite loops

**Success Criteria**:
- [ ] CrewAI tracks cost per agent
- [ ] OpenAI detects infinite loops
- [ ] Tool calls tracked with metrics

---

## 🌐 Phase 4: API & SDK (Weeks 8-10)

### Goal
Production-ready API and SDK for external integrations.

### Features to Build

#### 4.1 REST API

**File**: `src/wflo/api/main.py`

(See detailed implementation from earlier)

**Endpoints**:
- `POST /api/v1/executions` - Start execution
- `GET /api/v1/executions/{id}` - Get status
- `GET /api/v1/circuits/{name}/status` - Circuit status
- `POST /api/v1/circuits/{name}/reset` - Reset circuit

**Integration Tests**:
- [ ] Test execution creation via API
- [ ] Test status polling
- [ ] Test circuit management

---

#### 4.2 Python SDK

**File**: `src/wflo/sdk/client.py`

(See detailed implementation from earlier)

**Integration Tests**:
- [ ] Test SDK connects to API
- [ ] Test workflow execution via SDK
- [ ] Test status polling via SDK

---

### Phase 4 Deliverables

**Code**:
- `src/wflo/api/` (800 lines)
- `src/wflo/sdk/client.py` (400 lines)

**Tests**:
- `tests/integration/test_api.py` (300 lines)
- `tests/integration/test_sdk.py` (200 lines)

**Documentation**:
- API reference (OpenAPI spec)
- SDK guide with examples
- Integration guides for each framework

**Success Criteria**:
- [ ] All 4 framework examples work end-to-end
- [ ] API documented and tested
- [ ] SDK can execute workflows remotely

---

## 🧪 Integration Test Matrix

| Framework | Test File | What It Tests |
|-----------|-----------|---------------|
| LangGraph | `test_langgraph_integration.py` | Cost tracking per node, checkpointing, budget enforcement |
| CrewAI | `test_crewai_integration.py` | Per-agent budgets, multi-agent coordination |
| OpenAI | `test_openai_integration.py` | Function calling, loop detection, retry |
| Anthropic | `test_anthropic_integration.py` | Tool use, cost tracking for Claude |

**All tests must**:
- Run against real API (not mocked)
- Verify cost calculations
- Test budget enforcement
- Test checkpointing and rollback
- Measure latency overhead (< 50ms)

---

## 📈 Success Metrics

### Phase 1
- ✅ LangGraph example tracks cost within 5% accuracy
- ✅ OpenAI example enforces budget
- ✅ Integration tests pass

### Phase 2
- ✅ Auto-retry reduces transient failures by 90%
- ✅ Circuit breakers prevent cascading failures
- ✅ All integration tests pass

### Phase 3
- ✅ CrewAI tracks cost per agent
- ✅ Loop detection catches infinite loops
- ✅ Tool calls tracked with < 10ms overhead

### Phase 4
- ✅ All 4 framework examples work end-to-end
- ✅ API handles 100 req/s
- ✅ SDK can execute workflows remotely
- ✅ Documentation complete

---

## 🎯 Next Steps

1. ✅ Research frameworks
2. ✅ Create integration examples
3. ✅ Analyze integration patterns
4. ⏭️ **Start Phase 1 implementation**
5. ⏭️ Write integration tests
6. ⏭️ Iterate based on test results

---

**Last Updated**: 2025-01-11
**Status**: Ready to implement Phase 1
