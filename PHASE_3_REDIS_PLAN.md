# Phase 3: Redis Distributed Locks and Caching

**Duration**: 6-8 hours
**Goal**: Implement Redis-based distributed locking and caching to prevent duplicate workflow executions and reduce LLM API costs.

## Prerequisites

✅ Redis configuration in settings.py (already exists)
✅ redis-py dependency (assumed installed)

## Implementation Tasks

### Task 1: Redis Client Wrapper (2 hours)

**File**: `src/wflo/cache/redis.py`

**Requirements**:
- Async Redis client with connection pooling
- Context manager support for automatic cleanup
- Health check capabilities
- Graceful connection handling
- Type hints and proper error handling

**API Design**:
```python
from wflo.cache import get_redis_client

async with get_redis_client() as redis:
    await redis.set("key", "value", ex=60)
    value = await redis.get("key")
```

### Task 2: Distributed Lock Implementation (3 hours)

**File**: `src/wflo/cache/locks.py`

**Requirements**:
- Redlock algorithm for distributed locking
- Lock acquisition with timeout
- Automatic lock renewal (heartbeat) for long operations
- Lock release with verification (check ownership before release)
- Context manager support

**Use Cases**:
1. **Workflow Deduplication**: Prevent duplicate workflow executions
2. **Critical Sections**: Protect database operations that must be atomic
3. **Background Tasks**: Ensure only one worker processes a job

**API Design**:
```python
from wflo.cache import DistributedLock

async with DistributedLock(
    key=f"workflow:{workflow_id}",
    timeout=300,  # 5 minutes
    auto_renewal=True
) as lock:
    # Execute workflow - lock auto-renewed every 30s
    result = await execute_workflow()
```

### Task 3: LLM Response Caching (2 hours)

**File**: `src/wflo/cache/llm_cache.py`

**Requirements**:
- Cache LLM responses by (model, prompt, temperature, max_tokens) tuple
- Configurable TTL (time-to-live)
- Cache hit/miss metrics
- Automatic serialization/deserialization

**Cost Savings**:
- GPT-4 Turbo: $10/M input tokens → 0 if cached
- Claude 3.5 Sonnet: $3/M input tokens → 0 if cached
- Expected savings: 20-40% for workflows with repeated prompts

**API Design**:
```python
from wflo.cache import LLMCache

cache = LLMCache(ttl=3600)  # 1 hour cache

response = await cache.get_or_compute(
    model="gpt-4-turbo",
    prompt="What is Python?",
    compute_fn=lambda: llm_client.generate(...),
    temperature=0.7,
)
```

### Task 4: Integration with Temporal Workflows (1 hour)

**Files to modify**:
- `src/wflo/temporal/workflows.py`
- `src/wflo/temporal/activities.py`

**Changes**:
1. Add distributed lock acquisition at workflow start
2. Integrate LLM cache in activities that call LLMs
3. Add cache hit/miss metrics

**Example**:
```python
@workflow.defn
class DataProcessingWorkflow:
    async def run(self, workflow_id: str) -> dict:
        # Acquire lock to prevent duplicate execution
        async with DistributedLock(f"workflow:{workflow_id}", timeout=300):
            # Execute workflow steps
            result = await workflow.execute_activity(...)
            return result
```

### Task 5: Testing (1-2 hours)

**File**: `tests/integration/test_redis.py`

**Test Cases**:
1. Redis client connection and operations
2. Lock acquisition and release
3. Lock timeout and auto-renewal
4. Concurrent lock attempts (should block/fail)
5. LLM cache hit/miss scenarios
6. Cache expiration

## Implementation Order

1. ✅ Create implementation plan
2. ⬜ Implement Redis client wrapper
3. ⬜ Implement distributed lock
4. ⬜ Implement LLM cache
5. ⬜ Integrate with Temporal workflows
6. ⬜ Write integration tests
7. ⬜ Update metrics to track cache hits/misses
8. ⬜ Commit and push

## Key Technical Decisions

### Lock Implementation: Redlock vs Simple Lock
- **Simple Lock**: Single Redis instance, faster, good for development
- **Redlock**: Multiple Redis instances, more reliable, better for production
- **Decision**: Start with simple lock, add Redlock as optional enhancement

### Cache Key Strategy
- Use SHA256 hash of (model, prompt, params) to avoid key length issues
- Store metadata separately for debugging

### Auto-Renewal Strategy
- Renew lock every 1/3 of timeout duration
- Background task using asyncio.create_task()
- Cancel renewal task on lock release

## Success Criteria

✅ Distributed locks prevent duplicate workflow execution
✅ LLM cache reduces API costs by 20-40%
✅ Redis connection pool handles concurrent requests
✅ Lock auto-renewal works for long-running operations
✅ Integration tests pass (95%+ coverage)
✅ Metrics track cache hit rate and lock wait times

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Redis unavailable | Graceful degradation: skip locking/caching, log warning |
| Lock held too long | Implement lock timeout and force-release capability |
| Cache poisoning | Validate cached data structure before returning |
| Memory usage | Set max cache size and implement LRU eviction |

## Rollout Strategy

1. **Phase 3a**: Redis client + locks (this phase)
2. **Phase 3b**: LLM cache integration
3. **Phase 3c**: Metrics and monitoring
4. **Phase 3d**: Production testing with gradual rollout

## Next Phase Preview

**Phase 4: Kafka Event Streaming** - After Redis implementation, we'll add event streaming for:
- Workflow state changes
- Cost threshold alerts
- Audit logging
- Real-time monitoring
