"""Temporal worker configuration and startup.

The worker is responsible for polling Temporal for work and executing
workflows and activities.
"""

import asyncio
import signal
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker

from wflo.config.settings import Settings, get_settings
from wflo.db.engine import init_db
from wflo.temporal.activities import (
    check_budget,
    create_state_snapshot,
    execute_code_in_sandbox,
    save_step_execution,
    save_workflow_execution,
    track_cost,
    update_step_execution,
    update_workflow_execution_status,
)
from wflo.temporal.workflows import (
    CodeExecutionWorkflow,
    SimpleWorkflow,
    WfloWorkflow,
)


async def create_worker(
    client: Client,
    task_queue: str = "wflo-task-queue",
    settings: Settings | None = None,
) -> Worker:
    """Create a Temporal worker.

    Args:
        client: Temporal client
        task_queue: Task queue name
        settings: Application settings (optional)

    Returns:
        Worker: Configured Temporal worker
    """
    if settings is None:
        settings = get_settings()

    # Initialize database
    init_db(settings)

    # Create worker with workflows and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            WfloWorkflow,
            SimpleWorkflow,
            CodeExecutionWorkflow,
        ],
        activities=[
            save_workflow_execution,
            update_workflow_execution_status,
            save_step_execution,
            update_step_execution,
            create_state_snapshot,
            track_cost,
            execute_code_in_sandbox,
            check_budget,
        ],
        max_concurrent_activities=10,
        max_concurrent_workflow_tasks=10,
    )

    return worker


async def run_worker(
    temporal_address: str = "localhost:7233",
    task_queue: str = "wflo-task-queue",
    namespace: str = "default",
) -> None:
    """Run the Temporal worker.

    Args:
        temporal_address: Temporal server address
        task_queue: Task queue name
        namespace: Temporal namespace
    """
    print(f"🚀 Starting Wflo Temporal worker...")
    print(f"   Temporal: {temporal_address}")
    print(f"   Task Queue: {task_queue}")
    print(f"   Namespace: {namespace}")

    # Connect to Temporal
    client = await Client.connect(
        temporal_address,
        namespace=namespace,
    )

    # Create worker
    worker = await create_worker(
        client=client,
        task_queue=task_queue,
    )

    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig: Any, frame: Any) -> None:
        print(f"\n⚠️  Received signal {sig}, shutting down worker...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ Worker started successfully!")
    print("   Press Ctrl+C to stop")
    print()

    # Run worker until shutdown signal
    try:
        async with worker:
            await shutdown_event.wait()
    finally:
        print("👋 Worker stopped")


async def start_worker_from_settings() -> None:
    """Start worker using settings from environment.

    This is the main entry point for starting a worker.
    """
    settings = get_settings()

    await run_worker(
        temporal_address=settings.temporal_address,
        task_queue=settings.temporal_task_queue,
        namespace=settings.temporal_namespace,
    )


def main() -> None:
    """Main entry point for the worker CLI."""
    try:
        asyncio.run(start_worker_from_settings())
    except KeyboardInterrupt:
        print("\n👋 Worker interrupted")
    except Exception as e:
        print(f"❌ Worker failed: {e}")
        raise


if __name__ == "__main__":
    main()
