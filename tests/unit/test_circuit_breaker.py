"""Unit tests for circuit breaker pattern."""

import asyncio
import pytest
import time

from wflo.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    circuit_breaker,
    get_circuit_breaker,
)


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(
            name="test-circuit",
            failure_threshold=3,
        )

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self):
        """Test successful call in CLOSED state."""
        breaker = CircuitBreaker(name="test")

        async def successful_function():
            return "success"

        result = await breaker.call(successful_function)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_increments_count(self):
        """Test failures increment failure count."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=5,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            await breaker.call(failing_function)

        assert breaker.failure_count == 1
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=3,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        # Trigger failures to reach threshold
        for i in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        # Circuit should now be OPEN
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_open_fails_fast(self):
        """Test circuit OPEN fails fast without calling function."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            expected_exception=(ValueError,),
        )

        call_count = []

        async def failing_function():
            call_count.append(1)
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN
        assert len(call_count) == 2

        # Now circuit is open, should fail fast
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await breaker.call(failing_function)

        # Function should NOT be called
        assert len(call_count) == 2  # Still 2, not 3
        assert exc_info.value.circuit_name == "test"

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,  # Very short for testing
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Should transition to HALF_OPEN on next call
        async def check_state():
            return "probe"

        # This should trigger transition to HALF_OPEN
        with pytest.raises(ValueError):
            await breaker.call(failing_function)

        # After attempting, should be HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_closes_on_success(self):
        """Test HALF_OPEN closes after successful calls."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.05,
            success_threshold=2,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        async def successful_function():
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)

        # Attempt call to transition to HALF_OPEN
        result1 = await breaker.call(successful_function)
        assert breaker.state == CircuitState.HALF_OPEN
        assert result1 == "success"

        # Second success should close circuit
        result2 = await breaker.call(successful_function)
        assert breaker.state == CircuitState.CLOSED
        assert result2 == "success"

    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self):
        """Test HALF_OPEN reopens circuit on failure."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.05,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)

        # Attempt call (moves to HALF_OPEN) but fails
        with pytest.raises(ValueError):
            await breaker.call(failing_function)

        # Should reopen
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_unexpected_exception_doesnt_count(self):
        """Test unexpected exceptions don't increment failure count."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            expected_exception=(ValueError,),  # Only track ValueError
        )

        async def raises_type_error():
            raise TypeError("Unexpected")

        # This should raise but not count as failure
        with pytest.raises(TypeError):
            await breaker.call(raises_type_error)

        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        """Test manual circuit reset."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        # Open circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_get_state(self):
        """Test get_state returns circuit information."""
        breaker = CircuitBreaker(
            name="test-circuit",
            failure_threshold=5,
            recovery_timeout=30.0,
        )

        state = breaker.get_state()

        assert state["name"] == "test-circuit"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["failure_threshold"] == 5
        assert state["recovery_timeout"] == 30.0

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Test successful call resets failure count in CLOSED state."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=5,
            expected_exception=(ValueError,),
        )

        async def failing_function():
            raise ValueError("Error")

        async def successful_function():
            return "success"

        # Some failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)

        assert breaker.failure_count == 2

        # Success resets count
        await breaker.call(successful_function)

        assert breaker.failure_count == 0


class TestCircuitBreakerDecorator:
    """Test @circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_async_function(self):
        """Test decorator on async function."""

        @circuit_breaker(
            name="test-decorator",
            failure_threshold=2,
            expected_exception=(ValueError,),
        )
        async def test_function():
            return "result"

        result = await test_function()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_decorator_shared_circuit_state(self):
        """Test decorator uses shared circuit breaker state."""

        @circuit_breaker(
            name="shared-circuit",
            failure_threshold=2,
            expected_exception=(ValueError,),
        )
        async def function_a():
            raise ValueError("Error")

        @circuit_breaker(
            name="shared-circuit",  # Same name = shared circuit
            failure_threshold=2,
            expected_exception=(ValueError,),
        )
        async def function_b():
            return "success"

        # Failures in function_a should affect function_b
        for _ in range(2):
            with pytest.raises(ValueError):
                await function_a()

        # Circuit is now open, function_b should also fail
        with pytest.raises(CircuitBreakerOpenError):
            await function_b()

    @pytest.mark.asyncio
    async def test_get_circuit_breaker_returns_existing(self):
        """Test get_circuit_breaker returns existing instance."""
        breaker1 = get_circuit_breaker(name="test-get", failure_threshold=3)
        breaker2 = get_circuit_breaker(name="test-get", failure_threshold=5)

        # Should return same instance (first config wins)
        assert breaker1 is breaker2
        assert breaker1.failure_threshold == 3  # Original config

    def test_circuit_breaker_sync_function(self):
        """Test circuit breaker with synchronous function."""
        breaker = CircuitBreaker(
            name="sync-test",
            failure_threshold=2,
            expected_exception=(ValueError,),
        )

        def sync_failing():
            raise ValueError("Sync error")

        # Trigger failures
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call_sync(sync_failing)

        assert breaker.state == CircuitState.OPEN

        # Should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call_sync(sync_failing)
