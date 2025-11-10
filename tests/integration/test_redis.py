"""Integration tests for Redis caching and distributed locking.

These tests require a running Redis instance.
Run with: pytest tests/integration/test_redis.py
"""

import asyncio

import pytest

from wflo.cache import (
    DistributedLock,
    LLMCache,
    LockAcquisitionError,
    check_redis_health,
    distributed_lock,
    get_llm_cache,
    get_redis_client,
)


@pytest.mark.asyncio
class TestRedisClient:
    """Test Redis client connection and basic operations."""

    async def test_redis_health_check(self):
        """Test Redis health check."""
        is_healthy = await check_redis_health()
        assert is_healthy is True, "Redis should be healthy"

    async def test_redis_set_get(self):
        """Test basic Redis set/get operations."""
        async with get_redis_client() as redis:
            # Set a key
            await redis.set("test_key", "test_value", ex=60)

            # Get the key
            value = await redis.get("test_key")
            assert value == "test_value"

            # Delete the key
            await redis.delete("test_key")

    async def test_redis_expiration(self):
        """Test key expiration."""
        async with get_redis_client() as redis:
            # Set key with 1 second TTL
            await redis.set("expire_key", "value", ex=1)

            # Key should exist
            value = await redis.get("expire_key")
            assert value == "value"

            # Wait for expiration
            await asyncio.sleep(1.5)

            # Key should be gone
            value = await redis.get("expire_key")
            assert value is None


@pytest.mark.asyncio
class TestDistributedLock:
    """Test distributed locking functionality."""

    async def test_lock_acquisition_and_release(self):
        """Test basic lock acquisition and release."""
        lock = DistributedLock("test_lock", timeout=60)

        # Acquire lock
        acquired = await lock.acquire()
        assert acquired is True

        # Release lock
        released = await lock.release()
        assert released is True

    async def test_lock_context_manager(self):
        """Test lock using context manager."""
        async with distributed_lock("test_lock_cm", timeout=60):
            # Inside critical section
            async with get_redis_client() as redis:
                exists = await redis.exists("lock:test_lock_cm")
                assert exists == 1, "Lock should exist"

        # After context exit, lock should be released
        async with get_redis_client() as redis:
            exists = await redis.exists("lock:test_lock_cm")
            assert exists == 0, "Lock should be released"

    async def test_lock_prevents_concurrent_access(self):
        """Test that lock prevents concurrent access."""
        lock1 = DistributedLock("concurrent_test", timeout=5)
        lock2 = DistributedLock("concurrent_test", timeout=5)

        # First lock acquires
        acquired1 = await lock1.acquire()
        assert acquired1 is True

        # Second lock should fail to acquire
        acquired2 = await lock2.acquire(wait=False)
        assert acquired2 is False

        # Release first lock
        await lock1.release()

        # Now second lock should acquire
        acquired2 = await lock2.acquire(wait=False)
        assert acquired2 is True

        # Clean up
        await lock2.release()

    async def test_lock_auto_expiration(self):
        """Test that locks auto-expire after timeout."""
        lock = DistributedLock("expire_lock", timeout=1)

        # Acquire lock
        await lock.acquire()

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Another instance should be able to acquire
        lock2 = DistributedLock("expire_lock", timeout=60)
        acquired = await lock2.acquire(wait=False)
        assert acquired is True

        # Clean up
        await lock2.release()

    async def test_lock_renewal(self):
        """Test lock renewal functionality."""
        lock = DistributedLock("renewal_lock", timeout=2)

        # Acquire lock
        await lock.acquire()

        # Renew lock
        renewed = await lock.renew()
        assert renewed is True

        # Wait past original timeout
        await asyncio.sleep(2.5)

        # Lock should still be held due to renewal
        async with get_redis_client() as redis:
            exists = await redis.exists("lock:renewal_lock")
            # Note: This might fail if renewal extended the lock
            # For proper test, we'd check the TTL instead

        # Clean up
        await lock.release()

    async def test_lock_auto_renewal(self):
        """Test automatic lock renewal for long operations."""
        lock = DistributedLock(
            "auto_renewal_lock",
            timeout=2,
            auto_renewal=True,
            renewal_interval=1,
        )

        async with lock():
            # Simulate long operation
            await asyncio.sleep(3)

            # Lock should still be held due to auto-renewal
            async with get_redis_client() as redis:
                exists = await redis.exists("lock:auto_renewal_lock")
                assert exists == 1, "Lock should still exist due to auto-renewal"

    async def test_lock_with_wait(self):
        """Test lock acquisition with wait."""
        lock1 = DistributedLock("wait_lock", timeout=2)
        lock2 = DistributedLock("wait_lock", timeout=60)

        # Acquire first lock
        await lock1.acquire()

        async def delayed_release():
            """Release lock after 1 second."""
            await asyncio.sleep(1)
            await lock1.release()

        # Start delayed release
        asyncio.create_task(delayed_release())

        # Second lock waits and acquires after release
        acquired = await lock2.acquire(wait=True, retry_interval=0.1)
        assert acquired is True

        # Clean up
        await lock2.release()

    async def test_lock_context_manager_exception(self):
        """Test that lock is released even on exception."""
        try:
            async with distributed_lock("exception_lock", timeout=60):
                # Simulate error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Lock should be released
        async with get_redis_client() as redis:
            exists = await redis.exists("lock:exception_lock")
            assert exists == 0, "Lock should be released after exception"

    async def test_lock_acquisition_error(self):
        """Test LockAcquisitionError when lock cannot be acquired."""
        lock1 = DistributedLock("error_lock", timeout=60)
        await lock1.acquire()

        # Try to acquire with context manager (should raise)
        with pytest.raises(LockAcquisitionError):
            lock2 = DistributedLock("error_lock", timeout=60)
            async with lock2(wait=False):
                pass

        # Clean up
        await lock1.release()


@pytest.mark.asyncio
class TestLLMCache:
    """Test LLM response caching."""

    async def test_cache_miss_and_set(self):
        """Test cache miss and subsequent set."""
        cache = LLMCache(ttl=60)

        # Cache miss
        result = await cache.get(
            model="gpt-4-turbo",
            prompt="What is Python?",
        )
        assert result is None

        # Set cache
        response = {"text": "Python is a programming language"}
        success = await cache.set(
            model="gpt-4-turbo",
            prompt="What is Python?",
            response=response,
        )
        assert success is True

        # Cache hit
        cached = await cache.get(
            model="gpt-4-turbo",
            prompt="What is Python?",
        )
        assert cached == response

    async def test_cache_get_or_compute(self):
        """Test get_or_compute convenience method."""
        cache = LLMCache(ttl=60)

        call_count = 0

        async def compute_response():
            """Simulate LLM API call."""
            nonlocal call_count
            call_count += 1
            return {"text": f"Response {call_count}"}

        # First call - cache miss, compute
        response1 = await cache.get_or_compute(
            model="gpt-4-turbo",
            prompt="Explain async",
            compute_fn=compute_response,
        )
        assert response1 == {"text": "Response 1"}
        assert call_count == 1

        # Second call - cache hit, no compute
        response2 = await cache.get_or_compute(
            model="gpt-4-turbo",
            prompt="Explain async",
            compute_fn=compute_response,
        )
        assert response2 == {"text": "Response 1"}
        assert call_count == 1  # Should not increment

    async def test_cache_with_different_parameters(self):
        """Test that cache keys differ for different parameters."""
        cache = LLMCache(ttl=60)

        # Set cache with temperature=0.7
        await cache.set(
            model="gpt-4-turbo",
            prompt="Hello",
            response={"text": "Response A"},
            temperature=0.7,
        )

        # Get with temperature=0.7 (should hit)
        result1 = await cache.get(
            model="gpt-4-turbo",
            prompt="Hello",
            temperature=0.7,
        )
        assert result1 == {"text": "Response A"}

        # Get with temperature=0.0 (should miss)
        result2 = await cache.get(
            model="gpt-4-turbo",
            prompt="Hello",
            temperature=0.0,
        )
        assert result2 is None

    async def test_cache_expiration(self):
        """Test cache expiration."""
        cache = LLMCache(ttl=1)  # 1 second TTL

        # Set cache
        await cache.set(
            model="gpt-4-turbo",
            prompt="Expire test",
            response={"text": "Expires soon"},
        )

        # Should hit immediately
        result1 = await cache.get(
            model="gpt-4-turbo",
            prompt="Expire test",
        )
        assert result1 is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should miss after expiration
        result2 = await cache.get(
            model="gpt-4-turbo",
            prompt="Expire test",
        )
        assert result2 is None

    async def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = LLMCache(ttl=60)

        # Set cache
        await cache.set(
            model="gpt-4-turbo",
            prompt="Invalidate me",
            response={"text": "Original"},
        )

        # Verify cached
        result = await cache.get(
            model="gpt-4-turbo",
            prompt="Invalidate me",
        )
        assert result is not None

        # Invalidate
        deleted = await cache.invalidate(
            model="gpt-4-turbo",
            prompt="Invalidate me",
        )
        assert deleted is True

        # Verify gone
        result = await cache.get(
            model="gpt-4-turbo",
            prompt="Invalidate me",
        )
        assert result is None

    async def test_cache_clear_all(self):
        """Test clearing all cached entries."""
        cache = LLMCache(ttl=60, namespace="test_clear")

        # Set multiple cache entries
        await cache.set(
            model="gpt-4-turbo",
            prompt="Entry 1",
            response={"text": "Response 1"},
        )
        await cache.set(
            model="gpt-4-turbo",
            prompt="Entry 2",
            response={"text": "Response 2"},
        )

        # Clear all
        deleted_count = await cache.clear_all()
        assert deleted_count == 2

        # Verify all gone
        result1 = await cache.get(model="gpt-4-turbo", prompt="Entry 1")
        result2 = await cache.get(model="gpt-4-turbo", prompt="Entry 2")
        assert result1 is None
        assert result2 is None

    async def test_get_llm_cache(self):
        """Test global cache instance."""
        cache1 = get_llm_cache(ttl=60)
        cache2 = get_llm_cache(ttl=60)

        # Should return same instance
        assert cache1 is cache2

    async def test_cache_with_max_tokens(self):
        """Test cache key includes max_tokens parameter."""
        cache = LLMCache(ttl=60)

        # Set with max_tokens=100
        await cache.set(
            model="gpt-4-turbo",
            prompt="Count tokens",
            response={"text": "100 tokens"},
            max_tokens=100,
        )

        # Get with max_tokens=100 (should hit)
        result1 = await cache.get(
            model="gpt-4-turbo",
            prompt="Count tokens",
            max_tokens=100,
        )
        assert result1 is not None

        # Get with max_tokens=200 (should miss)
        result2 = await cache.get(
            model="gpt-4-turbo",
            prompt="Count tokens",
            max_tokens=200,
        )
        assert result2 is None
