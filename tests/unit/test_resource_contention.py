"""Unit tests for resource contention detection."""

import asyncio
import pytest

from wflo.resilience.contention import (
    ResourceLock,
    ContentionDetectedError,
    get_resource_lock,
    detect_contention,
)


class TestResourceLock:
    """Test ResourceLock class."""

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        """Test basic lock acquisition and release."""
        lock = ResourceLock(name="test-lock")

        async with lock.acquire(workflow_id="workflow-1"):
            # Lock is held
            assert "workflow-1" in lock._holders

        # Lock is released
        assert "workflow-1" not in lock._holders

    @pytest.mark.asyncio
    async def test_exclusive_lock_blocks_concurrent_access(self):
        """Test exclusive lock (max_concurrent=1) blocks concurrent access."""
        lock = ResourceLock(
            name="test-lock",
            max_concurrent=1,  # Exclusive
        )

        acquired_order = []

        async def worker(workflow_id: str):
            async with lock.acquire(workflow_id=workflow_id):
                acquired_order.append(workflow_id)
                await asyncio.sleep(0.05)  # Hold lock briefly

        # Start two workers concurrently
        await asyncio.gather(
            worker("workflow-1"),
            worker("workflow-2"),
        )

        # Both should complete but sequentially
        assert len(acquired_order) == 2
        assert acquired_order[0] != acquired_order[1]

    @pytest.mark.asyncio
    async def test_concurrent_lock_allows_multiple_holders(self):
        """Test concurrent lock allows multiple holders."""
        lock = ResourceLock(
            name="test-lock",
            max_concurrent=3,  # Allow 3 concurrent holders
        )

        holder_counts = []

        async def worker(workflow_id: str):
            async with lock.acquire(workflow_id=workflow_id):
                # Record number of concurrent holders
                holder_counts.append(len(lock._holders))
                await asyncio.sleep(0.05)

        # Start 5 workers
        await asyncio.gather(*[
            worker(f"workflow-{i}") for i in range(5)
        ])

        # Max holders should not exceed 3
        assert max(holder_counts) <= 3

    @pytest.mark.asyncio
    async def test_timeout_raises_contention_error(self):
        """Test timeout raises ContentionDetectedError."""
        lock = ResourceLock(
            name="test-lock",
            timeout=10.0,  # Default timeout (long)
        )

        holder_started = asyncio.Event()

        async def holder():
            # Holder gets longer timeout
            async with lock.acquire(workflow_id="holder", timeout=5.0):
                holder_started.set()  # Signal that holder has the lock
                await asyncio.sleep(1.0)  # Hold for long time (longer than waiter timeout)

        async def waiter():
            # Wait until holder has lock
            await holder_started.wait()
            # Waiter gets short timeout and should fail
            async with lock.acquire(workflow_id="waiter", timeout=0.1):
                pass

        # Start holder first
        holder_task = asyncio.create_task(holder())

        # Waiter should timeout
        with pytest.raises(ContentionDetectedError) as exc_info:
            await waiter()

        error = exc_info.value
        assert error.resource_name == "test-lock"
        assert error.wait_time >= 0.1
        assert "holder" in error.holders

        # Cancel holder task to clean up
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_contention_detection_threshold(self):
        """Test contention is detected when wait time exceeds threshold."""
        lock = ResourceLock(
            name="test-lock",
            contention_threshold=0.05,  # 50ms threshold
        )

        async def holder():
            async with lock.acquire(workflow_id="holder"):
                await asyncio.sleep(0.1)  # Hold for 100ms

        async def waiter():
            async with lock.acquire(workflow_id="waiter"):
                pass

        # Start holder
        holder_task = asyncio.create_task(holder())
        await asyncio.sleep(0.01)

        # Waiter will wait > threshold
        await waiter()
        await holder_task

        # Check contention was detected
        stats = lock.get_stats()
        assert stats["contention_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_stats_accuracy(self):
        """Test statistics are accurately tracked."""
        lock = ResourceLock(
            name="test-lock",
            contention_threshold=0.02,
        )

        async def quick_worker(workflow_id: str):
            async with lock.acquire(workflow_id=workflow_id):
                await asyncio.sleep(0.01)

        # Run some workers
        for i in range(5):
            await quick_worker(f"workflow-{i}")

        stats = lock.get_stats()

        assert stats["resource_name"] == "test-lock"
        assert stats["total_acquisitions"] == 5
        assert stats["current_holders"] == []  # All released
        assert stats["avg_wait_time_seconds"] >= 0.0

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test statistics can be reset."""
        lock = ResourceLock(name="test-lock")

        async with lock.acquire(workflow_id="test"):
            pass

        assert lock.get_stats()["total_acquisitions"] == 1

        lock.reset_stats()

        assert lock.get_stats()["total_acquisitions"] == 0
        assert lock.get_stats()["contention_count"] == 0

    @pytest.mark.asyncio
    async def test_custom_timeout_override(self):
        """Test custom timeout overrides default."""
        lock = ResourceLock(
            name="test-lock",
            timeout=10.0,  # Default timeout
        )

        async def holder():
            async with lock.acquire(workflow_id="holder"):
                await asyncio.sleep(0.5)

        async def waiter():
            # Override with shorter timeout
            async with lock.acquire(workflow_id="waiter", timeout=0.05):
                pass

        holder_task = asyncio.create_task(holder())
        await asyncio.sleep(0.01)

        # Should timeout with custom 0.05s timeout, not 10s
        with pytest.raises(ContentionDetectedError):
            await waiter()

        await holder_task

    @pytest.mark.asyncio
    async def test_lock_released_on_exception(self):
        """Test lock is released even if exception occurs."""
        lock = ResourceLock(name="test-lock")

        try:
            async with lock.acquire(workflow_id="test"):
                assert "test" in lock._holders
                raise ValueError("Test error")
        except ValueError:
            pass

        # Lock should be released despite exception
        assert "test" not in lock._holders


class TestResourceLockRegistry:
    """Test global resource lock registry."""

    @pytest.mark.asyncio
    async def test_get_resource_lock_creates_new(self):
        """Test get_resource_lock creates new lock."""
        lock = get_resource_lock(
            name="new-lock",
            timeout=20.0,
        )

        assert lock.name == "new-lock"
        assert lock.timeout == 20.0

    @pytest.mark.asyncio
    async def test_get_resource_lock_returns_existing(self):
        """Test get_resource_lock returns existing lock."""
        lock1 = get_resource_lock(name="shared-lock", timeout=10.0)
        lock2 = get_resource_lock(name="shared-lock", timeout=30.0)

        # Should return same instance
        assert lock1 is lock2
        # First config wins
        assert lock1.timeout == 10.0


class TestDetectContentionDecorator:
    """Test @detect_contention decorator."""

    @pytest.mark.asyncio
    async def test_decorator_protects_resource(self):
        """Test decorator protects resource with lock."""
        from wflo.sdk.context import ExecutionContext

        call_order = []

        @detect_contention(
            resource_name="test-resource",
            max_concurrent=1,
        )
        async def protected_function(value: str):
            call_order.append(f"{value}-start")
            await asyncio.sleep(0.05)
            call_order.append(f"{value}-end")
            return value

        # Execute two calls concurrently
        async with ExecutionContext(execution_id="exec-1"):
            task1 = asyncio.create_task(protected_function("A"))

        async with ExecutionContext(execution_id="exec-2"):
            task2 = asyncio.create_task(protected_function("B"))

        results = await asyncio.gather(task1, task2)

        # Both should complete
        assert set(results) == {"A", "B"}

        # But they should not overlap (exclusive lock)
        # Either A-start, A-end, B-start, B-end
        # Or B-start, B-end, A-start, A-end
        assert len(call_order) == 4

    @pytest.mark.asyncio
    async def test_decorator_detects_contention(self):
        """Test decorator detects high wait times."""
        from wflo.sdk.context import ExecutionContext

        @detect_contention(
            resource_name="contended-resource",
            contention_threshold=0.02,
            max_concurrent=1,
        )
        async def slow_function():
            await asyncio.sleep(0.05)
            return "done"

        # First call
        async with ExecutionContext(execution_id="exec-1"):
            task1 = asyncio.create_task(slow_function())

        await asyncio.sleep(0.01)  # Let first acquire lock

        # Second call will wait
        async with ExecutionContext(execution_id="exec-2"):
            task2 = asyncio.create_task(slow_function())

        await asyncio.gather(task1, task2)

        # Check contention was logged
        lock = get_resource_lock("contended-resource")
        stats = lock.get_stats()
        assert stats["total_acquisitions"] == 2

    @pytest.mark.asyncio
    async def test_decorator_with_concurrent_access(self):
        """Test decorator allows configured concurrent access."""

        @detect_contention(
            resource_name="concurrent-resource",
            max_concurrent=3,
        )
        async def concurrent_function():
            await asyncio.sleep(0.05)
            return "done"

        from wflo.sdk.context import ExecutionContext

        # Run 5 workers
        tasks = []
        for i in range(5):
            async with ExecutionContext(execution_id=f"exec-{i}"):
                tasks.append(asyncio.create_task(concurrent_function()))

        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(r == "done" for r in results)
