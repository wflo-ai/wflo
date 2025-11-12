"""Integration tests for Phase 2 resilience patterns.

These tests verify that retry manager, circuit breaker, and resource contention
detection work correctly with real workflow execution.

NOTE: These tests mock database operations to avoid requiring a live database.
They demonstrate resilience patterns integrated with WfloWorkflow API, simulating
real failure scenarios.

Requirements:
- DATABASE_URL in .env (can be any valid URL, mocked in tests)

Setup:
1. Configure .env file with:
   DATABASE_URL=postgresql+asyncpg://localhost/test

2. Run tests:
   poetry run pytest tests/integration/test_resilience_patterns.py -v -m integration

These tests simulate real failure scenarios:
- Network timeouts and transient API errors
- Circuit breaker preventing cascading failures
- Resource contention between concurrent workflows
- Combined patterns working together
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from wflo.config import get_settings
from wflo.db.engine import init_db
from wflo.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    circuit_breaker,
)
from wflo.resilience.contention import (
    ContentionDetectedError,
    ResourceLock,
    detect_contention,
    get_resource_lock,
)
from wflo.resilience.retry import (
    RetryExhaustedError,
    RetryManager,
    RetryStrategy,
    retry_with_backoff,
)
from wflo.sdk.context import ExecutionContext
from wflo.sdk.workflow import WfloWorkflow


# Load settings
_settings = get_settings()


@pytest.fixture(scope="function")
async def setup_database():
    """Setup for tests - database operations are mocked in individual tests."""
    # Note: Database operations are mocked in each test to avoid requiring
    # a live database connection. This fixture is kept for consistency.
    yield
    # Cleanup handled by individual tests


@pytest.mark.integration
@pytest.mark.asyncio
class TestRetryManagerIntegration:
    """Integration tests for RetryManager with workflow execution."""

    async def test_workflow_with_transient_failures(self, setup_database):
        """Test workflow execution with transient failures that recover."""
        workflow = WfloWorkflow(name="retry-test", budget_usd=10.0)

        # Simulate API that fails twice then succeeds
        call_count = {"count": 0}

        async def flaky_api_call():
            call_count["count"] += 1
            if call_count["count"] <= 2:
                raise ConnectionError(f"Temporary network error (attempt {call_count['count']})")
            return {"result": "success", "attempts": call_count["count"]}

        # Wrap with retry manager
        retry_manager = RetryManager(
            max_retries=3,
            base_delay=0.1,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,
        )

        # Execute workflow with retry protection
        async def workflow_logic():
            result = await retry_manager.execute(
                flaky_api_call,
                retryable_exceptions=(ConnectionError,),
            )
            return result

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            result = await workflow.execute(workflow_logic, {})

        # Verify it retried and eventually succeeded
        assert result["result"] == "success"
        assert result["attempts"] == 3  # Failed twice, succeeded on third
        assert call_count["count"] == 3

    async def test_workflow_fails_after_max_retries(self, setup_database):
        """Test workflow fails gracefully after exhausting retries."""
        workflow = WfloWorkflow(name="retry-exhausted-test", budget_usd=10.0)

        async def always_failing_api():
            raise TimeoutError("API timeout")

        retry_manager = RetryManager(
            max_retries=2,
            base_delay=0.05,
            strategy=RetryStrategy.FIXED,
        )

        async def workflow_logic():
            return await retry_manager.execute(
                always_failing_api,
                retryable_exceptions=(TimeoutError,),
            )

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            # Should raise RetryExhaustedError
            with pytest.raises(RetryExhaustedError) as exc_info:
                await workflow.execute(workflow_logic, {})

            error = exc_info.value
            assert error.attempts == 3  # Initial + 2 retries
            assert isinstance(error.last_exception, TimeoutError)

    async def test_retry_decorator_in_workflow(self, setup_database):
        """Test @retry_with_backoff decorator in workflow context."""
        workflow = WfloWorkflow(name="decorator-test", budget_usd=10.0)

        attempts = []

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.05,
            retryable_exceptions=(ValueError,),
        )
        async def decorated_function(value: str):
            attempts.append(len(attempts) + 1)
            if len(attempts) < 2:
                raise ValueError(f"Temporary error on attempt {len(attempts)}")
            return f"processed: {value}"

        async def workflow_logic(input_value: str):
            return await decorated_function(input_value)

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            result = await workflow.execute(workflow_logic, {"input_value": "test-data"})

        assert result == "processed: test-data"
        assert len(attempts) == 2  # Failed once, succeeded on retry


@pytest.mark.integration
@pytest.mark.asyncio
class TestCircuitBreakerIntegration:
    """Integration tests for CircuitBreaker with workflow execution."""

    async def test_circuit_breaker_protects_failing_service(self, setup_database):
        """Test circuit breaker opens after failures and prevents cascading failures."""
        workflow = WfloWorkflow(name="circuit-breaker-test", budget_usd=10.0)

        # Simulate failing external service
        call_count = {"count": 0}

        async def failing_external_service():
            call_count["count"] += 1
            raise ConnectionError(f"Service unavailable (call {call_count['count']})")

        # Create circuit breaker
        breaker = CircuitBreaker(
            name="external-service",
            failure_threshold=3,
            recovery_timeout=1.0,
            expected_exception=(ConnectionError,),
        )

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            # Execute workflow multiple times to trigger circuit breaker
            # First 3 calls should fail with ConnectionError
            for i in range(3):
                async def workflow_logic():
                    return await breaker.call(failing_external_service)

                with pytest.raises(ConnectionError):
                    await workflow.execute(workflow_logic, {})

            # Verify circuit is now OPEN
            assert breaker.state == CircuitState.OPEN
            assert call_count["count"] == 3

            # Next call should fail fast with CircuitBreakerOpenError (no API call)
            async def workflow_logic_fast_fail():
                return await breaker.call(failing_external_service)

            with pytest.raises(CircuitBreakerOpenError):
                await workflow.execute(workflow_logic_fast_fail, {})

            # Verify function was NOT called (fail fast)
            assert call_count["count"] == 3  # Still 3, not 4

    async def test_circuit_breaker_recovers_after_timeout(self, setup_database):
        """Test circuit breaker transitions to HALF_OPEN and recovers."""
        workflow = WfloWorkflow(name="circuit-recovery-test", budget_usd=10.0)

        call_count = {"count": 0, "should_fail": True}

        async def recovering_service():
            call_count["count"] += 1
            if call_count["should_fail"]:
                raise ValueError("Service error")
            return {"status": "recovered"}

        breaker = CircuitBreaker(
            name="recovering-service",
            failure_threshold=2,
            recovery_timeout=0.2,  # Short timeout for testing
            success_threshold=2,
            expected_exception=(ValueError,),
        )

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            # Open circuit with failures
            for _ in range(2):
                async def workflow_logic_fail():
                    return await breaker.call(recovering_service)

                with pytest.raises(ValueError):
                    await workflow.execute(workflow_logic_fail, {})

            assert breaker.state == CircuitState.OPEN

            # Wait for recovery timeout
            await asyncio.sleep(0.25)

            # Service recovers
            call_count["should_fail"] = False

            # Attempt call (should transition to HALF_OPEN)
            async def workflow_logic_recover():
                return await breaker.call(recovering_service)

            result1 = await workflow.execute(workflow_logic_recover, {})
            assert breaker.state == CircuitState.HALF_OPEN
            assert result1["status"] == "recovered"

            # Second success should close circuit
            result2 = await workflow.execute(workflow_logic_recover, {})
            assert breaker.state == CircuitState.CLOSED
            assert result2["status"] == "recovered"

    async def test_circuit_breaker_decorator_in_workflow(self, setup_database):
        """Test @circuit_breaker decorator protecting workflow functions."""
        workflow = WfloWorkflow(name="circuit-decorator-test", budget_usd=10.0)

        failure_count = {"count": 0}

        @circuit_breaker(
            name="decorated-service",
            failure_threshold=2,
            expected_exception=(RuntimeError,),
        )
        async def protected_service_call():
            failure_count["count"] += 1
            if failure_count["count"] <= 2:
                raise RuntimeError(f"Service error {failure_count['count']}")
            return "service-response"

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            # First 2 calls fail and open circuit
            for _ in range(2):
                async def workflow_logic():
                    return await protected_service_call()

                with pytest.raises(RuntimeError):
                    await workflow.execute(workflow_logic, {})

            # Third call fails fast
            async def workflow_logic_fast_fail():
                return await protected_service_call()

            with pytest.raises(CircuitBreakerOpenError):
                await workflow.execute(workflow_logic_fast_fail, {})

            assert failure_count["count"] == 2  # Service not called on 3rd attempt


@pytest.mark.integration
@pytest.mark.asyncio
class TestResourceContentionIntegration:
    """Integration tests for ResourceLock with concurrent workflows."""

    async def test_concurrent_workflows_with_exclusive_lock(self, setup_database):
        """Test multiple workflows accessing exclusive resource sequentially."""
        # Simulate shared resource (e.g., database connection, API quota)
        execution_order = []

        # Mock database operations globally for all workflows
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            # Need to return a new generator each time
            mock_get_session.side_effect = lambda: mock_session_gen()

            async def workflow_with_exclusive_resource(workflow_id: str):
                workflow = WfloWorkflow(name=f"workflow-{workflow_id}", budget_usd=10.0)

                @detect_contention(
                    resource_name="exclusive-db-connection",
                    max_concurrent=1,  # Exclusive access
                    contention_threshold=0.5,
                )
                async def access_exclusive_resource():
                    execution_order.append(f"{workflow_id}-start")
                    await asyncio.sleep(0.1)  # Simulate work
                    execution_order.append(f"{workflow_id}-end")
                    return f"result-{workflow_id}"

                async def workflow_logic():
                    return await access_exclusive_resource()

                return await workflow.execute(workflow_logic, {})

            # Run 3 workflows concurrently
            results = await asyncio.gather(
                workflow_with_exclusive_resource("A"),
                workflow_with_exclusive_resource("B"),
                workflow_with_exclusive_resource("C"),
            )

            # Verify all completed
            assert len(results) == 3
            assert set(results) == {"result-A", "result-B", "result-C"}

            # Verify exclusive access (no interleaving)
            # Each workflow should complete before next starts
            assert len(execution_order) == 6
            for i in range(0, 6, 2):
                workflow_id = execution_order[i].split("-")[0]
                assert execution_order[i] == f"{workflow_id}-start"
                assert execution_order[i + 1] == f"{workflow_id}-end"

    async def test_resource_contention_detection(self, setup_database):
        """Test contention is detected when workflows wait too long."""
        lock = get_resource_lock(
            name="contended-resource",
            max_concurrent=1,
            contention_threshold=0.05,  # 50ms threshold
        )

        # Mock database operations globally
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.side_effect = lambda: mock_session_gen()

            async def workflow_accessing_resource(workflow_id: str, hold_time: float):
                workflow = WfloWorkflow(name=f"workflow-{workflow_id}", budget_usd=10.0)

                async def access_resource():
                    async with lock.acquire(workflow_id=workflow_id):
                        await asyncio.sleep(hold_time)
                    return "done"

                return await workflow.execute(access_resource, {})

            # First workflow holds lock for 100ms
            task1 = asyncio.create_task(workflow_accessing_resource("1", 0.1))
            await asyncio.sleep(0.01)  # Let first acquire lock

            # Second workflow will wait and detect contention
            task2 = asyncio.create_task(workflow_accessing_resource("2", 0.01))

            await asyncio.gather(task1, task2)

            # Verify contention was detected
            stats = lock.get_stats()
            assert stats["contention_count"] >= 1

    async def test_workflow_timeout_on_resource_contention(self, setup_database):
        """Test workflow fails gracefully when resource is unavailable."""
        lock = ResourceLock(
            name="timeout-test-resource",
            timeout=0.2,  # Short timeout
            max_concurrent=1,
        )

        holder_started = asyncio.Event()

        async def holder_workflow():
            workflow = WfloWorkflow(name="holder", budget_usd=10.0)

            async def hold_resource():
                async with lock.acquire(workflow_id="holder", timeout=5.0):
                    holder_started.set()
                    await asyncio.sleep(1.0)  # Hold for long time
                return "holder-done"

            with patch("wflo.sdk.workflow.get_session") as mock_get_session:
                mock_session = Mock()
                mock_session.add = Mock()
                mock_session.commit = AsyncMock()
                mock_session.flush = AsyncMock()
                mock_session.get = AsyncMock(return_value=None)

                mock_result = Mock()
                mock_result.scalar_one_or_none = Mock(return_value=None)
                mock_session.execute = AsyncMock(return_value=mock_result)

                async def mock_session_gen():
                    yield mock_session

                mock_get_session.return_value = mock_session_gen()

                return await workflow.execute(hold_resource, {})

        async def waiter_workflow():
            await holder_started.wait()  # Wait for holder to acquire lock

            workflow = WfloWorkflow(name="waiter", budget_usd=10.0)

            async def wait_for_resource():
                async with lock.acquire(workflow_id="waiter", timeout=0.1):
                    return "waiter-done"

            with patch("wflo.sdk.workflow.get_session") as mock_get_session:
                mock_session = Mock()
                mock_session.add = Mock()
                mock_session.commit = AsyncMock()
                mock_session.flush = AsyncMock()
                mock_session.get = AsyncMock(return_value=None)

                mock_result = Mock()
                mock_result.scalar_one_or_none = Mock(return_value=None)
                mock_session.execute = AsyncMock(return_value=mock_result)

                async def mock_session_gen():
                    yield mock_session

                mock_get_session.return_value = mock_session_gen()

                return await workflow.execute(wait_for_resource, {})

        # Start holder
        holder_task = asyncio.create_task(holder_workflow())

        # Waiter should timeout
        with pytest.raises(ContentionDetectedError) as exc_info:
            await waiter_workflow()

        error = exc_info.value
        assert error.resource_name == "timeout-test-resource"
        assert "holder" in error.holders

        # Cleanup
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestCombinedResiliencePatterns:
    """Integration tests combining multiple resilience patterns."""

    async def test_retry_with_circuit_breaker(self, setup_database):
        """Test RetryManager and CircuitBreaker working together."""
        workflow = WfloWorkflow(name="combined-test", budget_usd=10.0)

        call_count = {"count": 0}

        async def flaky_service_with_circuit_breaker():
            call_count["count"] += 1
            # Fail first 2 calls
            if call_count["count"] <= 2:
                raise ConnectionError(f"Error {call_count['count']}")
            return {"status": "success", "calls": call_count["count"]}

        # Circuit breaker protects service
        breaker = CircuitBreaker(
            name="protected-flaky-service",
            failure_threshold=5,  # High threshold
            expected_exception=(ConnectionError,),
        )

        # Retry manager handles transient failures
        retry_manager = RetryManager(
            max_retries=3,
            base_delay=0.05,
            strategy=RetryStrategy.EXPONENTIAL,
        )

        async def workflow_logic():
            # Retry wraps circuit breaker
            result = await retry_manager.execute(
                lambda: breaker.call(flaky_service_with_circuit_breaker),
                retryable_exceptions=(ConnectionError,),
            )
            return result

        # Mock database operations
        with patch("wflo.sdk.workflow.get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)

            mock_result = Mock()
            mock_result.scalar_one_or_none = Mock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_session_gen():
                yield mock_session

            mock_get_session.return_value = mock_session_gen()

            result = await workflow.execute(workflow_logic, {})

        # Verify retry handled failures and circuit breaker tracked them
        assert result["status"] == "success"
        assert result["calls"] == 3  # Failed twice, succeeded on third
        assert breaker.state == CircuitState.CLOSED  # Never opened (below threshold)
        assert breaker.failure_count == 0  # Reset on success
