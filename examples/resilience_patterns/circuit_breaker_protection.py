"""Example: Using CircuitBreaker to prevent cascading failures.

This example demonstrates how to use the circuit breaker pattern to protect
workflows from cascading failures when external services are degraded.

Run:
    python examples/resilience_patterns/circuit_breaker_protection.py
"""

import asyncio
import os
from datetime import datetime

from openai import AsyncOpenAI

from wflo.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker,
)
from wflo.sdk.workflow import WfloWorkflow


# Example 1: Basic Circuit Breaker Usage
async def example_basic_circuit_breaker():
    """Example showing circuit breaker basics."""
    print("\n=== Example 1: Basic Circuit Breaker ===\n")

    # Create circuit breaker for external service
    breaker = CircuitBreaker(
        name="openai-api",
        failure_threshold=3,  # Open circuit after 3 failures
        recovery_timeout=30.0,  # Try to recover after 30 seconds
        success_threshold=2,  # Close circuit after 2 successful calls
        expected_exception=(Exception,),  # Track all exceptions
    )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def call_openai():
        """Protected LLM API call."""
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi!"}],
            max_tokens=10,
        )
        return response.choices[0].message.content

    # Make several calls
    for i in range(5):
        try:
            result = await breaker.call(call_openai)
            print(f"✅ Call {i+1}: {result} (Circuit: {breaker.state.value})")
        except CircuitBreakerOpenError as e:
            print(f"⚡ Call {i+1}: Circuit OPEN - Failing fast! {e}")
        except Exception as e:
            print(f"❌ Call {i+1}: Error - {e} (Circuit: {breaker.state.value})")

    # Show circuit state
    state = breaker.get_state()
    print(f"\n📊 Circuit State: {state}")


# Example 2: Circuit Breaker Decorator
async def example_circuit_breaker_decorator():
    """Example using @circuit_breaker decorator."""
    print("\n=== Example 2: @circuit_breaker Decorator ===\n")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @circuit_breaker(
        name="llm-service",
        failure_threshold=2,
        recovery_timeout=10.0,
        expected_exception=(Exception,),
    )
    async def protected_llm_call(prompt: str):
        """LLM call protected by circuit breaker."""
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        return response.choices[0].message.content

    # Simulate normal operation
    try:
        result = await protected_llm_call("What is Python?")
        print(f"✅ Normal operation: {result[:50]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


# Example 3: Circuit Breaker in Workflow
async def example_workflow_with_circuit_breaker():
    """Example integrating circuit breaker with WfloWorkflow."""
    print("\n=== Example 3: Circuit Breaker in Workflow ===\n")

    workflow = WfloWorkflow(
        name="protected-workflow",
        budget_usd=1.0,
    )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Get shared circuit breaker (persists across workflow executions)
    breaker = get_circuit_breaker(
        name="workflow-llm-service",
        failure_threshold=3,
        recovery_timeout=60.0,
    )

    async def workflow_logic(questions: list):
        """Workflow that processes multiple questions."""
        results = []

        for question in questions:
            try:
                # Protected API call
                result = await breaker.call(
                    lambda q=question: client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": q}],
                        max_tokens=30,
                    )
                )
                answer = result.choices[0].message.content
                results.append({"question": question, "answer": answer, "status": "success"})
                print(f"✅ {question[:30]}... → {answer[:40]}...")

            except CircuitBreakerOpenError:
                # Circuit is open - fail fast
                results.append({"question": question, "answer": None, "status": "circuit_open"})
                print(f"⚡ {question[:30]}... → CIRCUIT OPEN (skipping)")

            except Exception as e:
                # Other errors
                results.append({"question": question, "answer": None, "status": f"error: {e}"})
                print(f"❌ {question[:30]}... → ERROR: {e}")

        return {"results": results, "circuit_state": breaker.state.value}

    try:
        result = await workflow.execute(
            workflow_logic,
            {
                "questions": [
                    "What is machine learning?",
                    "What is deep learning?",
                    "What is neural network?",
                ]
            },
        )
        print(f"\n📊 Workflow Result: {result}")
    except Exception as e:
        print(f"❌ Workflow error: {e}")


# Example 4: Circuit Breaker State Transitions
async def example_circuit_state_transitions():
    """Example demonstrating circuit breaker state machine."""
    print("\n=== Example 4: Circuit State Transitions ===\n")

    # Simulate failing service
    failure_count = {"count": 0}

    async def failing_service():
        """Service that fails first 3 times, then recovers."""
        failure_count["count"] += 1
        if failure_count["count"] <= 3:
            raise ConnectionError(f"Service unavailable (failure {failure_count['count']})")
        return f"Service recovered! (call {failure_count['count']})"

    breaker = CircuitBreaker(
        name="state-demo",
        failure_threshold=3,
        recovery_timeout=2.0,  # Short timeout for demo
        success_threshold=2,
        expected_exception=(ConnectionError,),
    )

    print(f"Initial state: {breaker.state.value}")

    # Phase 1: Trigger failures to open circuit
    print("\n📍 Phase 1: Triggering failures...")
    for i in range(3):
        try:
            await breaker.call(failing_service)
        except ConnectionError as e:
            print(f"  Failure {i+1}: {e} (State: {breaker.state.value})")

    print(f"\n⚡ Circuit opened! State: {breaker.state.value}")

    # Phase 2: Try while circuit is open (should fail fast)
    print("\n📍 Phase 2: Circuit open - failing fast...")
    try:
        await breaker.call(failing_service)
    except CircuitBreakerOpenError as e:
        print(f"  Fast fail: {e}")

    # Phase 3: Wait for recovery timeout
    print(f"\n📍 Phase 3: Waiting {breaker.recovery_timeout}s for recovery...")
    await asyncio.sleep(breaker.recovery_timeout + 0.1)

    # Phase 4: Attempt recovery (HALF_OPEN state)
    print("\n📍 Phase 4: Attempting recovery...")
    try:
        result = await breaker.call(failing_service)
        print(f"  Success 1: {result} (State: {breaker.state.value})")
    except Exception as e:
        print(f"  Error: {e}")

    # Phase 5: Second success closes circuit
    print("\n📍 Phase 5: Second success to close circuit...")
    try:
        result = await breaker.call(failing_service)
        print(f"  Success 2: {result} (State: {breaker.state.value})")
    except Exception as e:
        print(f"  Error: {e}")

    print(f"\n✅ Circuit closed! State: {breaker.state.value}")


# Example 5: Multiple Services with Separate Circuit Breakers
async def example_multiple_circuit_breakers():
    """Example with separate circuit breakers for different services."""
    print("\n=== Example 5: Multiple Circuit Breakers ===\n")

    # Each service gets its own circuit breaker
    openai_breaker = get_circuit_breaker(name="openai", failure_threshold=3)
    database_breaker = get_circuit_breaker(name="database", failure_threshold=5)
    cache_breaker = get_circuit_breaker(name="cache", failure_threshold=2)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def call_openai():
        return await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
        )

    async def call_database():
        # Simulate database call
        await asyncio.sleep(0.01)
        return {"user_id": 123, "name": "Alice"}

    async def call_cache():
        # Simulate cache call
        await asyncio.sleep(0.005)
        return {"cached_value": "some_data"}

    # Make protected calls
    try:
        llm_result = await openai_breaker.call(call_openai)
        db_result = await database_breaker.call(call_database)
        cache_result = await cache_breaker.call(call_cache)

        print(f"✅ OpenAI: {llm_result.choices[0].message.content} (Circuit: {openai_breaker.state.value})")
        print(f"✅ Database: {db_result} (Circuit: {database_breaker.state.value})")
        print(f"✅ Cache: {cache_result} (Circuit: {cache_breaker.state.value})")

    except CircuitBreakerOpenError as e:
        print(f"⚡ Circuit open: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("Circuit Breaker Examples - Preventing Cascading Failures")
    print("=" * 70)

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in environment")
        print("Set it with: export OPENAI_API_KEY='sk-...'")
        return

    # Run examples
    await example_basic_circuit_breaker()
    await example_circuit_breaker_decorator()
    await example_workflow_with_circuit_breaker()
    await example_circuit_state_transitions()
    await example_multiple_circuit_breakers()

    print("\n" + "=" * 70)
    print("✅ All circuit breaker examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
