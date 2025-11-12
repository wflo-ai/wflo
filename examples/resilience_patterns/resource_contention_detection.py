"""Example: Using ResourceLock to detect and prevent resource contention.

This example demonstrates how to use resource locks to coordinate access to
shared resources and detect contention between concurrent workflows.

Run:
    python examples/resilience_patterns/resource_contention_detection.py
"""

import asyncio
import os
from datetime import datetime

from openai import AsyncOpenAI

from wflo.resilience.contention import (
    ContentionDetectedError,
    ResourceLock,
    detect_contention,
    get_resource_lock,
)
from wflo.sdk.workflow import WfloWorkflow


# Example 1: Basic Resource Lock
async def example_basic_resource_lock():
    """Example showing basic exclusive resource locking."""
    print("\n=== Example 1: Basic Exclusive Resource Lock ===\n")

    # Create exclusive lock (max_concurrent=1)
    lock = ResourceLock(
        name="api-rate-limit",
        max_concurrent=1,  # Only one workflow at a time
        timeout=5.0,
        contention_threshold=1.0,  # Warn if waiting > 1 second
    )

    async def workflow_task(workflow_id: str, work_duration: float):
        """Simulated workflow accessing shared resource."""
        print(f"[{workflow_id}] Waiting for resource...")

        try:
            async with lock.acquire(workflow_id=workflow_id):
                print(f"[{workflow_id}] ✅ Acquired resource, working for {work_duration}s...")
                await asyncio.sleep(work_duration)
                print(f"[{workflow_id}] ✅ Released resource")
                return f"{workflow_id}-success"

        except ContentionDetectedError as e:
            print(f"[{workflow_id}] ⚠️  Contention detected: {e}")
            return f"{workflow_id}-timeout"

    # Run 3 workflows concurrently
    print("Starting 3 concurrent workflows...\n")
    results = await asyncio.gather(
        workflow_task("Workflow-A", 1.0),
        workflow_task("Workflow-B", 0.5),
        workflow_task("Workflow-C", 0.5),
    )

    print(f"\n📊 Results: {results}")
    print(f"📊 Lock Statistics: {lock.get_stats()}")


# Example 2: Concurrent Resource Access
async def example_concurrent_resource_access():
    """Example with resource that allows multiple concurrent accessors."""
    print("\n=== Example 2: Concurrent Resource Access ===\n")

    # Allow up to 3 concurrent accessors
    lock = ResourceLock(
        name="connection-pool",
        max_concurrent=3,  # Up to 3 connections
        timeout=10.0,
        contention_threshold=2.0,
    )

    async def use_connection(worker_id: int):
        """Worker using database connection from pool."""
        print(f"[Worker-{worker_id}] Requesting connection...")

        async with lock.acquire(workflow_id=f"worker-{worker_id}"):
            print(f"[Worker-{worker_id}] ✅ Got connection (active: {len(lock._holders)})")
            await asyncio.sleep(0.5)  # Simulate query
            print(f"[Worker-{worker_id}] ✅ Released connection")

        return worker_id

    # Launch 5 workers (more than pool size)
    print("Launching 5 workers with pool size of 3...\n")
    results = await asyncio.gather(*[use_connection(i) for i in range(5)])

    print(f"\n📊 All workers completed: {results}")
    print(f"📊 Pool Statistics: {lock.get_stats()}")


# Example 3: Detect Contention Decorator
async def example_detect_contention_decorator():
    """Example using @detect_contention decorator."""
    print("\n=== Example 3: @detect_contention Decorator ===\n")

    @detect_contention(
        resource_name="shared-api-quota",
        max_concurrent=2,
        contention_threshold=0.5,
        timeout=3.0,
    )
    async def call_rate_limited_api(request_id: str):
        """API call protected by rate limit."""
        print(f"[{request_id}] Calling API...")
        await asyncio.sleep(1.0)  # Simulate API call
        print(f"[{request_id}] API response received")
        return f"response-{request_id}"

    # Make concurrent API calls
    print("Making 4 concurrent API calls (limit: 2)...\n")

    tasks = [call_rate_limited_api(f"req-{i}") for i in range(4)]
    results = await asyncio.gather(*tasks)

    print(f"\n📊 API Calls completed: {results}")


# Example 4: Contention in Workflow
async def example_workflow_with_contention_detection():
    """Example integrating contention detection with WfloWorkflow."""
    print("\n=== Example 4: Contention Detection in Workflow ===\n")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Shared resource lock for LLM API quota
    api_lock = get_resource_lock(
        name="llm-api-quota",
        max_concurrent=2,  # Limit concurrent API calls
        contention_threshold=1.0,
    )

    async def run_workflow(workflow_id: str, prompt: str):
        """Workflow making LLM API call with quota protection."""
        workflow = WfloWorkflow(
            name=f"workflow-{workflow_id}",
            budget_usd=0.5,
        )

        async def workflow_logic(prompt: str):
            """Protected LLM call."""
            print(f"[{workflow_id}] Starting workflow...")

            try:
                # Acquire API quota
                async with api_lock.acquire(workflow_id=workflow_id, timeout=5.0):
                    print(f"[{workflow_id}] ✅ Got API quota, calling LLM...")

                    response = await client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=30,
                    )

                    result = response.choices[0].message.content
                    print(f"[{workflow_id}] ✅ LLM response: {result[:40]}...")
                    return {"workflow_id": workflow_id, "result": result, "status": "success"}

            except ContentionDetectedError as e:
                print(f"[{workflow_id}] ⚠️  Quota contention: {e}")
                return {"workflow_id": workflow_id, "result": None, "status": "quota_timeout"}

        return await workflow.execute(workflow_logic, {"prompt": prompt})

    # Run 3 workflows concurrently (exceeds quota limit of 2)
    print("Running 3 workflows with API quota limit of 2...\n")

    results = await asyncio.gather(
        run_workflow("A", "What is Python?"),
        run_workflow("B", "What is JavaScript?"),
        run_workflow("C", "What is Rust?"),
    )

    print(f"\n📊 Workflow Results:")
    for result in results:
        print(f"  {result}")

    print(f"\n📊 API Quota Statistics: {api_lock.get_stats()}")


# Example 5: Timeout and Error Handling
async def example_timeout_handling():
    """Example showing timeout when resource is unavailable."""
    print("\n=== Example 5: Timeout Handling ===\n")

    lock = ResourceLock(
        name="exclusive-resource",
        max_concurrent=1,
        timeout=2.0,  # Short timeout
        contention_threshold=0.5,
    )

    async def long_holder():
        """Workflow that holds resource for long time."""
        print("[Holder] Acquiring resource for 5 seconds...")
        async with lock.acquire(workflow_id="holder", timeout=10.0):
            print("[Holder] ✅ Holding resource...")
            await asyncio.sleep(5.0)
            print("[Holder] ✅ Released")

    async def impatient_waiter():
        """Workflow with short timeout."""
        # Give holder time to acquire
        await asyncio.sleep(0.1)

        print("[Waiter] Trying to acquire resource (timeout: 2s)...")
        try:
            async with lock.acquire(workflow_id="waiter", timeout=2.0):
                print("[Waiter] ✅ Got resource")
                await asyncio.sleep(0.1)
        except ContentionDetectedError as e:
            print(f"[Waiter] ⚠️  Timeout! {e}")
            print(f"  Resource holders: {e.holders}")
            print(f"  Wait time: {e.wait_time:.2f}s")

    # Run both
    await asyncio.gather(
        long_holder(),
        impatient_waiter(),
    )


# Example 6: Monitoring Contention Statistics
async def example_contention_statistics():
    """Example showing how to monitor contention statistics."""
    print("\n=== Example 6: Contention Statistics Monitoring ===\n")

    lock = ResourceLock(
        name="monitored-resource",
        max_concurrent=1,
        contention_threshold=0.1,  # Low threshold for demo
    )

    async def worker(worker_id: int, work_time: float):
        """Worker accessing resource."""
        async with lock.acquire(workflow_id=f"worker-{worker_id}"):
            await asyncio.sleep(work_time)
        return worker_id

    # Run multiple workers
    print("Running 5 workers sequentially (will cause contention)...\n")
    await asyncio.gather(*[worker(i, 0.2) for i in range(5)])

    # Get detailed statistics
    stats = lock.get_stats()

    print("\n📊 Contention Statistics:")
    print(f"  Resource: {stats['resource_name']}")
    print(f"  Total acquisitions: {stats['total_acquisitions']}")
    print(f"  Contention events: {stats['contention_count']}")
    print(f"  Contention rate: {stats['contention_rate']:.1%}")
    print(f"  Avg wait time: {stats['avg_wait_time_seconds']:.3f}s")
    print(f"  Max wait time: {stats['max_wait_time_seconds']:.3f}s")
    print(f"  Current holders: {stats['current_holders']}")

    # Reset statistics
    lock.reset_stats()
    print("\n✅ Statistics reset for next monitoring period")


# Example 7: Database Connection Pool Pattern
async def example_database_connection_pool():
    """Real-world example: Database connection pool management."""
    print("\n=== Example 7: Database Connection Pool Pattern ===\n")

    # Simulate connection pool with 3 connections
    db_pool = ResourceLock(
        name="postgres-connection-pool",
        max_concurrent=3,
        timeout=5.0,
        contention_threshold=2.0,
    )

    async def execute_query(query_id: int, query: str):
        """Execute database query using connection from pool."""
        print(f"[Query-{query_id}] Waiting for DB connection...")

        try:
            async with db_pool.acquire(workflow_id=f"query-{query_id}", timeout=3.0):
                print(f"[Query-{query_id}] ✅ Executing: {query[:30]}...")
                await asyncio.sleep(0.5)  # Simulate query execution
                print(f"[Query-{query_id}] ✅ Query completed")
                return {"query_id": query_id, "status": "success"}

        except ContentionDetectedError as e:
            print(f"[Query-{query_id}] ⚠️  Pool exhausted: {e}")
            return {"query_id": query_id, "status": "pool_timeout"}

    # Simulate 6 concurrent queries (exceeds pool size of 3)
    print("Executing 6 concurrent queries with pool size of 3...\n")

    queries = [
        "SELECT * FROM users WHERE id = 1",
        "SELECT * FROM orders WHERE user_id = 1",
        "SELECT * FROM products WHERE category = 'electronics'",
        "SELECT COUNT(*) FROM sessions",
        "SELECT * FROM logs WHERE timestamp > NOW() - INTERVAL '1 hour'",
        "SELECT AVG(rating) FROM reviews",
    ]

    results = await asyncio.gather(*[execute_query(i, q) for i, q in enumerate(queries)])

    print(f"\n📊 Query Results:")
    for result in results:
        print(f"  Query {result['query_id']}: {result['status']}")

    stats = db_pool.get_stats()
    print(f"\n📊 Connection Pool Statistics:")
    print(f"  Total queries: {stats['total_acquisitions']}")
    print(f"  Pool contentions: {stats['contention_count']}")
    print(f"  Contention rate: {stats['contention_rate']:.1%}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("Resource Contention Detection Examples")
    print("=" * 70)

    # Run examples that don't need API key
    await example_basic_resource_lock()
    await example_concurrent_resource_access()
    await example_detect_contention_decorator()
    await example_timeout_handling()
    await example_contention_statistics()
    await example_database_connection_pool()

    # Run example with API if available
    if os.getenv("OPENAI_API_KEY"):
        await example_workflow_with_contention_detection()
    else:
        print("\n⚠️  Skipping workflow example (OPENAI_API_KEY not set)")

    print("\n" + "=" * 70)
    print("✅ All resource contention examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
