"""Distributed locking using Redis for preventing duplicate operations."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from wflo.cache.redis import get_redis_client
from wflo.observability import get_logger

logger = get_logger(__name__)


class LockAcquisitionError(Exception):
    """Raised when a lock cannot be acquired within the timeout period."""

    pass


class DistributedLock:
    """Distributed lock using Redis for preventing concurrent operations.

    Features:
    - Automatic lock renewal (heartbeat) for long operations
    - Lock ownership verification before release
    - Timeout-based lock acquisition
    - Context manager support for automatic cleanup

    Example:
        >>> # Basic usage
        >>> async with DistributedLock("workflow:abc-123", timeout=60) as lock:
        ...     # Critical section - only one process can execute
        ...     await process_workflow()

        >>> # With auto-renewal for long operations
        >>> async with DistributedLock(
        ...     "workflow:abc-123",
        ...     timeout=300,
        ...     auto_renewal=True
        ... ) as lock:
        ...     # Lock auto-renewed every 100 seconds
        ...     await long_running_operation()
    """

    def __init__(
        self,
        key: str,
        timeout: int = 60,
        auto_renewal: bool = False,
        renewal_interval: int | None = None,
    ):
        """Initialize distributed lock.

        Args:
            key: Lock key (e.g., "workflow:abc-123")
            timeout: Lock expiration in seconds (default: 60)
            auto_renewal: If True, automatically renew lock before expiration
            renewal_interval: Seconds between renewals (default: timeout / 3)
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.auto_renewal = auto_renewal
        self.renewal_interval = renewal_interval or max(timeout // 3, 10)

        # Unique lock ID to verify ownership
        self.lock_id = str(uuid.uuid4())

        # Renewal task handle
        self._renewal_task: asyncio.Task | None = None

    async def acquire(self, wait: bool = False, retry_interval: float = 0.1) -> bool:
        """Acquire the distributed lock.

        Args:
            wait: If True, wait until lock is acquired (blocks indefinitely)
            retry_interval: Seconds to wait between acquisition attempts

        Returns:
            True if lock acquired, False otherwise

        Raises:
            LockAcquisitionError: If lock cannot be acquired (when wait=False)
        """
        async with get_redis_client() as redis:
            while True:
                # Try to acquire lock with SET NX (set if not exists)
                acquired = await redis.set(
                    self.key,
                    self.lock_id,
                    nx=True,  # Only set if key doesn't exist
                    ex=self.timeout,  # Expiration time
                )

                if acquired:
                    logger.info(
                        "lock_acquired",
                        key=self.key,
                        lock_id=self.lock_id,
                        timeout=self.timeout,
                    )

                    # Start auto-renewal if enabled
                    if self.auto_renewal:
                        self._start_renewal()

                    return True

                if not wait:
                    logger.warning(
                        "lock_acquisition_failed",
                        key=self.key,
                        lock_id=self.lock_id,
                    )
                    return False

                # Wait before retrying
                logger.debug(
                    "lock_waiting",
                    key=self.key,
                    retry_interval=retry_interval,
                )
                await asyncio.sleep(retry_interval)

    async def release(self) -> bool:
        """Release the distributed lock.

        Only releases if the lock is still owned by this instance
        (verified by lock_id).

        Returns:
            True if lock released, False if lock not owned

        Note:
            Uses Lua script to ensure atomic check-and-delete operation.
        """
        # Stop auto-renewal
        await self._stop_renewal()

        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        async with get_redis_client() as redis:
            result = await redis.eval(lua_script, 1, self.key, self.lock_id)

            if result:
                logger.info(
                    "lock_released",
                    key=self.key,
                    lock_id=self.lock_id,
                )
                return True
            else:
                logger.warning(
                    "lock_release_failed",
                    key=self.key,
                    lock_id=self.lock_id,
                    reason="lock_not_owned_or_expired",
                )
                return False

    async def renew(self) -> bool:
        """Renew the lock expiration time.

        Returns:
            True if lock renewed, False if lock not owned

        Note:
            Only renews if lock is still owned by this instance.
        """
        # Lua script for atomic check-and-expire
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        async with get_redis_client() as redis:
            result = await redis.eval(
                lua_script,
                1,
                self.key,
                self.lock_id,
                self.timeout,
            )

            if result:
                logger.debug(
                    "lock_renewed",
                    key=self.key,
                    lock_id=self.lock_id,
                    timeout=self.timeout,
                )
                return True
            else:
                logger.warning(
                    "lock_renewal_failed",
                    key=self.key,
                    lock_id=self.lock_id,
                )
                return False

    def _start_renewal(self) -> None:
        """Start background task to auto-renew lock."""
        async def renewal_loop():
            """Periodically renew the lock."""
            while True:
                await asyncio.sleep(self.renewal_interval)

                success = await self.renew()
                if not success:
                    logger.error(
                        "lock_renewal_stopped",
                        key=self.key,
                        lock_id=self.lock_id,
                        reason="renewal_failed",
                    )
                    break

        self._renewal_task = asyncio.create_task(renewal_loop())

        logger.debug(
            "lock_renewal_started",
            key=self.key,
            lock_id=self.lock_id,
            interval=self.renewal_interval,
        )

    async def _stop_renewal(self) -> None:
        """Stop background renewal task."""
        if self._renewal_task and not self._renewal_task.done():
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass

            logger.debug(
                "lock_renewal_stopped",
                key=self.key,
                lock_id=self.lock_id,
            )

    @asynccontextmanager
    async def __call__(
        self,
        wait: bool = False,
        retry_interval: float = 0.1,
    ) -> AsyncGenerator["DistributedLock", None]:
        """Context manager for automatic lock acquisition and release.

        Args:
            wait: If True, wait until lock is acquired
            retry_interval: Seconds between acquisition attempts

        Yields:
            Lock instance

        Raises:
            LockAcquisitionError: If lock cannot be acquired

        Example:
            >>> lock = DistributedLock("workflow:123", timeout=60)
            >>> async with lock() as acquired_lock:
            ...     # Critical section
            ...     await process_data()
        """
        acquired = await self.acquire(wait=wait, retry_interval=retry_interval)

        if not acquired:
            raise LockAcquisitionError(
                f"Failed to acquire lock: {self.key}"
            )

        try:
            yield self
        finally:
            await self.release()


@asynccontextmanager
async def distributed_lock(
    key: str,
    timeout: int = 60,
    auto_renewal: bool = False,
    wait: bool = False,
) -> AsyncGenerator[DistributedLock, None]:
    """Convenience function for distributed lock context manager.

    Args:
        key: Lock key
        timeout: Lock expiration in seconds
        auto_renewal: Enable auto-renewal
        wait: Wait for lock acquisition

    Yields:
        Acquired lock

    Example:
        >>> async with distributed_lock("workflow:123", timeout=120) as lock:
        ...     await execute_workflow()
    """
    lock = DistributedLock(key=key, timeout=timeout, auto_renewal=auto_renewal)

    async with lock(wait=wait):
        yield lock
