"""Example: Using RetryManager with LLM API calls.

This example demonstrates how to use the retry pattern to handle
transient failures when calling LLM APIs (rate limits, timeouts, etc.).

Run:
    python examples/resilience_patterns/retry_with_llm.py
"""

import asyncio
import os

from openai import AsyncOpenAI

from wflo.resilience.retry import RetryManager, RetryStrategy, retry_with_backoff
from wflo.sdk.decorators.track_llm import track_llm_call
from wflo.sdk.workflow import WfloWorkflow


# Example 1: Using RetryManager directly
async def example_retry_manager():
    """Example using RetryManager to handle API rate limits."""
    print("\n=== Example 1: RetryManager with LLM API ===\n")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create retry manager for API calls
    retry_manager = RetryManager(
        max_retries=3,
        base_delay=1.0,  # Start with 1 second
        max_delay=30.0,  # Cap at 30 seconds
        multiplier=2.0,  # Exponential backoff: 1s, 2s, 4s, 8s...
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=True,  # Add randomness to prevent thundering herd
    )

    async def call_openai_api(prompt: str):
        """LLM API call that might fail."""
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return response.choices[0].message.content

    # Execute with retry protection
    try:
        result = await retry_manager.execute(
            call_openai_api,
            "What is the capital of France?",
            retryable_exceptions=(
                Exception,  # Retry on any exception (timeouts, rate limits, etc.)
            ),
        )
        print(f"✅ Success after retries: {result}")
    except Exception as e:
        print(f"❌ Failed after all retries: {e}")


# Example 2: Using @retry_with_backoff decorator
async def example_retry_decorator():
    """Example using decorator for cleaner code."""
    print("\n=== Example 2: @retry_with_backoff Decorator ===\n")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retryable_exceptions=(Exception,),
    )
    @track_llm_call(model="gpt-4")  # Combine with cost tracking
    async def ask_llm(question: str):
        """LLM call with automatic retry on failures."""
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}],
            max_tokens=50,
        )
        return response

    try:
        result = await ask_llm("What is 2+2?")
        print(f"✅ LLM Response: {result.choices[0].message.content}")
    except Exception as e:
        print(f"❌ LLM call failed: {e}")


# Example 3: Retry in WfloWorkflow
async def example_workflow_with_retry():
    """Example integrating retry with WfloWorkflow."""
    print("\n=== Example 3: Retry in WfloWorkflow ===\n")

    workflow = WfloWorkflow(
        name="llm-workflow-with-retry",
        budget_usd=1.0,
    )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @retry_with_backoff(
        max_retries=3,
        base_delay=0.5,
        strategy=RetryStrategy.LINEAR,  # Linear backoff: 0.5s, 1.0s, 1.5s
    )
    async def generate_summary(text: str):
        """Generate summary with retry protection."""
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Summarize the following text in one sentence."},
                {"role": "user", "content": text},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content

    async def workflow_logic(text: str):
        """Workflow that uses retry-protected LLM call."""
        summary = await generate_summary(text)
        return {"summary": summary}

    try:
        result = await workflow.execute(
            workflow_logic,
            {
                "text": "Artificial intelligence is transforming how we work and live. "
                "Machine learning enables computers to learn from data without explicit programming."
            },
        )
        print(f"✅ Workflow completed: {result}")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")


# Example 4: Custom retry callback
async def example_retry_with_callback():
    """Example with callback to monitor retry attempts."""
    print("\n=== Example 4: Retry with Monitoring Callback ===\n")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    retry_attempts = []

    def on_retry(attempt: int, exception: Exception):
        """Called before each retry attempt."""
        retry_attempts.append({"attempt": attempt, "error": str(exception)})
        print(f"⚠️  Retry attempt {attempt + 1} after error: {exception}")

    retry_manager = RetryManager(
        max_retries=2,
        base_delay=0.5,
        strategy=RetryStrategy.FIXED,
    )

    async def flaky_llm_call():
        """Simulate flaky API (fails first time, succeeds second)."""
        if len(retry_attempts) == 0:
            raise ConnectionError("Simulated network timeout")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=20,
        )
        return response.choices[0].message.content

    try:
        result = await retry_manager.execute(
            flaky_llm_call,
            retryable_exceptions=(ConnectionError,),
            on_retry=on_retry,
        )
        print(f"✅ Success: {result}")
        print(f"📊 Total retries: {len(retry_attempts)}")
    except Exception as e:
        print(f"❌ Failed: {e}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("RetryManager Examples - Handling LLM API Failures")
    print("=" * 60)

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in environment")
        print("Set it with: export OPENAI_API_KEY='sk-...'")
        return

    # Run examples
    await example_retry_manager()
    await example_retry_decorator()
    await example_workflow_with_retry()
    await example_retry_with_callback()

    print("\n" + "=" * 60)
    print("✅ All retry examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
