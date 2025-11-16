"""
OpenAI API Interceptor

Monkey-patches the OpenAI SDK to intercept all API calls.
"""

import functools
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..runtime import WfloRuntime


class OpenAIInterceptor:
    """Intercepts all OpenAI API calls."""

    def __init__(self, runtime: "WfloRuntime"):
        self.runtime = runtime
        self.original_create = None
        self.original_acreate = None
        self.patched = False

    def install(self):
        """Install the interceptor by monkey-patching OpenAI SDK."""
        try:
            # Try OpenAI v1.0+ (new SDK structure)
            from openai.resources.chat import completions

            # Save original methods
            self.original_create = completions.Completions.create
            self.original_acreate = completions.AsyncCompletions.create

            # Patch sync method
            completions.Completions.create = self._wrap_sync(self.original_create)

            # Patch async method
            completions.AsyncCompletions.create = self._wrap_async(
                self.original_acreate
            )

            self.patched = True

        except ImportError:
            # Try OpenAI v0.x (old SDK structure)
            try:
                import openai

                self.original_create = openai.ChatCompletion.create
                openai.ChatCompletion.create = self._wrap_sync(self.original_create)

                self.patched = True
            except (ImportError, AttributeError):
                raise ImportError("OpenAI library not found or unsupported version")

    def uninstall(self):
        """Uninstall the interceptor by restoring original methods."""
        if not self.patched:
            return

        try:
            from openai.resources.chat import completions

            if self.original_create:
                completions.Completions.create = self.original_create

            if self.original_acreate:
                completions.AsyncCompletions.create = self.original_acreate

        except ImportError:
            try:
                import openai

                if self.original_create:
                    openai.ChatCompletion.create = self.original_create
            except (ImportError, AttributeError):
                pass

        self.patched = False

    def _wrap_sync(self, original_fn: Callable) -> Callable:
        """Wrap synchronous OpenAI call."""

        @functools.wraps(original_fn)
        def wrapper(*args, **kwargs):
            # Run the interception in an event loop
            import asyncio
            import inspect

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # For sync calls to original_fn that expect sync behavior
            # We need to handle async interception carefully
            async def async_wrapper():
                return await self.runtime.intercept_call(
                    provider="openai",
                    method="chat.completions.create",
                    args=args,
                    kwargs=kwargs,
                    original_fn=original_fn,
                )

            if loop.is_running():
                # If loop is already running, create a task
                # This handles nested event loops
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, async_wrapper()
                    )
                    return future.result()
            else:
                # Normal case: run in the loop
                return loop.run_until_complete(async_wrapper())

        return wrapper

    def _wrap_async(self, original_fn: Callable) -> Callable:
        """Wrap asynchronous OpenAI call."""

        @functools.wraps(original_fn)
        async def wrapper(*args, **kwargs):
            return await self.runtime.intercept_call(
                provider="openai",
                method="chat.completions.create",
                args=args,
                kwargs=kwargs,
                original_fn=original_fn,
            )

        return wrapper
