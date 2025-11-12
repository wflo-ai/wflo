"""Circuit breaker pattern for failing services and tool calls."""

import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

import structlog

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, failure_count: int):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.failure_count = failure_count


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Tracks failure rate and opens circuit when threshold is exceeded.
    Prevents repeated calls to failing services, allowing them time to recover.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Circuit is open, requests fail immediately with CircuitBreakerOpenError
    - HALF_OPEN: Testing recovery, limited requests allowed

    Example:
        breaker = CircuitBreaker(
            name="openai-api",
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=TimeoutError,
        )

        try:
            result = await breaker.call(make_api_request, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit is open, use fallback
            result = fallback_value
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        expected_exception: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name (for logging/metrics)
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery (OPEN → HALF_OPEN)
            success_threshold: Successful calls needed in HALF_OPEN to close circuit
            expected_exception: Exceptions that count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if self.state != CircuitState.OPEN:
            return False

        if self.opened_at is None:
            return True

        return (time.time() - self.opened_at) >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                "circuit_breaker_success_in_half_open",
                circuit_name=self.name,
                success_count=self.success_count,
                success_threshold=self.success_threshold,
            )

            if self.success_count >= self.success_threshold:
                # Enough successes, close circuit
                self._close_circuit()
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    def _record_failure(self, exception: Exception) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.warning(
            "circuit_breaker_failure",
            circuit_name=self.name,
            failure_count=self.failure_count,
            failure_threshold=self.failure_threshold,
            state=self.state.value,
            error=str(exception),
            error_type=type(exception).__name__,
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failure in HALF_OPEN, reopen circuit
            logger.warning(
                "circuit_breaker_reopening",
                circuit_name=self.name,
                reason="failure_in_half_open",
            )
            self._open_circuit()

        elif self.state == CircuitState.CLOSED:
            # Check if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()

    def _open_circuit(self) -> None:
        """Open circuit breaker."""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.success_count = 0

        logger.error(
            "circuit_breaker_opened",
            circuit_name=self.name,
            failure_count=self.failure_count,
            recovery_timeout=self.recovery_timeout,
        )

    def _close_circuit(self) -> None:
        """Close circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None

        logger.info(
            "circuit_breaker_closed",
            circuit_name=self.name,
        )

    def _attempt_reset(self) -> None:
        """Attempt to reset circuit breaker to HALF_OPEN."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0

        logger.info(
            "circuit_breaker_half_open",
            circuit_name=self.name,
        )

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the function
        """
        # Check if circuit should attempt reset
        if self._should_attempt_reset():
            self._attempt_reset()

        # Fail fast if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                circuit_name=self.name,
                failure_count=self.failure_count,
            )

        # Attempt call
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure(e)
            raise

        except Exception as e:
            # Unexpected exception, don't count as failure
            logger.error(
                "circuit_breaker_unexpected_exception",
                circuit_name=self.name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def call_sync(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute synchronous function through circuit breaker.

        Args:
            func: Synchronous function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self._should_attempt_reset():
            self._attempt_reset()

        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                circuit_name=self.name,
                failure_count=self.failure_count,
            )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(
            "circuit_breaker_manual_reset",
            circuit_name=self.name,
        )
        self._close_circuit()

    def get_state(self) -> dict:
        """
        Get current circuit breaker state.

        Returns:
            Dictionary with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "opened_at": self.opened_at,
            "recovery_timeout": self.recovery_timeout,
        }


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    expected_exception: Tuple[Type[Exception], ...] = (Exception,),
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Recovery timeout in seconds
        success_threshold: Successes needed to close
        expected_exception: Exceptions to track

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            expected_exception=expected_exception,
        )

    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    expected_exception: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for automatic circuit breaker protection.

    Example:
        @circuit_breaker(
            name="openai-api",
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=(TimeoutError, ConnectionError),
        )
        async def call_openai_api():
            return await client.chat.completions.create(...)

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Recovery timeout in seconds
        success_threshold: Successes needed to close
        expected_exception: Exceptions to track
    """

    def decorator(func: Callable) -> Callable:
        breaker = get_circuit_breaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            expected_exception=expected_exception,
        )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await breaker.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call_sync(func, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
