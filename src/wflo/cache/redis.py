"""Redis client wrapper with async support and connection pooling."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from wflo.config import get_settings
from wflo.observability import get_logger

logger = get_logger(__name__)

# Global connection pool (shared across application)
_redis_pool: redis.ConnectionPool | None = None


def get_redis_pool() -> redis.ConnectionPool:
    """Get or create the global Redis connection pool.

    Returns:
        Redis connection pool configured from settings

    Note:
        Pool is created once and reused across the application.
        Connection pooling reduces overhead of creating new connections.
    """
    global _redis_pool

    if _redis_pool is None:
        settings = get_settings()

        _redis_pool = redis.ConnectionPool.from_url(
            str(settings.redis_url),
            max_connections=settings.redis_max_connections,
            decode_responses=True,  # Auto-decode bytes to strings
            socket_connect_timeout=5,
            socket_keepalive=True,
        )

        logger.info(
            "redis_pool_created",
            url=str(settings.redis_url),
            max_connections=settings.redis_max_connections,
        )

    return _redis_pool


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Get a Redis client from the connection pool.

    Yields:
        Redis client for executing commands

    Example:
        >>> async with get_redis_client() as redis:
        ...     await redis.set("key", "value", ex=60)
        ...     value = await redis.get("key")
        ...     print(value)
        'value'

    Note:
        Client automatically closes when context exits.
        Connection is returned to pool, not closed.
    """
    pool = get_redis_pool()
    client = Redis(connection_pool=pool)

    try:
        yield client
    except RedisError as e:
        logger.error(
            "redis_error",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise
    finally:
        await client.close()


async def check_redis_health() -> bool:
    """Check if Redis is available and responding.

    Returns:
        True if Redis is healthy, False otherwise

    Example:
        >>> if await check_redis_health():
        ...     print("Redis is healthy")
        ... else:
        ...     print("Redis is down")
    """
    try:
        async with get_redis_client() as client:
            await client.ping()
            logger.debug("redis_health_check", status="healthy")
            return True
    except RedisError as e:
        logger.warning(
            "redis_health_check",
            status="unhealthy",
            error=str(e),
        )
        return False
    except Exception as e:
        logger.error(
            "redis_health_check_unexpected_error",
            error_type=type(e).__name__,
            error=str(e),
        )
        return False


async def close_redis_pool() -> None:
    """Close the global Redis connection pool.

    Call this during application shutdown to gracefully close all connections.

    Example:
        >>> # In application shutdown handler
        >>> await close_redis_pool()
    """
    global _redis_pool

    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("redis_pool_closed")
