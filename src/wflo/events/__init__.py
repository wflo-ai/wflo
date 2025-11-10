"""Kafka-based event streaming for workflow observability and integration.

This package provides:
- Event schemas for workflows, costs, sandbox, and audit
- Kafka producer for publishing events
- Kafka consumer for subscribing to events
- Topic configuration and management
"""

from wflo.events.consumer import KafkaConsumer, KafkaMessage, subscribe_to_events
from wflo.events.producer import (
    KafkaProducer,
    close_kafka_producer,
    ensure_topics_exist,
    get_kafka_producer,
)
from wflo.events.schemas import (
    AuditEvent,
    BaseEvent,
    CostEvent,
    SandboxEvent,
    WorkflowEvent,
)
from wflo.events.topics import KafkaTopic, get_all_topics, get_topic_config

__all__ = [
    # Producer
    "KafkaProducer",
    "get_kafka_producer",
    "close_kafka_producer",
    "ensure_topics_exist",
    # Consumer
    "KafkaConsumer",
    "KafkaMessage",
    "subscribe_to_events",
    # Schemas
    "BaseEvent",
    "WorkflowEvent",
    "CostEvent",
    "SandboxEvent",
    "AuditEvent",
    # Topics
    "KafkaTopic",
    "get_all_topics",
    "get_topic_config",
]
