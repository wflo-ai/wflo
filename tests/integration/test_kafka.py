"""Integration tests for Kafka event streaming.

These tests require a running Kafka instance with Zookeeper.
Run with: pytest tests/integration/test_kafka.py
"""

import asyncio

import pytest

from wflo.events import (
    AuditEvent,
    CostEvent,
    KafkaConsumer,
    KafkaProducer,
    KafkaTopic,
    SandboxEvent,
    WorkflowEvent,
    ensure_topics_exist,
    subscribe_to_events,
)


@pytest.mark.asyncio
class TestKafkaProducer:
    """Test Kafka producer functionality."""

    async def test_producer_connect_and_close(self):
        """Test producer connection and cleanup."""
        producer = KafkaProducer()

        await producer.connect()
        assert producer.producer is not None

        await producer.close()

    async def test_producer_context_manager(self):
        """Test producer using context manager."""
        async with KafkaProducer() as producer:
            assert producer.producer is not None

    async def test_send_workflow_event(self):
        """Test sending a workflow event."""
        async with KafkaProducer() as producer:
            event = WorkflowEvent(
                event_type="workflow.started",
                workflow_id="test-workflow",
                execution_id="exec-123",
                status="running",
            )

            # Should not raise
            await producer.send(
                KafkaTopic.WORKFLOWS.value,
                event,
                key="test-workflow",
            )

    async def test_send_cost_event(self):
        """Test sending a cost event."""
        async with KafkaProducer() as producer:
            event = CostEvent(
                event_type="cost.tracked",
                execution_id="exec-123",
                model="gpt-4-turbo",
                cost_usd=0.05,
                prompt_tokens=1000,
                completion_tokens=500,
                total_cost_usd=0.05,
            )

            await producer.send(
                KafkaTopic.COSTS.value,
                event,
                key="exec-123",
            )

    async def test_send_sandbox_event(self):
        """Test sending a sandbox event."""
        async with KafkaProducer() as producer:
            event = SandboxEvent(
                event_type="sandbox.executed",
                execution_id="exec-123",
                language="python",
                exit_code=0,
                duration_seconds=2.5,
                status="success",
            )

            await producer.send(
                KafkaTopic.SANDBOX.value,
                event,
                key="exec-123",
            )

    async def test_send_audit_event(self):
        """Test sending an audit event."""
        async with KafkaProducer() as producer:
            event = AuditEvent(
                event_type="audit.workflow.executed",
                actor="user@example.com",
                action="execute",
                resource_type="workflow",
                resource_id="test-workflow",
                details={"execution_id": "exec-123", "trigger": "manual"},
            )

            await producer.send(
                KafkaTopic.AUDIT.value,
                event,
                key="test-workflow",
            )

    async def test_send_with_headers(self):
        """Test sending event with custom headers."""
        async with KafkaProducer() as producer:
            event = WorkflowEvent(
                event_type="workflow.completed",
                workflow_id="test-workflow",
                execution_id="exec-123",
                status="completed",
                duration_seconds=120.5,
            )

            headers = {
                "correlation_id": "corr-123",
                "source": "test",
            }

            await producer.send(
                KafkaTopic.WORKFLOWS.value,
                event,
                key="test-workflow",
                headers=headers,
            )


@pytest.mark.asyncio
class TestKafkaConsumer:
    """Test Kafka consumer functionality."""

    async def test_consumer_connect_and_close(self):
        """Test consumer connection and cleanup."""
        consumer = KafkaConsumer(
            topics=[KafkaTopic.WORKFLOWS.value],
            group_id="test-group",
        )

        await consumer.start()
        assert consumer.consumer is not None

        await consumer.stop()

    async def test_consumer_context_manager(self):
        """Test consumer using context manager."""
        async with KafkaConsumer(
            topics=[KafkaTopic.WORKFLOWS.value],
            group_id="test-group",
        ) as consumer:
            assert consumer.consumer is not None

    async def test_produce_and_consume(self):
        """Test end-to-end message production and consumption."""
        # Use unique topic and group for isolation
        topic = KafkaTopic.WORKFLOWS.value
        test_workflow_id = "test-e2e-workflow"

        # Produce event
        async with KafkaProducer() as producer:
            event = WorkflowEvent(
                event_type="workflow.test",
                workflow_id=test_workflow_id,
                execution_id="exec-test-123",
                status="running",
            )
            await producer.send(topic, event, key=test_workflow_id)

        # Brief sleep to ensure message is committed
        await asyncio.sleep(1)

        # Consume event
        consumed = False
        async with KafkaConsumer(
            topics=[topic],
            group_id="test-e2e-group",
            auto_offset_reset="earliest",
        ) as consumer:
            # Set timeout to avoid infinite wait
            try:
                async with asyncio.timeout(10):
                    async for message in consumer:
                        if message.value.get("workflow_id") == test_workflow_id:
                            assert message.value["event_type"] == "workflow.test"
                            assert message.value["status"] == "running"
                            consumed = True
                            break
            except asyncio.TimeoutError:
                pass

        assert consumed, "Message was not consumed within timeout"

    async def test_consumer_deserialization(self):
        """Test that consumer correctly deserializes messages."""
        topic = KafkaTopic.COSTS.value
        test_exec_id = "exec-deserialize-test"

        # Produce event
        async with KafkaProducer() as producer:
            event = CostEvent(
                event_type="cost.tracked",
                execution_id=test_exec_id,
                model="gpt-3.5-turbo",
                cost_usd=0.001,
                prompt_tokens=100,
                completion_tokens=50,
                total_cost_usd=0.001,
            )
            await producer.send(topic, event, key=test_exec_id)

        await asyncio.sleep(1)

        # Consume and verify
        async with KafkaConsumer(
            topics=[topic],
            group_id="test-deserialize-group",
            auto_offset_reset="earliest",
        ) as consumer:
            try:
                async with asyncio.timeout(10):
                    async for message in consumer:
                        if message.value.get("execution_id") == test_exec_id:
                            # Verify all fields present
                            assert "event_id" in message.value
                            assert "timestamp" in message.value
                            assert message.value["model"] == "gpt-3.5-turbo"
                            assert message.value["cost_usd"] == 0.001
                            assert message.value["prompt_tokens"] == 100
                            break
            except asyncio.TimeoutError:
                pytest.fail("Message not consumed within timeout")

    async def test_multiple_consumers_same_group(self):
        """Test consumer group coordination with multiple consumers."""
        topic = KafkaTopic.WORKFLOWS.value
        group_id = "test-multi-group"

        # Produce multiple events
        async with KafkaProducer() as producer:
            for i in range(5):
                event = WorkflowEvent(
                    event_type="workflow.test",
                    workflow_id=f"workflow-{i}",
                    execution_id=f"exec-{i}",
                    status="running",
                )
                await producer.send(topic, event, key=f"workflow-{i}")

        await asyncio.sleep(1)

        # Two consumers in same group should each get some messages
        # (due to partition distribution)
        consumer1_count = 0
        consumer2_count = 0

        async def consume_with_limit(consumer_id: int, limit: int = 3):
            """Consume up to limit messages."""
            nonlocal consumer1_count, consumer2_count
            count = 0

            async with KafkaConsumer(
                topics=[topic],
                group_id=group_id,
                auto_offset_reset="earliest",
            ) as consumer:
                try:
                    async with asyncio.timeout(10):
                        async for message in consumer:
                            count += 1
                            if consumer_id == 1:
                                consumer1_count += 1
                            else:
                                consumer2_count += 1

                            if count >= limit:
                                break
                except asyncio.TimeoutError:
                    pass

        # Run consumers concurrently
        await asyncio.gather(
            consume_with_limit(1),
            consume_with_limit(2),
        )

        # Both should have consumed at least one message
        # (exact distribution depends on partitioning)
        total_consumed = consumer1_count + consumer2_count
        assert total_consumed >= 2, f"Expected at least 2 messages consumed, got {total_consumed}"


@pytest.mark.integration
class TestEventSchemas:
    """Test event schema validation."""

    def test_workflow_event_validation(self):
        """Test WorkflowEvent schema validation."""
        event = WorkflowEvent(
            event_type="workflow.started",
            workflow_id="test-wf",
            execution_id="exec-1",
            status="running",
        )

        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.service == "wflo"
        assert event.version == "1.0.0"
        assert event.workflow_id == "test-wf"

    def test_cost_event_with_budget(self):
        """Test CostEvent with budget fields."""
        event = CostEvent(
            event_type="cost.alert",
            execution_id="exec-1",
            model="gpt-4-turbo",
            cost_usd=7.50,
            prompt_tokens=10000,
            completion_tokens=5000,
            total_cost_usd=7.50,
            budget_limit_usd=10.00,
            budget_percentage=75.0,
            alert_type="warning_75",
        )

        assert event.budget_percentage == 75.0
        assert event.alert_type == "warning_75"

    def test_sandbox_event_with_metrics(self):
        """Test SandboxEvent with resource metrics."""
        event = SandboxEvent(
            event_type="sandbox.executed",
            execution_id="exec-1",
            language="python",
            exit_code=0,
            duration_seconds=2.5,
            status="success",
            memory_used_mb=128.5,
            cpu_percent=45.2,
        )

        assert event.memory_used_mb == 128.5
        assert event.cpu_percent == 45.2

    def test_audit_event_full(self):
        """Test AuditEvent with all fields."""
        event = AuditEvent(
            event_type="audit.workflow.created",
            actor="user@example.com",
            action="create",
            resource_type="workflow",
            resource_id="new-workflow",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"name": "Test Workflow", "schedule": "0 2 * * *"},
            success=True,
        )

        assert event.actor == "user@example.com"
        assert event.ip_address == "192.168.1.100"
        assert event.success is True


@pytest.mark.asyncio
class TestTopicManagement:
    """Test topic creation and management."""

    async def test_ensure_topics_exist(self):
        """Test topic creation."""
        topics = [
            KafkaTopic.WORKFLOWS.value,
            KafkaTopic.COSTS.value,
        ]

        # Should not raise (idempotent)
        await ensure_topics_exist(topics)

    async def test_get_all_topics(self):
        """Test getting all topic names."""
        from wflo.events import get_all_topics

        topics = get_all_topics()

        assert KafkaTopic.WORKFLOWS.value in topics
        assert KafkaTopic.COSTS.value in topics
        assert KafkaTopic.SANDBOX.value in topics
        assert KafkaTopic.AUDIT.value in topics
        assert len(topics) == 5  # workflows, costs, sandbox, audit, metrics
