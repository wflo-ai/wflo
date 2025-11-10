# Phase 4: Kafka Event Streaming

**Duration**: 8-12 hours
**Goal**: Implement Kafka-based event streaming for workflow state changes, cost alerts, and audit logging.

## Prerequisites

✅ Kafka configured in docker-compose.yml (already exists)
✅ confluent-kafka dependency (assumed installed)
✅ Settings configured for Kafka connection

## Why Kafka?

**Event-Driven Architecture Benefits:**
- **Asynchronous Processing**: Decouple event producers from consumers
- **Scalability**: Handle high-throughput events (10K+ events/sec)
- **Durability**: Events are persisted, can replay history
- **Multiple Consumers**: Different services can subscribe to same events
- **Real-time Monitoring**: Stream events to dashboards, alerts, logging

**Use Cases in Wflo:**
1. **Workflow Events**: Started, completed, failed, cancelled
2. **Cost Alerts**: Budget thresholds reached (50%, 75%, 90%)
3. **Audit Log**: All workflow operations for compliance
4. **Metrics Stream**: Real-time metrics to monitoring systems
5. **External Integrations**: Webhook notifications, Slack alerts

## Event Schema Design

### Base Event

All events share common fields:

```python
class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = "wflo"
    version: str = "1.0.0"
```

### Event Types

1. **WorkflowEvent** - Workflow lifecycle events
2. **CostEvent** - Cost tracking and budget alerts
3. **SandboxEvent** - Code execution events
4. **AuditEvent** - Audit trail events

## Implementation Tasks

### Task 1: Event Schema Definitions (2 hours)

**File**: `src/wflo/events/schemas.py`

**Event Types:**

```python
class WorkflowEvent(BaseEvent):
    """Workflow lifecycle event."""
    workflow_id: str
    execution_id: str
    status: WorkflowStatus  # started, completed, failed, cancelled
    duration_seconds: float | None = None
    error: str | None = None

class CostEvent(BaseEvent):
    """Cost tracking and budget alert event."""
    execution_id: str
    model: str
    cost_usd: float
    total_cost_usd: float
    budget_limit_usd: float | None
    budget_percentage: float | None
    alert_type: str | None  # warning_50, warning_75, warning_90, exceeded

class SandboxEvent(BaseEvent):
    """Sandbox code execution event."""
    execution_id: str
    language: str
    exit_code: int
    duration_seconds: float
    status: str  # success, error, timeout

class AuditEvent(BaseEvent):
    """Audit trail event."""
    actor: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
```

### Task 2: Kafka Producer (3 hours)

**File**: `src/wflo/events/producer.py`

**Requirements:**
- Async producer wrapper around confluent_kafka
- Idempotent producer (exactly-once semantics)
- Automatic serialization (Pydantic → JSON)
- Error handling and retries
- Partitioning by workflow_id for ordering

**API Design:**

```python
from wflo.events import KafkaProducer, WorkflowEvent

async with KafkaProducer() as producer:
    event = WorkflowEvent(
        event_type="workflow.started",
        workflow_id="abc-123",
        execution_id="exec-456",
        status="running",
    )
    await producer.send("wflo.workflows", event)
```

**Key Features:**
- Connection pooling
- Automatic topic creation
- Compression (snappy)
- Batching for throughput
- Monitoring metrics

### Task 3: Kafka Consumer (3 hours)

**File**: `src/wflo/events/consumer.py`

**Requirements:**
- Async consumer with background thread
- Consumer group management
- Auto commit offset tracking
- Graceful shutdown
- Message deserialization

**API Design:**

```python
from wflo.events import KafkaConsumer, WorkflowEvent

async with KafkaConsumer(
    topics=["wflo.workflows"],
    group_id="wflo-monitor",
) as consumer:
    async for message in consumer:
        event = WorkflowEvent(**message.value)
        await process_event(event)
```

### Task 4: Event Publisher Integration (2 hours)

**Files to modify:**
- `src/wflo/temporal/workflows.py`
- `src/wflo/temporal/activities.py`
- `src/wflo/cost/tracker.py`

**Integration Points:**

1. **Workflow Start** → Publish `WorkflowEvent(started)`
2. **Workflow Complete** → Publish `WorkflowEvent(completed)`
3. **Workflow Failed** → Publish `WorkflowEvent(failed)`
4. **Cost Tracked** → Publish `CostEvent`
5. **Budget Exceeded** → Publish `CostEvent(exceeded)`
6. **Sandbox Executed** → Publish `SandboxEvent`

**Example:**

```python
from wflo.events import get_event_publisher

@workflow.defn
class WfloWorkflow:
    async def run(self, workflow_id: str) -> dict:
        publisher = get_event_publisher()

        # Publish workflow started event
        await publisher.publish(WorkflowEvent(
            event_type="workflow.started",
            workflow_id=workflow_id,
            execution_id=self.execution_id,
            status="running",
        ))

        try:
            result = await self.execute_steps()

            # Publish workflow completed event
            await publisher.publish(WorkflowEvent(
                event_type="workflow.completed",
                workflow_id=workflow_id,
                execution_id=self.execution_id,
                status="completed",
                duration_seconds=elapsed_time,
            ))

            return result
        except Exception as e:
            # Publish workflow failed event
            await publisher.publish(WorkflowEvent(
                event_type="workflow.failed",
                workflow_id=workflow_id,
                execution_id=self.execution_id,
                status="failed",
                error=str(e),
            ))
            raise
```

### Task 5: Topic Configuration (1 hour)

**File**: `src/wflo/events/topics.py`

**Topics:**
- `wflo.workflows` - Workflow lifecycle events
- `wflo.costs` - Cost tracking and alerts
- `wflo.sandbox` - Code execution events
- `wflo.audit` - Audit trail events
- `wflo.metrics` - Real-time metrics stream

**Configuration:**
- Partitions: 3 per topic (scalability)
- Replication: 1 (development), 3 (production)
- Retention: 7 days (default), 30 days (audit)
- Compression: snappy (balance speed/size)

### Task 6: Testing (2 hours)

**File**: `tests/integration/test_kafka.py`

**Test Cases:**
1. Producer connection and message send
2. Consumer connection and message receive
3. Event serialization/deserialization
4. Idempotent producer (no duplicates)
5. Consumer offset tracking
6. Consumer group coordination
7. Error handling and retries

## Implementation Order

1. ✅ Create implementation plan
2. ⬜ Define event schemas (Pydantic models)
3. ⬜ Implement Kafka producer
4. ⬜ Implement Kafka consumer
5. ⬜ Configure topics
6. ⬜ Integrate with workflows and activities
7. ⬜ Write integration tests
8. ⬜ Add monitoring metrics
9. ⬜ Commit and push

## Key Technical Decisions

### confluent-kafka vs kafka-python
- **Choice**: confluent-kafka (C library wrapper)
- **Reason**: 10x faster, better reliability, official Confluent support

### Async vs Sync
- **Producer**: Async wrapper around sync producer (run_in_executor)
- **Consumer**: Background thread with async message queue
- **Reason**: confluent-kafka doesn't have native async, but we wrap it

### Serialization Format
- **Choice**: JSON (via Pydantic)
- **Alternatives**: Avro (more efficient), Protobuf (more structured)
- **Reason**: JSON is simpler, human-readable, sufficient for now

### Topic Naming Convention
- **Pattern**: `{service}.{domain}` (e.g., wflo.workflows)
- **Reason**: Easy to organize, filter, and manage permissions

## Success Criteria

✅ Events published to Kafka from workflows and activities
✅ Consumers can subscribe and process events
✅ No message loss (at-least-once delivery)
✅ Idempotent producer prevents duplicates
✅ Integration tests pass (95%+ coverage)
✅ Metrics track producer/consumer health

## Monitoring Metrics

New Prometheus metrics:

```python
kafka_messages_produced_total = Counter(
    "wflo_kafka_messages_produced_total",
    "Total messages produced to Kafka",
    ["topic", "status"],  # status: success or error
)

kafka_messages_consumed_total = Counter(
    "wflo_kafka_messages_consumed_total",
    "Total messages consumed from Kafka",
    ["topic", "consumer_group"],
)

kafka_producer_latency_seconds = Histogram(
    "wflo_kafka_producer_latency_seconds",
    "Kafka producer latency",
    ["topic"],
)
```

## Use Cases Enabled

### 1. Real-Time Dashboard
Stream workflow events to web dashboard:
- Current running workflows
- Completed/failed counts
- Average duration
- Cost burn rate

### 2. Budget Alerts
Trigger alerts when budget thresholds reached:
- Email/Slack notification at 90%
- Auto-pause workflows at 100%
- Daily cost reports

### 3. Audit Compliance
Immutable audit trail for compliance:
- Who executed what workflow
- What data was accessed
- When and why actions were taken

### 4. External Integrations
Connect to external systems:
- Webhooks on workflow completion
- Zapier/Make.com integrations
- Custom notification systems

### 5. Data Analytics
Stream events to data warehouse:
- BigQuery, Snowflake, Redshift
- Historical trend analysis
- Cost optimization insights

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Kafka unavailable | Graceful degradation: log events locally, sync later |
| Message ordering issues | Partition by workflow_id for ordering guarantee |
| Consumer lag | Monitor consumer lag metrics, scale consumers |
| Schema evolution | Use schema registry (future enhancement) |
| Duplicate messages | Idempotent consumers (handle duplicates gracefully) |

## Rollout Strategy

1. **Phase 4a**: Kafka infrastructure + producer (this phase)
2. **Phase 4b**: Consumer framework
3. **Phase 4c**: Workflow integration
4. **Phase 4d**: Monitoring and alerting
5. **Phase 4e**: Production testing

## Next Phase Preview

**Phase 5: Security Hardening** - After Kafka implementation, we'll focus on:
- Container image scanning
- gVisor runtime evaluation
- Security audit logging (using Kafka!)
- Penetration testing
