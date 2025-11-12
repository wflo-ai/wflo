# Wflo Implementation Roadmap

**Complete Phased Approach for Production-Ready AI Agent Orchestration**

Version: 1.0
Last Updated: 2025-01-12
Status: Phases 1-2 Complete, Phases 3-7 Pending

---

## 📊 Executive Summary

This document provides a comprehensive roadmap for implementing Wflo, a production-grade orchestration platform for AI agents. It covers all features from basic workflow execution to advanced human-in-the-loop approval gates, distributed coordination, and deployment controls.

**Current State:**
- ✅ **Phases 1-2 Complete** (203 tests passing, 100% success rate)
- ⏳ **Phases 3-7 Pending** (5 phases, estimated 8-12 weeks)

**Architecture Vision:**
```
┌─────────────────────────────────────────────────────────────┐
│                    WFLO SERVICE CATALOG                     │
├─────────────────────────────────────────────────────────────┤
│ 1. EXECUTION ORCHESTRATION ✅ Phase 3                       │
│    • Task allocation with unique IDs                        │
│    • Ownership tracking across distributed workers          │
│    • Heartbeat monitoring and dead worker detection         │
│    • Workflow checkpointing and state persistence           │
│                                                             │
│ 2. RELIABILITY & RESILIENCE ✅ Phase 2 (DONE)              │
│    • Automatic retry with exponential backoff               │
│    • Circuit breakers for cascading failure prevention      │
│    • Resource contention detection                          │
│    • Timeout management                                     │
│                                                             │
│ 3. RESOURCE GOVERNANCE ✅ Phase 4                          │
│    • Token budget enforcement (DONE - Phase 2)             │
│    • Time budget enforcement                                │
│    • Rate limiting with token bucket algorithm              │
│    • Throttling and backpressure                            │
│                                                             │
│ 4. HUMAN-IN-THE-LOOP (HITL) ⭐ Phase 5 - CRITICAL          │
│    • Approval gates for sensitive operations                │
│    • Web UI for approval decisions                          │
│    • Slack/Teams/Email notifications                        │
│    • Audit trail and compliance logging                     │
│                                                             │
│ 5. MULTI-AGENT COORDINATION ✅ Phase 6                      │
│    • Consensus voting mechanisms                            │
│    • State synchronization across agents                    │
│    • Deadlock detection and resolution                      │
│    • Conflict resolution strategies                         │
│                                                             │
│ 6. OBSERVABILITY ✅ Phase 6                                │
│    • Distributed tracing with OpenTelemetry                 │
│    • Cost tracking (DONE - Phase 1)                        │
│    • Performance metrics aggregation                        │
│    • Error tracking and alerting                            │
│                                                             │
│ 7. DEPLOYMENT CONTROLS ✅ Phase 7                          │
│    • Workflow versioning                                    │
│    • Canary deployment support                              │
│    • Rollback capabilities                                  │
│    • A/B testing infrastructure                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Completed Phases (Phases 1-2)

### **Phase 1: Core SDK Foundation** ✅ COMPLETE

**Duration:** 2 weeks
**Status:** 100% Complete
**Tests:** 133 passing

#### Delivered Features:
1. **WfloWorkflow API**
   - Workflow execution with unique execution IDs
   - Budget enforcement (token budget only)
   - Integration with LangGraph, CrewAI, AutoGen, LlamaIndex

2. **Cost Tracking**
   - `@track_llm` decorator for LLM call tracking
   - Token usage monitoring
   - Cost calculation per execution
   - Database persistence

3. **Checkpointing**
   - `@checkpoint` decorator for state persistence
   - Rollback to previous checkpoints
   - State versioning

4. **Database Infrastructure**
   - PostgreSQL schema (workflow_definitions, workflow_executions, llm_calls, checkpoints)
   - SQLAlchemy 2.0 async ORM
   - Supabase integration support

#### Files Created:
```
src/wflo/
├── sdk/
│   ├── workflow.py (WfloWorkflow API)
│   ├── context.py (Execution context)
│   ├── decorators/
│   │   ├── track_llm.py (@track_llm decorator)
│   │   └── checkpoint.py (@checkpoint decorator)
├── db/
│   ├── engine.py (Database engine)
│   └── models/ (SQLAlchemy models)
├── cost/
│   └── tracker.py (Cost tracking service)
└── config/
    └── settings.py (Configuration)

tests/unit/ (133 tests)
examples/ (10+ integration examples)
```

---

### **Phase 2: Resilience Patterns** ✅ COMPLETE

**Duration:** 3 weeks
**Status:** 100% Complete
**Tests:** 60 unit tests + 10 integration tests (all passing)

#### Delivered Features:

1. **RetryManager**
   - Exponential, linear, and fixed backoff strategies
   - Configurable jitter to prevent thundering herd
   - Custom retry callbacks for monitoring
   - `@retry_with_backoff` decorator

2. **CircuitBreaker**
   - State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
   - Configurable failure thresholds
   - Automatic recovery after timeout
   - `@circuit_breaker` decorator

3. **ResourceLock**
   - Exclusive and concurrent access control
   - Contention detection with configurable thresholds
   - Statistics tracking (wait times, contention rate)
   - `@detect_contention` decorator

4. **Budget Caching Optimization**
   - Context variable caching for budget
   - 33% reduction in DB queries per LLM call (3→2 queries)

#### Files Created:
```
src/wflo/resilience/
├── retry.py (RetryManager, 331 lines)
├── circuit_breaker.py (CircuitBreaker, 390 lines)
└── contention.py (ResourceLock, 300 lines)

tests/unit/
├── test_retry_manager.py (16 tests)
├── test_circuit_breaker.py (20 tests)
├── test_resource_contention.py (15 tests)
└── test_budget_caching.py (9 tests)

tests/integration/
└── test_resilience_patterns.py (10 tests)

examples/resilience_patterns/
├── retry_with_llm.py (4 examples)
├── circuit_breaker_protection.py (5 examples)
├── resource_contention_detection.py (7 examples)
└── README.md (comprehensive guide)

docs/
├── PHASE_2_RESILIENCE_PATTERNS.md
└── BUDGET_CACHING_OPTIMIZATION.md
```

#### Usage Examples:
```python
# Retry with exponential backoff
from wflo.resilience.retry import retry_with_backoff, RetryStrategy

@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL,
    jitter=True,
)
async def call_api():
    return await client.get("/data")

# Circuit breaker
from wflo.resilience.circuit_breaker import circuit_breaker

@circuit_breaker(
    name="external-api",
    failure_threshold=5,
    recovery_timeout=60.0,
)
async def call_external_service():
    return await service.get_data()

# Resource contention detection
from wflo.resilience.contention import detect_contention

@detect_contention(
    resource_name="database-pool",
    max_concurrent=10,
    contention_threshold=2.0,
)
async def execute_query(query: str):
    return await db.execute(query)
```

---

## 🚧 Pending Phases (Phases 3-7)

### **Phase 3: Execution Orchestration Service** ⏳ NEXT

**Priority:** HIGH (Foundation for distributed execution)
**Estimated Duration:** 2-3 weeks
**Dependencies:** None (builds on Phase 1-2)
**Estimated Effort:** 40-60 hours

#### Objectives:
Build distributed task coordination across multiple workers/pods in Kubernetes clusters.

#### Features to Implement:

1. **Task Allocation Service**
   - Unique task ID generation
   - Distributed locking for task claims
   - Ownership tracking (which worker owns which task)
   - Task lifecycle management (allocated → running → completed/failed)

2. **Heartbeat Monitoring**
   - Periodic heartbeat updates from workers
   - Stale task detection (dead workers)
   - Automatic task reassignment

3. **Coordinator Service**
   - Central coordination service
   - Worker registration and discovery
   - Task queue management
   - Execution status tracking

#### Database Schema:

**File:** `migrations/003_execution_orchestration.sql`

```sql
-- Task allocation table
CREATE TABLE task_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,  -- pod_id or worker_id
    status VARCHAR(50) NOT NULL,      -- 'allocated', 'running', 'completed', 'failed'
    allocated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    heartbeat_at TIMESTAMP,           -- For liveness detection
    metadata JSONB,
    UNIQUE(execution_id, task_id)
);

CREATE INDEX idx_task_owner ON task_allocations(owner_id, status);
CREATE INDEX idx_task_heartbeat ON task_allocations(heartbeat_at) WHERE status = 'running';

-- Ownership claims (distributed locking)
CREATE TABLE ownership_claims (
    resource_id VARCHAR(255) PRIMARY KEY,
    owner_id VARCHAR(255) NOT NULL,
    claimed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    lease_duration_seconds INT NOT NULL DEFAULT 30
);

CREATE INDEX idx_ownership_expiry ON ownership_claims(expires_at);

-- Execution coordination metadata
ALTER TABLE workflow_executions
ADD COLUMN coordinator_metadata JSONB DEFAULT '{}';
```

#### Implementation Files:

**File Structure:**
```
src/wflo/services/coordinator/
├── __init__.py
├── service.py          # CoordinatorService (main service)
├── models.py           # Data models
└── heartbeat.py        # Heartbeat monitor

src/wflo/sdk/decorators/
└── coordinated.py      # @coordinated_task decorator

tests/unit/
└── test_coordinator_service.py

tests/integration/
└── test_distributed_coordination.py

examples/coordination/
├── distributed_workflow.py
└── README.md
```

**Key Service:** `src/wflo/services/coordinator/service.py`

```python
"""Execution Coordinator Service."""

class CoordinatorService:
    """Distributed execution coordinator.

    Provides:
    - Unique execution ID allocation
    - Task ownership tracking
    - Distributed locking
    - Heartbeat monitoring
    - Dead worker detection
    """

    def __init__(self):
        self.worker_id = os.getenv("HOSTNAME", f"worker-{uuid.uuid4().hex[:8]}")
        self.heartbeat_interval = 10  # seconds

    async def allocate_execution_id(
        self,
        workflow_name: str,
        parent_execution_id: Optional[str] = None,
    ) -> str:
        """Allocate unique execution ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:8]
        return f"exec-{timestamp}-{random_suffix}"

    async def claim_task(
        self,
        execution_id: str,
        task_id: str,
        timeout_seconds: int = 300,
    ) -> bool:
        """Claim ownership of a task."""
        # Try to insert claim (atomic operation)
        # Returns True if claimed, False if already claimed by another worker

    async def mark_task_running(self, execution_id: str, task_id: str):
        """Mark task as running."""

    async def mark_task_completed(self, execution_id: str, task_id: str, result: Dict):
        """Mark task as completed."""

    async def mark_task_failed(self, execution_id: str, task_id: str, error: str):
        """Mark task as failed."""

    async def update_heartbeat(self, execution_id: str, task_id: str):
        """Update task heartbeat."""

    async def detect_dead_workers(self, timeout_seconds: int = 60) -> List[Dict]:
        """Detect tasks with stale heartbeats."""

    async def reassign_stale_tasks(self, timeout_seconds: int = 60):
        """Reassign tasks from dead workers."""
```

**Decorator:** `src/wflo/sdk/decorators/coordinated.py`

```python
"""Decorator for coordinated task execution."""

def coordinated_task(
    task_id: Optional[str] = None,
    retry_on_failure: bool = True,
    max_retries: int = 3,
):
    """Decorator for distributed task coordination.

    Ensures:
    - Unique task allocation across workers
    - Ownership tracking
    - Heartbeat monitoring
    - Automatic retry on failure

    Usage:
        @coordinated_task(task_id="step-1")
        async def process_step(execution_id: str, data: dict):
            # This will only run on one worker
            result = await expensive_operation(data)
            return result
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            coordinator = get_coordinator()
            execution_id = kwargs.get("execution_id")

            # Try to claim task
            claimed = await coordinator.claim_task(execution_id, task_id)
            if not claimed:
                # Wait for task to complete by another worker
                return await wait_for_task_completion(execution_id, task_id)

            # Execute with heartbeat
            await coordinator.mark_task_running(execution_id, task_id)

            try:
                result = await func(*args, **kwargs)
                await coordinator.mark_task_completed(execution_id, task_id, result)
                return result
            except Exception as e:
                await coordinator.mark_task_failed(execution_id, task_id, str(e))
                raise

        return wrapper
    return decorator
```

#### Tests:

**Unit Tests:** `tests/unit/test_coordinator_service.py`
- Test execution ID allocation (unique, timestamped)
- Test task claiming (atomic, no double-allocation)
- Test heartbeat updates
- Test dead worker detection
- Test task reassignment

**Integration Tests:** `tests/integration/test_distributed_coordination.py`
- Test multiple workers claiming same task (only one succeeds)
- Test heartbeat monitoring with simulated worker failure
- Test automatic task reassignment
- Test distributed workflow execution

#### Example Usage:

**File:** `examples/coordination/distributed_workflow.py`

```python
"""Example: Distributed workflow execution."""

from wflo.sdk.workflow import WfloWorkflow
from wflo.sdk.decorators.coordinated import coordinated_task

@coordinated_task(task_id="data-ingestion")
async def ingest_data(execution_id: str, source: str):
    """Ingest data - only runs once across all workers."""
    print(f"Ingesting from {source}...")
    await asyncio.sleep(2)
    return {"records": 1000}

@coordinated_task(task_id="data-processing")
async def process_data(execution_id: str, data: dict):
    """Process data - only runs once across all workers."""
    print(f"Processing {data['records']} records...")
    await asyncio.sleep(3)
    return {"processed": data["records"]}

async def distributed_workflow(source: str):
    workflow = WfloWorkflow(name="distributed-etl", budget_usd=5.0)

    async def workflow_logic(source: str):
        execution_id = workflow.execution_id

        # These steps run on different workers but coordinated
        data = await ingest_data(execution_id=execution_id, source=source)
        result = await process_data(execution_id=execution_id, data=data)
        return result

    return await workflow.execute(workflow_logic, {"source": source})
```

#### Deployment:

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wflo-coordinator
spec:
  replicas: 3  # High availability
  template:
    spec:
      containers:
      - name: coordinator
        image: wflo/coordinator:latest
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: wflo-secrets
              key: database-url
        - name: HEARTBEAT_INTERVAL
          value: "10"
```

#### Testing Checklist:
- [ ] Unit tests for CoordinatorService methods
- [ ] Integration tests with multiple workers
- [ ] Load test with 100+ concurrent tasks
- [ ] Failure scenarios (worker crash, network partition)
- [ ] Heartbeat monitoring and reassignment
- [ ] Performance benchmarks (task claim latency)

---

### **Phase 4: Resource Governance Enhancements** ⏳

**Priority:** MEDIUM
**Estimated Duration:** 1-2 weeks
**Dependencies:** Phase 3 (uses coordinator for distributed rate limiting)
**Estimated Effort:** 20-30 hours

#### Objectives:
Add time budget enforcement, rate limiting, and advanced throttling.

#### Features to Implement:

1. **Time Budget Enforcement**
   - Track execution time per workflow
   - Enforce maximum execution duration
   - Timeout with graceful cleanup
   - Integration with circuit breaker

2. **Rate Limiter Service**
   - Token bucket algorithm implementation
   - Per-resource rate limits (API keys, endpoints)
   - Distributed rate limiting using Redis
   - Burst capacity support

3. **Throttling Service**
   - Automatic backpressure when system overloaded
   - Queue management with priority
   - Load shedding strategies

#### Database Schema:

**File:** `migrations/004_resource_governance.sql`

```sql
-- Time budget tracking
ALTER TABLE workflow_executions
ADD COLUMN time_budget_seconds INT,
ADD COLUMN execution_started_at TIMESTAMP,
ADD COLUMN execution_duration_seconds DECIMAL(10, 3);

-- Rate limit counters (optional, Redis preferred)
CREATE TABLE rate_limits (
    resource_id VARCHAR(255) PRIMARY KEY,
    tokens_remaining DECIMAL(10, 2),
    last_refill_at TIMESTAMP NOT NULL,
    rate_per_second DECIMAL(10, 2) NOT NULL,
    burst_capacity DECIMAL(10, 2) NOT NULL
);
```

#### Implementation Files:

```
src/wflo/governance/
├── __init__.py
├── time_budget.py       # TimeBudgetEnforcer
├── rate_limiter.py      # RateLimiter (token bucket)
└── throttle.py          # ThrottlingService

tests/unit/
├── test_time_budget.py
├── test_rate_limiter.py
└── test_throttle.py

examples/governance/
├── time_budget_example.py
├── rate_limiting_example.py
└── README.md
```

**Time Budget Enforcer:** `src/wflo/governance/time_budget.py`

```python
"""Time budget enforcement."""

class TimeBudgetEnforcer:
    """Enforces time budgets for workflow execution.

    Usage:
        enforcer = TimeBudgetEnforcer(budget_seconds=30)

        async with enforcer.track(execution_id="exec-123"):
            # This will timeout after 30 seconds
            result = await long_running_task()
    """

    def __init__(self, budget_seconds: float):
        self.budget_seconds = budget_seconds

    @asynccontextmanager
    async def track(self, execution_id: str):
        """Track execution time and enforce budget."""
        start_time = time.time()

        try:
            async with asyncio.timeout(self.budget_seconds):
                yield
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            raise TimeBudgetExceededError(
                f"Execution {execution_id} exceeded time budget "
                f"({elapsed:.1f}s > {self.budget_seconds}s)"
            )
```

**Rate Limiter:** `src/wflo/governance/rate_limiter.py`

```python
"""Rate limiting using Redis."""

class RateLimiter:
    """Token bucket rate limiter.

    Usage:
        limiter = RateLimiter(
            redis_client=redis_client,
            rate=100,  # 100 requests
            per_seconds=60,  # per minute
        )

        await limiter.acquire(resource_id="api-key-123", tokens=1)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        rate: int,
        per_seconds: int,
        burst: Optional[int] = None,
    ):
        self.redis = redis_client
        self.rate = rate
        self.per_seconds = per_seconds
        self.burst = burst or rate

    async def acquire(
        self,
        resource_id: str,
        tokens: int = 1,
        wait: bool = False,
    ) -> bool:
        """Acquire tokens from bucket.

        Returns:
            True if acquired, False if rate limited

        Raises:
            RateLimitExceededError: If rate limit exceeded and wait=False
        """
        # Token bucket algorithm implementation
        # Refill tokens based on elapsed time
        # Check if enough tokens available
        # Consume tokens if available
```

#### Integration with WfloWorkflow:

```python
from wflo.sdk.workflow import WfloWorkflow
from wflo.governance.time_budget import TimeBudgetEnforcer
from wflo.governance.rate_limiter import RateLimiter

workflow = WfloWorkflow(
    name="rate-limited-workflow",
    budget_usd=10.0,
    time_budget_seconds=60,  # NEW: Time budget
)

# Time budget automatically enforced
result = await workflow.execute(workflow_logic, inputs)
```

#### Tests:
- [ ] Time budget enforcement (timeout after N seconds)
- [ ] Rate limiter token bucket algorithm
- [ ] Burst capacity handling
- [ ] Distributed rate limiting across workers
- [ ] Integration with workflow execution

---

### **Phase 5: Human-in-the-Loop (HITL) Approval Gates** ⭐ CRITICAL

**Priority:** HIGHEST (Critical for enterprise adoption)
**Estimated Duration:** 3-4 weeks
**Dependencies:** Phase 3 (coordinator for execution tracking)
**Estimated Effort:** 60-80 hours

#### Objectives:
Build approval gates that pause workflows for human decision-making on sensitive operations.

#### Why This is Critical:
- **Enterprise requirement:** No company will deploy agents that can autonomously delete data, execute transactions, or modify infrastructure without human oversight
- **Compliance:** SOC2, HIPAA, GDPR all require human approval for sensitive operations
- **Trust:** Managers need visibility and control over agent actions
- **Audit trail:** Complete history of who approved what and why

#### Features to Implement:

1. **Approval Request Service**
   - Request approval for sensitive operations
   - Risk assessment (low, medium, high, critical)
   - Operation context (what, why, who, cost)
   - Timeout and expiration handling

2. **Notification System**
   - Slack integration (primary)
   - Email notifications
   - Microsoft Teams integration
   - Push notifications

3. **Web UI for Approvals**
   - Clean approval card interface
   - Operation details and risk factors
   - Approve/Reject with comments
   - Audit trail viewer

4. **Policy Engine**
   - Define approval policies (who can approve what)
   - Auto-approval conditions
   - Escalation rules
   - Approval routing

#### Database Schema:

**File:** `migrations/005_approval_gates.sql`

```sql
-- Approval requests
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,

    -- What needs approval
    operation_type VARCHAR(100) NOT NULL,  -- 'sql_query', 'api_call', 'file_delete'
    operation_details JSONB NOT NULL,

    -- Context
    reason TEXT,
    requested_by VARCHAR(255),

    -- Risk assessment
    risk_level VARCHAR(50) NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    risk_factors JSONB,
    estimated_cost_usd DECIMAL(10, 4),

    -- Approval workflow
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    required_approvers TEXT[],
    approved_by VARCHAR(255),
    rejected_by VARCHAR(255),
    approval_comment TEXT,

    -- Timing
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    responded_at TIMESTAMP,

    -- Notifications
    notification_sent_at TIMESTAMP,
    notification_channels TEXT[],

    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
);

CREATE INDEX idx_approval_status ON approval_requests(status, expires_at);

-- Approval policies
CREATE TABLE approval_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    operation_pattern JSONB NOT NULL,
    required_approvers TEXT[],
    auto_approve_conditions JSONB,
    approval_timeout_seconds INT NOT NULL DEFAULT 3600,
    notification_channels TEXT[] NOT NULL DEFAULT ARRAY['slack']
);

-- Audit log
CREATE TABLE approval_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'created', 'approved', 'rejected', 'expired'
    actor VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id)
);
```

#### Implementation Files:

```
src/wflo/services/approval/
├── __init__.py
├── service.py           # ApprovalGateService
├── models.py            # ApprovalRequest, ApprovalResponse
└── policy.py            # Policy engine

src/wflo/integrations/
├── slack.py             # Slack notifications
├── email.py             # Email notifications
└── teams.py             # MS Teams notifications

src/wflo/sdk/decorators/
└── require_approval.py  # @require_approval decorator

frontend/                # NEW: Web UI
├── src/
│   ├── pages/
│   │   ├── ApprovalDetail.tsx
│   │   └── ApprovalList.tsx
│   ├── components/
│   │   ├── ApprovalCard.tsx
│   │   └── RiskBadge.tsx
│   └── api/
│       └── approvals.ts
├── package.json
└── tsconfig.json

tests/unit/
├── test_approval_service.py
├── test_approval_decorator.py
└── test_slack_integration.py

tests/integration/
└── test_approval_workflow.py

examples/approval/
├── sql_approval_example.py
├── api_approval_example.py
└── README.md
```

**Approval Service:** `src/wflo/services/approval/service.py`

```python
"""Approval Gates Service."""

class ApprovalGateService:
    """Service for managing approval gates and HITL."""

    async def request_approval(
        self,
        execution_id: str,
        workflow_name: str,
        operation_type: str,
        operation_details: Dict[str, Any],
        reason: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        timeout_seconds: int = 3600,
    ) -> ApprovalResponse:
        """Request approval for an operation.

        This will:
        1. Create approval request in database
        2. Send notifications to approvers
        3. Wait for approval/rejection (or timeout)
        4. Return response
        """
        request_id = str(uuid.uuid4())

        # Create request in DB
        await self._create_request(request_id, ...)

        # Send notifications
        await self._send_notifications(request_id, ...)

        # Wait for response
        response = await self._wait_for_response(request_id, timeout_seconds)

        return response

    async def approve(self, request_id: str, approved_by: str, comment: str):
        """Approve a pending request."""

    async def reject(self, request_id: str, rejected_by: str, comment: str):
        """Reject a pending request."""
```

**Decorator:** `src/wflo/sdk/decorators/require_approval.py`

```python
"""Decorator for operations requiring approval."""

def require_approval(
    operation_type: str,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    reason: Optional[str] = None,
):
    """Decorator to require human approval before execution.

    Usage:
        @require_approval(
            operation_type="sql_delete",
            risk_level=RiskLevel.HIGH,
            reason="Deleting customer records",
        )
        async def delete_records(table: str, where: str):
            await db.execute(f"DELETE FROM {table} WHERE {where}")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            approval_service = ApprovalGateService()

            # Request approval
            response = await approval_service.request_approval(
                execution_id=get_current_execution_id(),
                operation_type=operation_type,
                operation_details={"function": func.__name__, "args": args},
                reason=reason,
                risk_level=risk_level,
            )

            if not response.approved:
                raise ApprovalRequiredError("Operation rejected")

            # Execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**Frontend UI:** `frontend/src/pages/ApprovalDetail.tsx`

```typescript
/**
 * Approval Detail Page
 *
 * Shows detailed approval request with:
 * - Operation context (who, what, why)
 * - Risk assessment
 * - Approve/Reject buttons
 * - Comment field
 */

const ApprovalDetail: React.FC = () => {
  const { requestId } = useParams();
  const [request, setRequest] = useState<ApprovalRequest | null>(null);

  const handleApprove = async () => {
    await fetch(`/api/approvals/${requestId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ comment }),
    });
    alert('✅ Approved!');
  };

  return (
    <div className="approval-card">
      <h1>Approval Required: {request.workflow_name}</h1>

      {/* Risk Badge */}
      <RiskBadge level={request.risk_level} />

      {/* Operation Details */}
      <section>
        <h2>What</h2>
        <pre>{JSON.stringify(request.operation_details, null, 2)}</pre>
      </section>

      {/* Actions */}
      <button onClick={handleApprove}>✅ Approve</button>
      <button onClick={handleReject}>❌ Reject</button>
    </div>
  );
};
```

**Slack Integration:** `src/wflo/integrations/slack.py`

```python
"""Slack integration for approval notifications."""

class SlackNotifier:
    """Send approval notifications to Slack."""

    async def send_approval_request(
        self,
        request_id: str,
        workflow_name: str,
        operation_type: str,
        risk_level: str,
        approval_url: str,
    ):
        """Send approval request to Slack with interactive button."""
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Approval Required: {workflow_name}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Operation:*\n{operation_type}"},
                        {"type": "mrkdwn", "text": f"*Risk:*\n{risk_level.upper()}"},
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ Review & Approve"},
                            "url": approval_url,
                            "style": "primary",
                        },
                    ],
                },
            ],
        }

        await self._send_to_slack(message)
```

#### Example Usage:

```python
"""Example: SQL query approval."""

from wflo.sdk.decorators.require_approval import require_approval, RiskLevel

@require_approval(
    operation_type="sql_delete",
    risk_level=RiskLevel.HIGH,
    reason="Monthly cleanup of expired records",
)
async def cleanup_expired_records(cutoff_date: str):
    """Delete expired records - requires approval."""
    query = f"DELETE FROM records WHERE expires_at < '{cutoff_date}'"
    await db.execute(query)
    return {"deleted": True}

# When this runs:
# 1. Workflow pauses
# 2. Slack notification sent to approvers
# 3. Manager clicks link, sees details
# 4. Manager approves/rejects
# 5. Workflow resumes or fails
```

#### Manager Experience:

1. **Receives Slack notification:**
   ```
   🚨 Approval Required: cleanup-workflow

   Operation: sql_delete
   Risk: HIGH

   [✅ Review & Approve]
   ```

2. **Clicks button → Opens web UI:**
   ```
   ┌─────────────────────────────────────────┐
   │ Approval Required                  HIGH │
   ├─────────────────────────────────────────┤
   │ Who: finance-agent-001                  │
   │ What: DELETE FROM records WHERE...      │
   │ Why: Monthly cleanup of expired records │
   │ Cost: $0.02 (estimated)                 │
   ├─────────────────────────────────────────┤
   │ Comment: [Optional]                     │
   │                                         │
   │ [✅ Approve]  [❌ Reject]               │
   └─────────────────────────────────────────┘
   ```

3. **Clicks Approve:**
   - Workflow resumes
   - Audit log updated
   - Execution completes

#### Tests:
- [ ] Approval request creation and persistence
- [ ] Notification sending (Slack, email)
- [ ] Approval/rejection handling
- [ ] Timeout and expiration
- [ ] Audit trail logging
- [ ] UI rendering and interaction
- [ ] Integration with workflow execution

#### Deployment:

**Frontend:**
```bash
cd frontend
npm install
npm run build
# Deploy to Vercel/Netlify or serve from backend
```

**Backend:**
```bash
# Set environment variables
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export APPROVAL_UI_URL="https://approvals.wflo.app"

# Run service
python -m wflo.services.approval.server
```

---

### **Phase 6: Multi-Agent Coordination & Observability** ⏳

**Priority:** MEDIUM
**Estimated Duration:** 3-4 weeks
**Dependencies:** Phase 3 (coordinator), Phase 5 (approval gates)
**Estimated Effort:** 60-80 hours

#### Part A: Multi-Agent Coordination

**Features:**
1. **Consensus Voting**
   - Majority voting
   - Weighted voting
   - Unanimous voting
   - Quorum thresholds

2. **State Synchronization**
   - Shared state across agents
   - Conflict detection
   - Merge strategies

3. **Deadlock Detection**
   - Dependency graph analysis
   - Cycle detection
   - Automatic resolution

**Implementation:**

```
src/wflo/services/consensus/
├── service.py           # ConsensusService
├── strategies.py        # Voting strategies
└── deadlock.py          # Deadlock detection

examples/multi_agent/
├── voting_example.py
├── consensus_example.py
└── README.md
```

#### Part B: Observability

**Features:**
1. **Distributed Tracing**
   - OpenTelemetry integration
   - Trace propagation across services
   - Span creation for operations
   - Trace visualization

2. **Metrics Aggregation**
   - Prometheus metrics export
   - Custom metrics (execution time, cost, etc.)
   - Grafana dashboards

3. **Error Tracking**
   - Structured error logging
   - Error aggregation
   - Alerting rules

**Implementation:**

```
src/wflo/observability/
├── tracing.py           # OpenTelemetry setup
├── metrics.py           # Prometheus metrics (exists)
└── alerts.py            # Alerting service

monitoring/
├── dashboards/
│   ├── workflow_performance.json
│   └── cost_tracking.json
└── alerts/
    └── alert_rules.yml
```

---

### **Phase 7: Deployment Controls** ⏳

**Priority:** LOW (Nice to have)
**Estimated Duration:** 2-3 weeks
**Dependencies:** All previous phases
**Estimated Effort:** 40-60 hours

**Features:**
1. **Workflow Versioning**
   - Semantic versioning (v1.0.0, v1.1.0)
   - Version history
   - Rollback to previous versions

2. **Canary Deployments**
   - Traffic splitting (10% to new version)
   - Gradual rollout
   - Automatic rollback on errors

3. **A/B Testing**
   - Variant allocation
   - Statistical analysis
   - Winner selection

**Implementation:**

```
src/wflo/deployment/
├── versioning.py        # Version management
├── canary.py            # Canary deployment
└── ab_test.py           # A/B testing

examples/deployment/
├── canary_deployment.py
├── ab_test_example.py
└── README.md
```

---

## 📅 Recommended Implementation Schedule

### **Sprint Plan (12-week timeline)**

| Sprint | Duration | Phase | Deliverables |
|--------|----------|-------|--------------|
| **Sprint 1** | Week 1-2 | Phase 3 (Orchestration) | CoordinatorService, @coordinated_task, tests |
| **Sprint 2** | Week 3-4 | Phase 3 (Orchestration) | Heartbeat monitoring, integration tests, examples |
| **Sprint 3** | Week 5-6 | Phase 5 (HITL) Part 1 | ApprovalGateService, database schema, decorator |
| **Sprint 4** | Week 7-8 | Phase 5 (HITL) Part 2 | Web UI, Slack integration, tests |
| **Sprint 5** | Week 9-10 | Phase 4 (Governance) | Time budget, rate limiter, throttling |
| **Sprint 6** | Week 11-12 | Phase 6 (Multi-agent + Observability) | Consensus, tracing, metrics |

**Phase 7 (Deployment Controls)** can be implemented later based on customer demand.

### **Alternative: MVP-First Approach**

If you need to ship faster, prioritize **Phase 3 + Phase 5** only:

| Sprint | Duration | Phase | Deliverables |
|--------|----------|-------|--------------|
| **Sprint 1** | Week 1-2 | Phase 3 | Orchestration (minimal) |
| **Sprint 2-3** | Week 3-6 | Phase 5 | HITL Approval Gates (complete) |

**Why this works:**
- Phase 3 provides foundation for distributed execution
- Phase 5 (HITL) is the killer feature for enterprise sales
- Phases 4, 6, 7 can be added incrementally based on customer feedback

---

## 🧪 Testing Strategy

### **Test Coverage Requirements**

| Phase | Unit Tests | Integration Tests | E2E Tests |
|-------|------------|-------------------|-----------|
| Phase 3 | 80%+ | 5+ scenarios | 2+ workflows |
| Phase 4 | 80%+ | 3+ scenarios | 1+ workflow |
| Phase 5 | 85%+ | 10+ scenarios | 5+ workflows |
| Phase 6 | 75%+ | 5+ scenarios | 2+ workflows |
| Phase 7 | 70%+ | 3+ scenarios | 1+ workflow |

### **Testing Pyramid**

```
           /\
          /  \     E2E Tests (10)
         /    \    - Full workflow execution
        /------\   - Cross-service integration
       /        \
      /  Unit    \ Integration Tests (50)
     /   Tests   \- Service interactions
    /    (200)    \- Database operations
   /--------------\
```

---

## 🚀 Deployment Architecture

### **Production Deployment (Kubernetes)**

```yaml
# High-level architecture
┌─────────────────────────────────────────────────────────┐
│                 Customer's K8s Cluster                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Agent Pods       │  │ Wflo Services    │           │
│  │ (their code)     │  │ (we provide)     │           │
│  │                  │  │                  │           │
│  │ - DeepAgents     │  │ - Coordinator    │           │
│  │ - Custom agents  │  │ - Approval Gates │           │
│  │                  │  │ - Circuit Breaker│           │
│  └──────────────────┘  └──────────────────┘           │
│          ↓                       ↓                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │          Shared Infrastructure                  │  │
│  │  - PostgreSQL (state, checkpoints, approvals)  │  │
│  │  - Redis (locks, rate limits, circuit state)   │  │
│  │  - TimescaleDB (metrics, traces)              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### **Helm Chart Installation**

```bash
# Install Wflo services
helm install wflo wflo/full-stack \
  --set database.host=$POSTGRES_HOST \
  --set redis.host=$REDIS_HOST \
  --set services.coordinator.replicas=3 \
  --set services.approval.replicas=2
```

---

## 📊 Success Metrics

### **Technical Metrics**

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | >80% | 100% (Phases 1-2) |
| API Response Time | <100ms (p95) | TBD |
| Workflow Execution Success Rate | >99% | TBD |
| Dead Worker Recovery Time | <30s | TBD |
| Approval Response Time | <2min (median) | TBD |

### **Business Metrics**

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Time to First Workflow | <30 min | Developer experience |
| Approval Completion Rate | >90% | Manager confidence |
| Production Incidents | <1/month | Reliability |
| Customer Adoption | 10+ enterprises | Product-market fit |

---

## 🆘 Getting Help

### **For Developers Implementing This:**

1. **Read Phase 1-2 Code First**
   - Understand existing patterns
   - Review test structure
   - Check examples

2. **Start with Phase 3**
   - Foundational for everything else
   - Well-defined scope
   - Clear success criteria

3. **Use This Document**
   - Copy code snippets as starting points
   - Follow database schema exactly
   - Implement tests alongside features

4. **Ask Questions**
   - Open GitHub issues for clarifications
   - Check existing examples
   - Review integration tests

### **Key Resources**

- **Codebase:** `/home/user/wflo/`
- **Tests:** `tests/unit/`, `tests/integration/`
- **Examples:** `examples/`
- **Docs:** `docs/`

---

## ✅ Definition of Done (Per Phase)

### **Phase is Complete When:**

- [ ] All features implemented
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Examples created and tested
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] Load tested (if applicable)
- [ ] Security reviewed (for sensitive features)

---

## 📝 Notes for Next Developer

### **Important Conventions:**

1. **Database Migrations:** Use sequential numbering (`003_`, `004_`, etc.)
2. **Test Structure:** Mirror source structure in `tests/`
3. **Async Everything:** All I/O operations must be async
4. **Error Handling:** Use custom exceptions, log with structlog
5. **Type Hints:** Required for all function signatures
6. **Docstrings:** Google style, include usage examples

### **Common Pitfalls:**

1. **SQLAlchemy 2.0:** Use `select()` not `Query`, `AsyncSession` not `Session`
2. **Asyncpg + Supabase:** Disable prepared statements (see `engine.py`)
3. **Context Variables:** Use for execution_id, budget (thread-safe)
4. **Mock Generators:** `side_effect = lambda: generator()` for multiple calls

### **Quick Start Commands:**

```bash
# Setup
poetry install
cp .env.example .env

# Run tests
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v -m integration

# Run examples
poetry run python examples/resilience_patterns/retry_with_llm.py

# Database migration
alembic upgrade head

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

---

## 🎯 Success Story

**When this roadmap is complete, developers will be able to:**

```python
from wflo.sdk.workflow import WfloWorkflow
from wflo.sdk.decorators.coordinated import coordinated_task
from wflo.sdk.decorators.require_approval import require_approval, RiskLevel
from wflo.resilience.retry import retry_with_backoff
from wflo.resilience.circuit_breaker import circuit_breaker

# Define workflow with full production capabilities
workflow = WfloWorkflow(
    name="production-workflow",
    budget_usd=100.0,
    time_budget_seconds=300,
)

@coordinated_task(task_id="step-1")  # Distributed coordination
@retry_with_backoff(max_retries=3)   # Auto-retry on failure
@circuit_breaker(name="external-api") # Prevent cascading failures
async def fetch_data(execution_id: str):
    return await api.get_data()

@coordinated_task(task_id="step-2")
@require_approval(                    # Human approval required
    operation_type="sql_delete",
    risk_level=RiskLevel.HIGH,
)
async def cleanup_data(execution_id: str, data: dict):
    await db.execute("DELETE FROM ...")

# Execute with full observability
result = await workflow.execute(workflow_logic, inputs)

# Full audit trail, cost tracking, approval history available
```

**This is production-ready AI agent orchestration.** 🚀

---

## 📧 Contact

For questions about this roadmap:
- **GitHub Issues:** https://github.com/wflo-ai/wflo/issues
- **Documentation:** https://docs.wflo.ai
- **Email:** support@wflo.ai

---

**Document Version:** 1.0
**Last Updated:** 2025-01-12
**Next Review:** After Phase 3 completion
