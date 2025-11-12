## Resilience Patterns Examples

These examples demonstrate how to use wflo's Phase 2 resilience patterns to build robust, production-ready workflows that gracefully handle failures.

### 📋 Examples Overview

| Example | Pattern | Description |
|---------|---------|-------------|
| **retry_with_llm.py** | Retry Manager | Handle transient failures with exponential backoff |
| **circuit_breaker_protection.py** | Circuit Breaker | Prevent cascading failures with fail-fast behavior |
| **resource_contention_detection.py** | Resource Lock | Coordinate shared resource access and detect contention |

---

### 🚀 Quick Start

#### Prerequisites

```bash
# Install wflo
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env and add:
# - DATABASE_URL (for workflow execution)
# - OPENAI_API_KEY (for LLM examples)
```

#### Run Examples

```bash
# Retry Manager examples
python examples/resilience_patterns/retry_with_llm.py

# Circuit Breaker examples
python examples/resilience_patterns/circuit_breaker_protection.py

# Resource Contention examples
python examples/resilience_patterns/resource_contention_detection.py
```

---

### 🔄 Retry Manager

**Use Cases:**
- Handling API rate limits (429 errors)
- Recovering from network timeouts
- Dealing with temporary service outages

**Key Features:**
- Multiple retry strategies (exponential, linear, fixed)
- Configurable jitter to prevent thundering herd
- Custom retry callbacks for monitoring
- Max delay caps to prevent excessive waiting

**Example:**

```python
from wflo.resilience.retry import retry_with_backoff, RetryStrategy

@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(TimeoutError, ConnectionError),
)
async def call_external_api():
    # Your API call here
    response = await client.get("https://api.example.com/data")
    return response.json()
```

**What It Demonstrates:**
1. ✅ Basic retry with exponential backoff
2. ✅ Decorator pattern for clean code
3. ✅ Integration with WfloWorkflow
4. ✅ Monitoring retry attempts with callbacks

---

### ⚡ Circuit Breaker

**Use Cases:**
- Protecting against cascading failures
- Preventing repeated calls to failing services
- Fast-failing when services are degraded

**Key Features:**
- Three states: CLOSED → OPEN → HALF_OPEN
- Configurable failure threshold
- Automatic recovery attempts
- Per-service circuit isolation

**Example:**

```python
from wflo.resilience.circuit_breaker import circuit_breaker

@circuit_breaker(
    name="external-service",
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=(ConnectionError, TimeoutError),
)
async def call_external_service():
    # Your service call here
    return await external_api.get_data()
```

**What It Demonstrates:**
1. ✅ Basic circuit breaker usage
2. ✅ State transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
3. ✅ Fail-fast behavior when circuit is OPEN
4. ✅ Multiple circuit breakers for different services

---

### 🔒 Resource Contention Detection

**Use Cases:**
- Database connection pooling
- API quota management
- Coordinating concurrent workflow access
- Preventing resource exhaustion

**Key Features:**
- Exclusive or concurrent access control
- Automatic contention detection and logging
- Timeout protection
- Detailed statistics and monitoring

**Example:**

```python
from wflo.resilience.contention import detect_contention

@detect_contention(
    resource_name="database-pool",
    max_concurrent=5,  # Connection pool size
    contention_threshold=1.0,  # Warn if waiting > 1s
    timeout=5.0,
)
async def execute_query(query: str):
    # Your database operation here
    result = await db.execute(query)
    return result
```

**What It Demonstrates:**
1. ✅ Exclusive resource locking (max_concurrent=1)
2. ✅ Concurrent access with limits (connection pools)
3. ✅ Contention detection and warnings
4. ✅ Timeout handling when resources unavailable
5. ✅ Statistics monitoring (contention rate, wait times)

---

### 🏗️ Real-World Scenarios

#### Scenario 1: Resilient LLM Pipeline

Combine all three patterns for maximum resilience:

```python
from wflo.resilience.retry import retry_with_backoff
from wflo.resilience.circuit_breaker import circuit_breaker
from wflo.resilience.contention import detect_contention

# Retry handles transient failures
@retry_with_backoff(max_retries=3, base_delay=1.0)
# Circuit breaker prevents cascading failures
@circuit_breaker(name="openai-api", failure_threshold=5)
# Resource lock manages API quota
@detect_contention(resource_name="openai-quota", max_concurrent=3)
async def call_llm(prompt: str):
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

#### Scenario 2: Database Connection Pool

Manage connection pool efficiently:

```python
from wflo.resilience.contention import get_resource_lock

# Create shared connection pool lock
db_pool = get_resource_lock(
    name="postgres-pool",
    max_concurrent=10,  # Pool size
    contention_threshold=2.0,
)

async def execute_transaction(query: str):
    async with db_pool.acquire(workflow_id="tx-123", timeout=5.0):
        # Connection acquired from pool
        result = await db.execute(query)
        return result
```

#### Scenario 3: Rate-Limited API

Handle API rate limits gracefully:

```python
from wflo.resilience.retry import RetryManager, RetryStrategy
from wflo.resilience.contention import ResourceLock

# Rate limit: 10 requests per second
rate_limiter = ResourceLock(
    name="api-rate-limit",
    max_concurrent=10,
    timeout=1.0,
)

# Retry on rate limit errors
retry_manager = RetryManager(
    max_retries=5,
    base_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL,
)

async def call_rate_limited_api(endpoint: str):
    async with rate_limiter.acquire(workflow_id="api-call"):
        return await retry_manager.execute(
            lambda: api_client.get(endpoint),
            retryable_exceptions=(RateLimitError,),
        )
```

---

### 📊 Monitoring and Observability

All resilience patterns include built-in observability:

#### Retry Manager
```python
# Callback for monitoring
def on_retry(attempt: int, exception: Exception):
    logger.warning(f"Retry attempt {attempt}: {exception}")
    metrics.increment("retry_attempts", tags={"error": type(exception).__name__})

retry_manager.execute(func, on_retry=on_retry)
```

#### Circuit Breaker
```python
# Get circuit state
breaker = get_circuit_breaker("my-service")
state = breaker.get_state()

print(f"State: {state['state']}")
print(f"Failures: {state['failure_count']}/{state['failure_threshold']}")
print(f"Last state change: {state['last_state_change']}")
```

#### Resource Lock
```python
# Get contention statistics
lock = get_resource_lock("my-resource")
stats = lock.get_stats()

print(f"Total acquisitions: {stats['total_acquisitions']}")
print(f"Contention events: {stats['contention_count']}")
print(f"Contention rate: {stats['contention_rate']:.1%}")
print(f"Avg wait time: {stats['avg_wait_time_seconds']:.3f}s")
```

---

### 🧪 Testing

Integration tests verify resilience patterns work with real workflows:

```bash
# Run integration tests
poetry run pytest tests/integration/test_resilience_patterns.py -v -m integration
```

**Test Coverage:**
- ✅ Retry with transient failures
- ✅ Circuit breaker state transitions
- ✅ Resource contention between concurrent workflows
- ✅ Combined patterns working together
- ✅ Timeout and error handling
- ✅ Statistics and monitoring

---

### 📖 Additional Resources

- **[Phase 2 Documentation](../../docs/PHASE_2_RESILIENCE_PATTERNS.md)** - Complete technical documentation
- **[Integration Tests](../../tests/integration/test_resilience_patterns.py)** - Real-world test scenarios
- **[Unit Tests](../../tests/unit/)** - Individual pattern testing

---

### 🎯 Best Practices

1. **Combine Patterns** - Use retry + circuit breaker for maximum resilience
2. **Monitor Statistics** - Track contention rates and failure patterns
3. **Tune Thresholds** - Adjust based on your application's characteristics
4. **Use Shared Circuit Breakers** - One circuit per service, not per request
5. **Set Reasonable Timeouts** - Balance responsiveness vs. retry opportunities

---

### ❓ FAQ

**Q: Should I use retry or circuit breaker?**
A: Use both! Retry handles transient failures. Circuit breaker prevents cascading failures. They complement each other.

**Q: What's a good contention threshold?**
A: Start with 5 seconds. Lower it if you need faster detection. Raise it for less noise.

**Q: How do I prevent retry storms?**
A: Enable jitter (`jitter=True`) to randomize retry timing and prevent synchronized retries.

**Q: Can I use these patterns outside of workflows?**
A: Yes! All patterns work standalone and can be used in any async Python code.

---

### 💬 Support

- **Issues:** [GitHub Issues](https://github.com/wflo-ai/wflo/issues)
- **Documentation:** [Full docs](../../docs/)
- **Examples:** This directory!
