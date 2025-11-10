"""Redis-based caching and distributed locking.

This package provides:
- Distributed locks for preventing duplicate operations
- LLM response caching to reduce API costs
- Redis connection pooling for efficiency
"""

from wflo.cache.llm_cache import LLMCache, get_llm_cache
from wflo.cache.locks import DistributedLock, LockAcquisitionError, distributed_lock
from wflo.cache.redis import (
    check_redis_health,
    close_redis_pool,
    get_redis_client,
    get_redis_pool,
)

__all__ = [
    # Redis client
    "get_redis_client",
    "get_redis_pool",
    "check_redis_health",
    "close_redis_pool",
    # Distributed locks
    "DistributedLock",
    "distributed_lock",
    "LockAcquisitionError",
    # LLM caching
    "LLMCache",
    "get_llm_cache",
]
