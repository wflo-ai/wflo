"""
Self-Healing - Automatic Recovery from Failures
"""

import asyncio
import time
from typing import Any, Callable, Optional

from .config import WfloConfig


class SelfHealer:
    """Automatically recover from common LLM API failures."""

    # Model fallbacks by provider
    MODEL_FALLBACKS = {
        "openai": {
            "gpt-4": "gpt-3.5-turbo",
            "gpt-4-turbo": "gpt-3.5-turbo",
            "gpt-4-turbo-preview": "gpt-3.5-turbo",
        },
        "anthropic": {
            "claude-3-opus-20240229": "claude-3-sonnet-20240229",
            "claude-3-sonnet-20240229": "claude-3-haiku-20240307",
        },
    }

    def __init__(self, config: WfloConfig):
        self.config = config
        self.retry_attempt = 0

    async def heal(
        self,
        error: Exception,
        provider: str,
        args: tuple,
        kwargs: dict,
        original_fn: Callable,
    ) -> Optional[Any]:
        """
        Attempt to heal from error and retry execution.

        Healing strategies:
        1. Rate limit → Wait and retry
        2. Model overloaded → Switch to backup model
        3. Timeout → Reduce max_tokens and retry
        4. Authentication → Re-authenticate (if credentials available)
        5. Generic → Exponential backoff retry

        Args:
            error: The exception that was raised
            provider: Provider name (openai, anthropic, etc.)
            args: Original function args
            kwargs: Original function kwargs
            original_fn: Original function to retry

        Returns:
            Result from healed execution, or None if healing failed
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Strategy 1: Rate limit error
        if "rate" in error_str or "429" in error_str or "ratelimit" in error_str:
            return await self._heal_rate_limit(original_fn, args, kwargs)

        # Strategy 2: Model overloaded/unavailable
        elif (
            "overloaded" in error_str
            or "503" in error_str
            or "unavailable" in error_str
            or "capacity" in error_str
        ):
            return await self._heal_model_overload(
                provider, original_fn, args, kwargs
            )

        # Strategy 3: Timeout
        elif "timeout" in error_str or "timed out" in error_str:
            return await self._heal_timeout(original_fn, args, kwargs)

        # Strategy 4: Context length exceeded
        elif "context" in error_str and "length" in error_str:
            return await self._heal_context_length(original_fn, args, kwargs)

        # Strategy 5: Generic retry with backoff
        elif self.retry_attempt < self.config.max_retry_attempts:
            return await self._heal_generic_retry(original_fn, args, kwargs)

        # No healing strategy available
        return None

    async def _heal_rate_limit(
        self, original_fn: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Heal rate limit error by waiting."""
        if not self.config.silent:
            print("   ⏳ Rate limit detected")

        # Wait with exponential backoff
        wait_time = self.config.retry_initial_delay_seconds * (
            self.config.retry_backoff_multiplier**self.retry_attempt
        )
        wait_time = min(wait_time, 60)  # Cap at 60 seconds

        if not self.config.silent:
            print(f"   ⏳ Waiting {wait_time:.1f}s before retry...")

        await asyncio.sleep(wait_time)

        if not self.config.silent:
            print("   🔄 Retrying...")

        self.retry_attempt += 1

        # Retry
        import inspect

        if inspect.iscoroutinefunction(original_fn):
            return await original_fn(*args, **kwargs)
        else:
            return original_fn(*args, **kwargs)

    async def _heal_model_overload(
        self, provider: str, original_fn: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Heal model overload by switching to backup model."""
        current_model = kwargs.get("model", "")

        # Get fallback model
        fallback_model = self.MODEL_FALLBACKS.get(provider, {}).get(current_model)

        if fallback_model:
            if not self.config.silent:
                print(f"   🔄 Model overloaded, switching to: {fallback_model}")

            kwargs = kwargs.copy()
            kwargs["model"] = fallback_model

            # Retry with backup model
            import inspect

            if inspect.iscoroutinefunction(original_fn):
                return await original_fn(*args, **kwargs)
            else:
                return original_fn(*args, **kwargs)

        return None

    async def _heal_timeout(
        self, original_fn: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Heal timeout by reducing max_tokens."""
        if "max_tokens" in kwargs:
            original_max = kwargs["max_tokens"]
            new_max = max(100, original_max // 2)  # Reduce by half, min 100

            if not self.config.silent:
                print(f"   ⚡ Timeout detected, reducing tokens: {original_max} → {new_max}")

            kwargs = kwargs.copy()
            kwargs["max_tokens"] = new_max

            # Retry with reduced tokens
            import inspect

            if inspect.iscoroutinefunction(original_fn):
                return await original_fn(*args, **kwargs)
            else:
                return original_fn(*args, **kwargs)

        return None

    async def _heal_context_length(
        self, original_fn: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Heal context length error by truncating messages."""
        if "messages" in kwargs:
            messages = kwargs["messages"]

            if len(messages) > 2:
                # Keep system message + last message only
                system_msgs = [m for m in messages if m.get("role") == "system"]
                last_msg = messages[-1]

                new_messages = system_msgs + [last_msg]

                if not self.config.silent:
                    print(
                        f"   ✂️  Context too long, truncating: "
                        f"{len(messages)} → {len(new_messages)} messages"
                    )

                kwargs = kwargs.copy()
                kwargs["messages"] = new_messages

                # Retry with truncated context
                import inspect

                if inspect.iscoroutinefunction(original_fn):
                    return await original_fn(*args, **kwargs)
                else:
                    return original_fn(*args, **kwargs)

        return None

    async def _heal_generic_retry(
        self, original_fn: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Generic retry with exponential backoff."""
        self.retry_attempt += 1

        if not self.config.silent:
            print(
                f"   🔄 Retrying (attempt {self.retry_attempt}/"
                f"{self.config.max_retry_attempts})..."
            )

        # Wait with exponential backoff
        wait_time = self.config.retry_initial_delay_seconds * (
            self.config.retry_backoff_multiplier ** (self.retry_attempt - 1)
        )

        await asyncio.sleep(wait_time)

        # Retry
        import inspect

        if inspect.iscoroutinefunction(original_fn):
            return await original_fn(*args, **kwargs)
        else:
            return original_fn(*args, **kwargs)
