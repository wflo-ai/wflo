"""Resource contention detection and prevention for concurrent workflows."""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import structlog

logger = structlog.get_logger()


class ContentionDetectedError(Exception):
    """Raised when resource contention is detected."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        wait_time: float,
        holders: list[str],
    ):
        super().__init__(message)
        self.resource_name = resource_name
        self.wait_time = wait_time
        self.holders = holders


class ResourceLock:
    """
    Distributed resource lock with contention detection.

    Tracks resource access patterns and detects contention when multiple
    workflows compete for the same resource.

    Example:
        lock = ResourceLock(
            name="database-connection-pool",
            timeout=30.0,
            contention_threshold=5.0,
        )

        async with lock.acquire(workflow_id="exec-123"):
            # Access protected resource
            await database.execute(query)
    """

    def __init__(
        self,
        name: str,
        timeout: float = 30.0,
        contention_threshold: float = 5.0,
        max_concurrent: int = 1,
    ):
        """
        Initialize resource lock.

        Args:
            name: Resource name for logging and metrics
            timeout: Maximum time to wait for lock (seconds)
            contention_threshold: Warn if wait time exceeds this (seconds)
            max_concurrent: Maximum concurrent holders (1 = exclusive lock)
        """
        self.name = name
        self.timeout = timeout
        self.contention_threshold = contention_threshold
        self.max_concurrent = max_concurrent

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._holders: set[str] = set()
        self._wait_times: list[float] = []
        self._total_acquisitions = 0
        self._contention_count = 0

    @asynccontextmanager
    async def acquire(
        self,
        workflow_id: str,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[None, None]:
        """
        Acquire resource lock with contention detection.

        Args:
            workflow_id: Identifier of workflow acquiring lock
            timeout: Override default timeout

        Yields:
            None (lock is held during context)

        Raises:
            ContentionDetectedError: If timeout exceeded
            asyncio.TimeoutError: If acquisition times out
        """
        acquisition_timeout = timeout or self.timeout
        start_time = time.time()

        logger.debug(
            "resource_lock_acquire_attempt",
            resource_name=self.name,
            workflow_id=workflow_id,
            timeout=acquisition_timeout,
        )

        try:
            # Try to acquire with timeout
            async with asyncio.timeout(acquisition_timeout):
                async with self._semaphore:
                    wait_time = time.time() - start_time

                    # Record acquisition
                    self._total_acquisitions += 1
                    self._wait_times.append(wait_time)
                    self._holders.add(workflow_id)

                    # Check for contention
                    if wait_time > self.contention_threshold:
                        self._contention_count += 1

                        logger.warning(
                            "resource_contention_detected",
                            resource_name=self.name,
                            workflow_id=workflow_id,
                            wait_time_seconds=round(wait_time, 2),
                            threshold_seconds=self.contention_threshold,
                            total_contentions=self._contention_count,
                            current_holders=list(self._holders),
                        )

                    logger.info(
                        "resource_lock_acquired",
                        resource_name=self.name,
                        workflow_id=workflow_id,
                        wait_time_seconds=round(wait_time, 2),
                        concurrent_holders=len(self._holders),
                    )

                    try:
                        yield

                    finally:
                        # Release lock
                        self._holders.discard(workflow_id)

                        hold_time = time.time() - start_time - wait_time

                        logger.info(
                            "resource_lock_released",
                            resource_name=self.name,
                            workflow_id=workflow_id,
                            hold_time_seconds=round(hold_time, 2),
                        )

        except asyncio.TimeoutError as e:
            wait_time = time.time() - start_time

            logger.error(
                "resource_lock_timeout",
                resource_name=self.name,
                workflow_id=workflow_id,
                wait_time_seconds=round(wait_time, 2),
                timeout_seconds=acquisition_timeout,
                current_holders=list(self._holders),
            )

            raise ContentionDetectedError(
                f"Resource '{self.name}' lock acquisition timeout after {wait_time:.1f}s",
                resource_name=self.name,
                wait_time=wait_time,
                holders=list(self._holders),
            ) from e

    def get_stats(self) -> dict[str, Any]:
        """
        Get resource lock statistics.

        Returns:
            Dictionary with lock statistics
        """
        avg_wait_time = (
            sum(self._wait_times) / len(self._wait_times) if self._wait_times else 0.0
        )

        max_wait_time = max(self._wait_times) if self._wait_times else 0.0

        contention_rate = (
            self._contention_count / self._total_acquisitions
            if self._total_acquisitions > 0
            else 0.0
        )

        return {
            "resource_name": self.name,
            "total_acquisitions": self._total_acquisitions,
            "contention_count": self._contention_count,
            "contention_rate": round(contention_rate, 3),
            "avg_wait_time_seconds": round(avg_wait_time, 3),
            "max_wait_time_seconds": round(max_wait_time, 3),
            "current_holders": list(self._holders),
            "concurrent_capacity": self.max_concurrent,
        }

    def reset_stats(self) -> None:
        """Reset statistics (useful for testing)."""
        self._wait_times = []
        self._total_acquisitions = 0
        self._contention_count = 0


# Global resource lock registry
_resource_locks: dict[str, ResourceLock] = {}


def get_resource_lock(
    name: str,
    timeout: float = 30.0,
    contention_threshold: float = 5.0,
    max_concurrent: int = 1,
) -> ResourceLock:
    """
    Get or create a resource lock by name.

    Args:
        name: Resource name
        timeout: Lock acquisition timeout
        contention_threshold: Contention warning threshold
        max_concurrent: Maximum concurrent holders

    Returns:
        ResourceLock instance
    """
    if name not in _resource_locks:
        _resource_locks[name] = ResourceLock(
            name=name,
            timeout=timeout,
            contention_threshold=contention_threshold,
            max_concurrent=max_concurrent,
        )

    return _resource_locks[name]


def detect_contention(
    resource_name: str,
    timeout: float = 30.0,
    contention_threshold: float = 5.0,
    max_concurrent: int = 1,
):
    """
    Decorator for automatic resource contention detection.

    Example:
        @detect_contention(
            resource_name="database-pool",
            contention_threshold=2.0,
        )
        async def execute_query(query: str):
            async with database.transaction():
                return await database.execute(query)

    Args:
        resource_name: Name of protected resource
        timeout: Lock timeout in seconds
        contention_threshold: Warn threshold in seconds
        max_concurrent: Maximum concurrent access
    """

    def decorator(func):
        from functools import wraps
        from wflo.sdk.context import get_current_execution_id

        lock = get_resource_lock(
            name=resource_name,
            timeout=timeout,
            contention_threshold=contention_threshold,
            max_concurrent=max_concurrent,
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get workflow ID from context
            workflow_id = get_current_execution_id()

            async with lock.acquire(workflow_id=workflow_id):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
