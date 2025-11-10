"""LLM response caching to reduce API costs and latency."""

import hashlib
import json
from typing import Any, Callable, TypeVar

from wflo.cache.redis import get_redis_client
from wflo.observability import get_logger
from wflo.observability.metrics import llm_cache_hits_total, llm_cache_misses_total

logger = get_logger(__name__)

T = TypeVar("T")


class LLMCache:
    """Cache for LLM API responses to reduce costs and improve latency.

    Caches responses by (model, prompt, temperature, max_tokens) tuple.
    Uses Redis for distributed caching across multiple workers.

    Cost Savings Example:
        - GPT-4 Turbo: $10/M input tokens → $0 if cached
        - Claude 3.5 Sonnet: $3/M input tokens → $0 if cached
        - Expected savings: 20-40% for workflows with repeated prompts

    Example:
        >>> cache = LLMCache(ttl=3600)  # 1 hour cache
        >>>
        >>> # Cache LLM response
        >>> response = await cache.get_or_compute(
        ...     model="gpt-4-turbo",
        ...     prompt="What is Python?",
        ...     compute_fn=lambda: llm_client.generate(...),
        ...     temperature=0.7,
        ... )
        >>>
        >>> # Second call hits cache (0 API cost)
        >>> response2 = await cache.get_or_compute(
        ...     model="gpt-4-turbo",
        ...     prompt="What is Python?",
        ...     compute_fn=lambda: llm_client.generate(...),
        ...     temperature=0.7,
        ... )
    """

    def __init__(self, ttl: int = 3600, namespace: str = "llm_cache"):
        """Initialize LLM cache.

        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
            namespace: Redis key namespace (default: "llm_cache")
        """
        self.ttl = ttl
        self.namespace = namespace

    def _generate_cache_key(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate cache key from LLM parameters.

        Uses SHA256 hash to avoid key length issues and ensure uniqueness.

        Args:
            model: LLM model name
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to include in cache key

        Returns:
            Cache key string
        """
        # Create canonical representation of parameters
        params = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Sort keys for consistency
        canonical = json.dumps(params, sort_keys=True)

        # Hash to avoid key length issues
        hash_digest = hashlib.sha256(canonical.encode()).hexdigest()

        return f"{self.namespace}:{hash_digest}"

    async def get(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict | None:
        """Get cached LLM response.

        Args:
            model: LLM model name
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional cache key parameters

        Returns:
            Cached response dict or None if not found
        """
        cache_key = self._generate_cache_key(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        try:
            async with get_redis_client() as redis:
                cached_data = await redis.get(cache_key)

                if cached_data:
                    # Track cache hit
                    llm_cache_hits_total.labels(model=model).inc()

                    logger.debug(
                        "llm_cache_hit",
                        model=model,
                        cache_key=cache_key,
                        prompt_length=len(prompt),
                    )

                    return json.loads(cached_data)

                # Track cache miss
                llm_cache_misses_total.labels(model=model).inc()

                logger.debug(
                    "llm_cache_miss",
                    model=model,
                    cache_key=cache_key,
                    prompt_length=len(prompt),
                )

                return None

        except Exception as e:
            # Log error but don't fail - graceful degradation
            logger.warning(
                "llm_cache_get_error",
                model=model,
                error_type=type(e).__name__,
                error=str(e),
            )
            return None

    async def set(
        self,
        model: str,
        prompt: str,
        response: dict,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> bool:
        """Cache LLM response.

        Args:
            model: LLM model name
            prompt: Input prompt
            response: LLM response to cache
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional cache key parameters

        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._generate_cache_key(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        try:
            async with get_redis_client() as redis:
                # Serialize response
                serialized = json.dumps(response)

                # Store with TTL
                await redis.set(cache_key, serialized, ex=self.ttl)

                logger.debug(
                    "llm_cache_set",
                    model=model,
                    cache_key=cache_key,
                    ttl=self.ttl,
                    response_size=len(serialized),
                )

                return True

        except Exception as e:
            # Log error but don't fail
            logger.warning(
                "llm_cache_set_error",
                model=model,
                error_type=type(e).__name__,
                error=str(e),
            )
            return False

    async def get_or_compute(
        self,
        model: str,
        prompt: str,
        compute_fn: Callable[[], T],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """Get cached response or compute and cache it.

        This is the primary API for LLM caching.

        Args:
            model: LLM model name
            prompt: Input prompt
            compute_fn: Async function to compute response if cache miss
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional cache key parameters

        Returns:
            LLM response (from cache or computed)

        Example:
            >>> response = await cache.get_or_compute(
            ...     model="gpt-4-turbo",
            ...     prompt="Explain Python",
            ...     compute_fn=lambda: openai.chat.completions.create(...),
            ... )
        """
        # Try cache first
        cached = await self.get(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        if cached is not None:
            return cached

        # Cache miss - compute response
        logger.info(
            "llm_computing_response",
            model=model,
            prompt_length=len(prompt),
        )

        response = await compute_fn()

        # Cache for future use
        await self.set(
            model=model,
            prompt=prompt,
            response=response,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response

    async def invalidate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> bool:
        """Invalidate (delete) cached response.

        Args:
            model: LLM model name
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional cache key parameters

        Returns:
            True if deleted, False if not found
        """
        cache_key = self._generate_cache_key(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        try:
            async with get_redis_client() as redis:
                deleted = await redis.delete(cache_key)

                logger.debug(
                    "llm_cache_invalidated",
                    model=model,
                    cache_key=cache_key,
                    found=bool(deleted),
                )

                return bool(deleted)

        except Exception as e:
            logger.warning(
                "llm_cache_invalidate_error",
                model=model,
                error_type=type(e).__name__,
                error=str(e),
            )
            return False

    async def clear_all(self) -> int:
        """Clear all cached responses in this namespace.

        Returns:
            Number of keys deleted

        Warning:
            This is a destructive operation. Use with caution.
        """
        try:
            async with get_redis_client() as redis:
                # Find all keys with namespace prefix
                pattern = f"{self.namespace}:*"
                keys = []

                async for key in redis.scan_iter(match=pattern):
                    keys.append(key)

                if keys:
                    deleted = await redis.delete(*keys)
                    logger.info(
                        "llm_cache_cleared",
                        namespace=self.namespace,
                        keys_deleted=deleted,
                    )
                    return deleted

                return 0

        except Exception as e:
            logger.error(
                "llm_cache_clear_error",
                error_type=type(e).__name__,
                error=str(e),
            )
            return 0


# Global cache instance with default settings
_default_cache: LLMCache | None = None


def get_llm_cache(ttl: int = 3600) -> LLMCache:
    """Get or create the default LLM cache instance.

    Args:
        ttl: Time-to-live in seconds (default: 1 hour)

    Returns:
        LLM cache instance

    Example:
        >>> cache = get_llm_cache()
        >>> response = await cache.get_or_compute(...)
    """
    global _default_cache

    if _default_cache is None or _default_cache.ttl != ttl:
        _default_cache = LLMCache(ttl=ttl)

    return _default_cache
