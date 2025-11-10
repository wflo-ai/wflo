"""Kafka consumer for subscribing to events asynchronously."""

import asyncio
import json
from typing import Any, AsyncIterator

from confluent_kafka import Consumer, KafkaError, KafkaException, Message
from pydantic import BaseModel, ValidationError

from wflo.config import get_settings
from wflo.observability import get_logger
from wflo.observability.metrics import kafka_consumer_lag, kafka_messages_consumed_total

logger = get_logger(__name__)


class KafkaMessage:
    """Wrapper for Kafka messages with deserialized value.

    Attributes:
        topic: Topic name
        partition: Partition number
        offset: Message offset
        key: Message key (optional)
        value: Deserialized message value (dict)
        headers: Message headers (optional)
        timestamp: Message timestamp
    """

    def __init__(self, msg: Message):
        """Initialize from confluent_kafka Message.

        Args:
            msg: Raw Kafka message
        """
        self.topic = msg.topic()
        self.partition = msg.partition()
        self.offset = msg.offset()
        self.key = msg.key().decode("utf-8") if msg.key() else None
        self.timestamp = msg.timestamp()[1] if msg.timestamp()[0] == 1 else None

        # Deserialize value
        if msg.value():
            self.value = json.loads(msg.value().decode("utf-8"))
        else:
            self.value = None

        # Deserialize headers
        self.headers = {}
        if msg.headers():
            for key, value in msg.headers():
                self.headers[key] = value.decode("utf-8") if value else None


class KafkaConsumer:
    """Async Kafka consumer with background polling and deserialization.

    Features:
    - Async iteration over messages
    - Automatic offset management
    - Consumer group coordination
    - Deserialization from JSON
    - Error handling and retries
    - Graceful shutdown

    Example:
        >>> from wflo.events import KafkaConsumer, WorkflowEvent
        >>>
        >>> async with KafkaConsumer(
        ...     topics=["wflo.workflows"],
        ...     group_id="wflo-monitor",
        ... ) as consumer:
        ...     async for message in consumer:
        ...         event = WorkflowEvent(**message.value)
        ...         await process_event(event)
    """

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
    ):
        """Initialize Kafka consumer.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            auto_offset_reset: Where to start reading (earliest, latest)
            enable_auto_commit: Automatically commit offsets
        """
        settings = get_settings()

        self.topics = topics
        self.group_id = group_id

        # Consumer configuration
        # https://docs.confluent.io/platform/current/installation/configuration/consumer-configs.html
        self.config = {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group_id,
            "client.id": f"{settings.kafka_client_id}-consumer",
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": enable_auto_commit,
            # Offset commit interval
            "auto.commit.interval.ms": 5000,
            # Session timeout
            "session.timeout.ms": 30000,
            # Max poll interval
            "max.poll.interval.ms": 300000,
            # Fetch config
            "fetch.min.bytes": 1024,
            "fetch.max.wait.ms": 500,
        }

        self.consumer: Consumer | None = None
        self._message_queue: asyncio.Queue[KafkaMessage | None] = asyncio.Queue()
        self._poll_task: asyncio.Task | None = None
        self._running = False

    async def __aenter__(self) -> "KafkaConsumer":
        """Context manager entry - connect and start consuming."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stop consuming and close."""
        await self.stop()

    async def start(self) -> None:
        """Start consuming messages from Kafka."""
        try:
            self.consumer = Consumer(self.config)
            self.consumer.subscribe(self.topics)

            self._running = True

            # Start background polling task
            self._poll_task = asyncio.create_task(self._poll_loop())

            logger.info(
                "kafka_consumer_started",
                topics=self.topics,
                group_id=self.group_id,
            )

        except Exception as e:
            logger.error(
                "kafka_consumer_start_failed",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    async def stop(self) -> None:
        """Stop consuming and close consumer."""
        self._running = False

        # Signal stop to message queue
        await self._message_queue.put(None)

        # Cancel polling task
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        # Close consumer
        if self.consumer:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consumer.close,
            )

            logger.info("kafka_consumer_stopped")

    async def _poll_loop(self) -> None:
        """Background task to poll Kafka for messages."""
        while self._running:
            try:
                # Poll for messages (non-blocking in executor)
                msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.consumer.poll(timeout=1.0),
                )

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition - not an error
                        logger.debug(
                            "kafka_partition_eof",
                            topic=msg.topic(),
                            partition=msg.partition(),
                        )
                        continue
                    else:
                        logger.error(
                            "kafka_consumer_error",
                            error_code=msg.error().code(),
                            error=str(msg.error()),
                        )
                        continue

                # Wrap message
                kafka_msg = KafkaMessage(msg)

                # Track metrics
                kafka_messages_consumed_total.labels(
                    topic=kafka_msg.topic,
                    consumer_group=self.group_id,
                ).inc()

                # Update lag metric (high watermark - current offset)
                _, high_watermark = self.consumer.get_watermark_offsets(
                    msg.topic(),
                    msg.partition(),
                )
                lag = high_watermark - msg.offset() - 1
                kafka_consumer_lag.labels(
                    topic=msg.topic(),
                    consumer_group=self.group_id,
                    partition=str(msg.partition()),
                ).set(max(0, lag))

                # Add to async queue
                await self._message_queue.put(kafka_msg)

                logger.debug(
                    "kafka_message_received",
                    topic=kafka_msg.topic,
                    partition=kafka_msg.partition,
                    offset=kafka_msg.offset,
                    key=kafka_msg.key,
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "kafka_poll_error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
                # Brief sleep on error to avoid tight loop
                await asyncio.sleep(1)

    async def __aiter__(self) -> AsyncIterator[KafkaMessage]:
        """Async iterator over consumed messages.

        Yields:
            KafkaMessage instances

        Example:
            >>> async for message in consumer:
            ...     print(message.value)
        """
        while True:
            message = await self._message_queue.get()

            # None signals stop
            if message is None:
                break

            yield message

    async def commit(self) -> None:
        """Manually commit current offsets.

        Use this when enable_auto_commit=False.

        Example:
            >>> async for message in consumer:
            ...     await process_message(message)
            ...     await consumer.commit()
        """
        if self.consumer:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consumer.commit,
            )

            logger.debug("kafka_offsets_committed", group_id=self.group_id)


async def subscribe_to_events(
    topics: list[str],
    handler: callable,
    group_id: str,
    event_model: type[BaseModel] | None = None,
) -> None:
    """Subscribe to Kafka topics and process events with a handler.

    Convenience function for event processing with automatic deserialization.

    Args:
        topics: List of topics to subscribe to
        handler: Async function to handle events (takes event dict or model)
        group_id: Consumer group ID
        event_model: Optional Pydantic model to deserialize into

    Example:
        >>> from wflo.events import subscribe_to_events, WorkflowEvent
        >>>
        >>> async def handle_workflow_event(event: WorkflowEvent):
        ...     print(f"Workflow {event.workflow_id} status: {event.status}")
        >>>
        >>> await subscribe_to_events(
        ...     topics=["wflo.workflows"],
        ...     handler=handle_workflow_event,
        ...     group_id="workflow-monitor",
        ...     event_model=WorkflowEvent,
        ... )
    """
    async with KafkaConsumer(topics=topics, group_id=group_id) as consumer:
        async for message in consumer:
            try:
                # Deserialize to event model if provided
                if event_model:
                    event = event_model(**message.value)
                    await handler(event)
                else:
                    await handler(message.value)

            except ValidationError as e:
                logger.error(
                    "event_validation_failed",
                    topic=message.topic,
                    error=str(e),
                    value=message.value,
                )
            except Exception as e:
                logger.error(
                    "event_handler_error",
                    topic=message.topic,
                    handler=handler.__name__,
                    error_type=type(e).__name__,
                    error=str(e),
                )
