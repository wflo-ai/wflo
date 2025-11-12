"""Retry manager with exponential backoff for resilient workflows."""

import asyncio
import random
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, Union

import structlog

logger = structlog.get_logger()


class RetryStrategy(str, Enum):
    """Retry strategies for handling failures."""

    EXPONENTIAL = "exponential"  # 2^n backoff (1s, 2s, 4s, 8s, ...)
    LINEAR = "linear"  # n * base_delay (1s, 2s, 3s, 4s, ...)
    FIXED = "fixed"  # constant delay (1s, 1s, 1s, 1s, ...)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Exception,
    ):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class RetryManager:
    """
    Manages retry logic with configurable backoff strategies.

    Provides exponential backoff, linear backoff, and fixed delay strategies
    with optional jitter to prevent thundering herd problems.

    Example:
        retry_manager = RetryManager(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
        )

        result = await retry_manager.execute(
            my_async_function,
            arg1, arg2,
            retryable_exceptions=(TimeoutError, ConnectionError),
        )
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        """
        Initialize retry manager.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds (cap)
            multiplier: Multiplier for exponential/linear backoff
            strategy: Retry strategy (exponential, linear, fixed)
            jitter: Whether to add random jitter to delays
            jitter_factor: Jitter factor (0.0 to 1.0). Delay * (1 ± jitter_factor)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.strategy = strategy
        self.jitter = jitter
        self.jitter_factor = jitter_factor

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            # Exponential backoff: base_delay * multiplier^attempt
            delay = self.base_delay * (self.multiplier**attempt)

        elif self.strategy == RetryStrategy.LINEAR:
            # Linear backoff: base_delay * (attempt + 1) * multiplier
            delay = self.base_delay * (attempt + 1) * self.multiplier

        elif self.strategy == RetryStrategy.FIXED:
            # Fixed delay
            delay = self.base_delay

        else:
            raise ValueError(f"Unknown retry strategy: {self.strategy}")

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
            # Ensure delay is never negative
            delay = max(0.0, delay)

        return delay

    async def execute(
        self,
        func: Callable,
        *args: Any,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exceptions to retry on
            on_retry: Optional callback called on each retry (attempt, exception)
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retries are exhausted
            Exception: If non-retryable exception occurs
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                logger.debug(
                    "retry_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    function=func.__name__,
                )

                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(
                        "retry_succeeded",
                        attempt=attempt,
                        function=func.__name__,
                    )

                return result

            except retryable_exceptions as e:
                last_exception = e

                if attempt >= self.max_retries:
                    # No more retries left
                    logger.error(
                        "retry_exhausted",
                        attempt=attempt,
                        max_retries=self.max_retries,
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise RetryExhaustedError(
                        f"Retry exhausted after {attempt + 1} attempts",
                        attempts=attempt + 1,
                        last_exception=e,
                    ) from e

                # Calculate backoff delay
                delay = self.calculate_delay(attempt)

                logger.warning(
                    "retry_scheduled",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    delay_seconds=round(delay, 2),
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Call retry callback if provided
                if on_retry:
                    on_retry(attempt, e)

                # Wait before retry
                await asyncio.sleep(delay)

            except Exception as e:
                # Non-retryable exception
                logger.error(
                    "non_retryable_exception",
                    attempt=attempt,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        # Should never reach here
        raise RetryExhaustedError(
            f"Retry logic failed unexpectedly",
            attempts=self.max_retries + 1,
            last_exception=last_exception or Exception("Unknown error"),
        )

    def execute_sync(
        self,
        func: Callable,
        *args: Any,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute synchronous function with retry logic.

        Args:
            func: Synchronous function to execute
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exceptions to retry on
            on_retry: Optional callback called on each retry
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retries are exhausted
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    "retry_attempt_sync",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    function=func.__name__,
                )

                result = func(*args, **kwargs)

                if attempt > 0:
                    logger.info(
                        "retry_succeeded_sync",
                        attempt=attempt,
                        function=func.__name__,
                    )

                return result

            except retryable_exceptions as e:
                last_exception = e

                if attempt >= self.max_retries:
                    logger.error(
                        "retry_exhausted_sync",
                        attempt=attempt,
                        max_retries=self.max_retries,
                        function=func.__name__,
                        error=str(e),
                    )
                    raise RetryExhaustedError(
                        f"Retry exhausted after {attempt + 1} attempts",
                        attempts=attempt + 1,
                        last_exception=e,
                    ) from e

                delay = self.calculate_delay(attempt)

                logger.warning(
                    "retry_scheduled_sync",
                    attempt=attempt,
                    delay_seconds=round(delay, 2),
                    function=func.__name__,
                    error=str(e),
                )

                if on_retry:
                    on_retry(attempt, e)

                time.sleep(delay)

            except Exception as e:
                logger.error(
                    "non_retryable_exception_sync",
                    attempt=attempt,
                    function=func.__name__,
                    error=str(e),
                )
                raise

        raise RetryExhaustedError(
            f"Retry logic failed unexpectedly",
            attempts=self.max_retries + 1,
            last_exception=last_exception or Exception("Unknown error"),
        )


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for automatic retry with exponential backoff.

    Example:
        @retry_with_backoff(
            max_retries=3,
            base_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL,
            retryable_exceptions=(TimeoutError, ConnectionError),
        )
        async def fetch_data():
            # This will be retried on TimeoutError or ConnectionError
            return await http_client.get("/api/data")

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Multiplier for backoff
        strategy: Retry strategy
        jitter: Whether to add jitter
        retryable_exceptions: Exceptions to retry on
    """

    def decorator(func: Callable) -> Callable:
        retry_manager = RetryManager(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            multiplier=multiplier,
            strategy=strategy,
            jitter=jitter,
        )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_manager.execute(
                func, *args, retryable_exceptions=retryable_exceptions, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return retry_manager.execute_sync(
                func, *args, retryable_exceptions=retryable_exceptions, **kwargs
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
