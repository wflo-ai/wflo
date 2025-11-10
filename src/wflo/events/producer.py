"""Kafka producer for publishing events asynchronously."""

import asyncio
import json
from typing import Any

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pydantic import BaseModel

from wflo.config import get_settings
from wflo.observability import get_logger
from wflo.observability.metrics import kafka_messages_produced_total

logger = get_logger(__name__)


class KafkaProducer:
    """Async Kafka producer with idempotent delivery and automatic serialization.

    Features:
    - Idempotent producer (exactly-once semantics)
    - Automatic JSON serialization from Pydantic models
    - Error handling and retries
    - Partitioning by key for message ordering
    - Compression for efficiency

    Example:
        >>> from wflo.events import KafkaProducer, WorkflowEvent
        >>>
        >>> async with KafkaProducer() as producer:
        ...     event = WorkflowEvent(
        ...         event_type="workflow.started",
        ...         workflow_id="data-pipeline",
        ...         execution_id="exec-123",
        ...         status="running",
        ...     )
        ...     await producer.send("wflo.workflows", event, key="data-pipeline")
    """

    def __init__(self):
        """Initialize Kafka producer with settings."""
        settings = get_settings()

        # Producer configuration
        # https://docs.confluent.io/platform/current/installation/configuration/producer-configs.html
        self.config = {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": settings.kafka_client_id,
            # Idempotence (exactly-once semantics)
            "enable.idempotence": True,
            # Compression
            "compression.type": "snappy",
            # Batching for throughput
            "linger.ms": 10,
            "batch.size": 16384,
            # Retries
            "retries": 3,
            "retry.backoff.ms": 100,
            # Delivery timeout
            "delivery.timeout.ms": 120000,
        }

        self.producer: Producer | None = None
        self._flush_task: asyncio.Task | None = None

    async def __aenter__(self) -> "KafkaProducer":
        """Context manager entry - connect to Kafka."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connection and flush."""
        await self.close()

    async def connect(self) -> None:
        """Connect to Kafka cluster."""
        try:
            self.producer = Producer(self.config)

            logger.info(
                "kafka_producer_connected",
                bootstrap_servers=self.config["bootstrap.servers"],
            )

            # Start background flush task
            self._flush_task = asyncio.create_task(self._flush_periodically())

        except Exception as e:
            logger.error(
                "kafka_producer_connection_failed",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    async def close(self) -> None:
        """Close Kafka producer and flush pending messages."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        if self.producer:
            # Flush pending messages
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.producer.flush(timeout=10),
            )

            logger.info("kafka_producer_closed")

    async def send(
        self,
        topic: str,
        event: BaseModel,
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Send an event to a Kafka topic.

        Args:
            topic: Kafka topic name
            event: Event to send (Pydantic model)
            key: Partition key for ordering (optional)
            headers: Message headers (optional)

        Raises:
            RuntimeError: If producer not connected
            Exception: If send fails after retries

        Example:
            >>> event = WorkflowEvent(...)
            >>> await producer.send("wflo.workflows", event, key=workflow_id)
        """
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")

        try:
            # Serialize event to JSON
            value = self._serialize(event)

            # Convert key to bytes
            key_bytes = key.encode("utf-8") if key else None

            # Convert headers to list of tuples
            headers_list = None
            if headers:
                headers_list = [(k, v.encode("utf-8")) for k, v in headers.items()]

            # Send to Kafka (non-blocking with callback)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.producer.produce(
                    topic=topic,
                    value=value,
                    key=key_bytes,
                    headers=headers_list,
                    on_delivery=self._delivery_callback,
                ),
            )

            # Track metric
            kafka_messages_produced_total.labels(topic=topic, status="success").inc()

            logger.debug(
                "kafka_message_sent",
                topic=topic,
                event_type=event.event_type,
                key=key,
            )

        except Exception as e:
            # Track error metric
            kafka_messages_produced_total.labels(topic=topic, status="error").inc()

            logger.error(
                "kafka_send_failed",
                topic=topic,
                event_type=event.event_type,
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    def _serialize(self, event: BaseModel) -> bytes:
        """Serialize Pydantic model to JSON bytes.

        Args:
            event: Pydantic model to serialize

        Returns:
            JSON bytes
        """
        return event.model_dump_json().encode("utf-8")

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        """Callback for message delivery confirmation.

        Args:
            err: Error if delivery failed
            msg: Message metadata
        """
        if err:
            logger.error(
                "kafka_delivery_failed",
                topic=msg.topic(),
                partition=msg.partition(),
                error=str(err),
            )
        else:
            logger.debug(
                "kafka_delivery_confirmed",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
            )

    async def _flush_periodically(self) -> None:
        """Background task to flush producer periodically."""
        while True:
            try:
                await asyncio.sleep(5)  # Flush every 5 seconds

                if self.producer:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.producer.poll(0),
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "kafka_flush_error",
                    error_type=type(e).__name__,
                    error=str(e),
                )


async def ensure_topics_exist(topics: list[str]) -> None:
    """Ensure Kafka topics exist, create if missing.

    Args:
        topics: List of topic names to ensure exist

    Example:
        >>> await ensure_topics_exist([
        ...     "wflo.workflows",
        ...     "wflo.costs",
        ...     "wflo.sandbox",
        ... ])
    """
    settings = get_settings()

    admin_client = AdminClient({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
    })

    # Get existing topics
    metadata = admin_client.list_topics(timeout=10)
    existing_topics = set(metadata.topics.keys())

    # Find missing topics
    missing_topics = [t for t in topics if t not in existing_topics]

    if not missing_topics:
        logger.debug("kafka_topics_exist", topics=topics)
        return

    # Create missing topics
    new_topics = [
        NewTopic(
            topic,
            num_partitions=3,  # 3 partitions for parallelism
            replication_factor=1,  # 1 replica for development
        )
        for topic in missing_topics
    ]

    # Create topics
    futures = admin_client.create_topics(new_topics)

    # Wait for creation
    for topic, future in futures.items():
        try:
            future.result()  # Wait for operation to complete
            logger.info("kafka_topic_created", topic=topic)
        except Exception as e:
            logger.error(
                "kafka_topic_creation_failed",
                topic=topic,
                error_type=type(e).__name__,
                error=str(e),
            )


# Global producer instance (singleton)
_producer: KafkaProducer | None = None


async def get_kafka_producer() -> KafkaProducer:
    """Get or create the global Kafka producer instance.

    Returns:
        KafkaProducer instance

    Example:
        >>> producer = await get_kafka_producer()
        >>> await producer.send("wflo.workflows", event)
    """
    global _producer

    if _producer is None:
        _producer = KafkaProducer()
        await _producer.connect()

    return _producer


async def close_kafka_producer() -> None:
    """Close the global Kafka producer.

    Call this during application shutdown.

    Example:
        >>> await close_kafka_producer()
    """
    global _producer

    if _producer is not None:
        await _producer.close()
        _producer = None
