"""
Anthropic API Interceptor

Monkey-patches the Anthropic SDK to intercept all API calls.
"""

import functools
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..runtime import WfloRuntime


class AnthropicInterceptor:
    """Intercepts all Anthropic API calls."""

    def __init__(self, runtime: "WfloRuntime"):
        self.runtime = runtime
        self.original_create = None
        self.original_acreate = None
        self.patched = False

    def install(self):
        """Install the interceptor by monkey-patching Anthropic SDK."""
        try:
            from anthropic.resources import messages

            # Save original methods
            self.original_create = messages.Messages.create
            self.original_acreate = messages.AsyncMessages.create

            # Patch sync method
            messages.Messages.create = self._wrap_sync(self.original_create)

            # Patch async method
            messages.AsyncMessages.create = self._wrap_async(self.original_acreate)

            self.patched = True

        except ImportError:
            raise ImportError("Anthropic library not found or unsupported version")

    def uninstall(self):
        """Uninstall the interceptor by restoring original methods."""
        if not self.patched:
            return

        try:
            from anthropic.resources import messages

            if self.original_create:
                messages.Messages.create = self.original_create

            if self.original_acreate:
                messages.AsyncMessages.create = self.original_acreate

        except ImportError:
            pass

        self.patched = False

    def _wrap_sync(self, original_fn: Callable) -> Callable:
        """Wrap synchronous Anthropic call."""

        @functools.wraps(original_fn)
        def wrapper(*args, **kwargs):
            # Run the interception in an event loop
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            async def async_wrapper():
                return await self.runtime.intercept_call(
                    provider="anthropic",
                    method="messages.create",
                    args=args,
                    kwargs=kwargs,
                    original_fn=original_fn,
                )

            if loop.is_running():
                # Handle nested event loops
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_wrapper())
                    return future.result()
            else:
                return loop.run_until_complete(async_wrapper())

        return wrapper

    def _wrap_async(self, original_fn: Callable) -> Callable:
        """Wrap asynchronous Anthropic call."""

        @functools.wraps(original_fn)
        async def wrapper(*args, **kwargs):
            return await self.runtime.intercept_call(
                provider="anthropic",
                method="messages.create",
                args=args,
                kwargs=kwargs,
                original_fn=original_fn,
            )

        return wrapper
