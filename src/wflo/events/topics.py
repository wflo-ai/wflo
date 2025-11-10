"""Kafka topic definitions and configuration."""

from enum import Enum


class KafkaTopic(str, Enum):
    """Kafka topic names for Wflo events.

    Using an enum ensures type safety and prevents typos.
    """

    # Workflow lifecycle events
    WORKFLOWS = "wflo.workflows"

    # Cost tracking and budget alerts
    COSTS = "wflo.costs"

    # Sandbox code execution events
    SANDBOX = "wflo.sandbox"

    # Audit trail for compliance
    AUDIT = "wflo.audit"

    # Real-time metrics stream
    METRICS = "wflo.metrics"


# Topic configuration
# https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html
TOPIC_CONFIGS = {
    KafkaTopic.WORKFLOWS: {
        "partitions": 3,
        "replication_factor": 1,  # 1 for dev, 3 for prod
        "config": {
            "retention.ms": 604800000,  # 7 days
            "compression.type": "snappy",
            "cleanup.policy": "delete",
        },
    },
    KafkaTopic.COSTS: {
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": 2592000000,  # 30 days (cost history)
            "compression.type": "snappy",
            "cleanup.policy": "delete",
        },
    },
    KafkaTopic.SANDBOX: {
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": 604800000,  # 7 days
            "compression.type": "snappy",
            "cleanup.policy": "delete",
        },
    },
    KafkaTopic.AUDIT: {
        "partitions": 3,
        "replication_factor": 1,  # 3 for prod (critical data)
        "config": {
            "retention.ms": 7776000000,  # 90 days (compliance)
            "compression.type": "snappy",
            "cleanup.policy": "delete",
            # Require stronger durability for audit logs
            "min.insync.replicas": 1,  # 2 for prod
        },
    },
    KafkaTopic.METRICS: {
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": 86400000,  # 1 day (short-lived)
            "compression.type": "snappy",
            "cleanup.policy": "delete",
        },
    },
}


def get_all_topics() -> list[str]:
    """Get list of all topic names.

    Returns:
        List of topic name strings

    Example:
        >>> topics = get_all_topics()
        >>> print(topics)
        ['wflo.workflows', 'wflo.costs', 'wflo.sandbox', 'wflo.audit', 'wflo.metrics']
    """
    return [topic.value for topic in KafkaTopic]


def get_topic_config(topic: KafkaTopic) -> dict:
    """Get configuration for a specific topic.

    Args:
        topic: Topic enum value

    Returns:
        Topic configuration dict

    Example:
        >>> config = get_topic_config(KafkaTopic.WORKFLOWS)
        >>> print(config['partitions'])
        3
    """
    return TOPIC_CONFIGS.get(topic, {})
