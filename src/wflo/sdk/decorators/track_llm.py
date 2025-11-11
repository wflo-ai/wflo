"""LLM call tracking decorator for automatic cost and usage tracking."""

import time
from functools import wraps
from typing import Any, Callable, Optional
import structlog

from wflo.cost import CostTracker
from wflo.observability import metrics

logger = structlog.get_logger()


def track_llm_call(model: str):
    """
    Decorator to automatically track LLM API calls.

    Tracks:
    - Input/output tokens
    - Cost in USD
    - Latency in milliseconds
    - Model used
    - Success/failure

    Usage:
        @track_llm_call(model="gpt-4")
        async def call_openai(messages):
            return await client.chat.completions.create(...)

        @track_llm_call(model="claude-3-5-sonnet-20241022")
        async def call_anthropic(messages):
            return await client.messages.create(...)

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-5-sonnet-20241022")

    Returns:
        Decorated async function that tracks LLM usage
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get execution context
            from wflo.sdk.context import get_current_execution_id

            execution_id = get_current_execution_id()
            start_time = time.time()

            # Initialize cost tracker
            cost_tracker = CostTracker()

            try:
                # Execute the LLM call
                response = await func(*args, **kwargs)

                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000

                # Extract token usage from response
                usage = _extract_usage(response, model)

                if usage:
                    # Track cost in database
                    cost_usd = await cost_tracker.track_llm_call(
                        execution_id=execution_id,
                        provider=_get_provider_from_model(model),
                        model=model,
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                    )

                    # Emit metrics
                    metrics.histogram("llm_call_duration_ms", latency_ms, tags={"model": model})
                    metrics.counter(
                        "llm_call_tokens_total",
                        usage["total_tokens"],
                        tags={"model": model, "type": "total"},
                    )
                    metrics.counter(
                        "llm_call_cost_usd", cost_usd, tags={"model": model}
                    )
                    metrics.counter("llm_calls_total", 1, tags={"model": model, "status": "success"})

                    # Structured logging
                    logger.info(
                        "llm_call_completed",
                        execution_id=execution_id,
                        model=model,
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                        total_tokens=usage["total_tokens"],
                        cost_usd=round(cost_usd, 6),
                        latency_ms=round(latency_ms, 2),
                    )
                else:
                    logger.warning(
                        "llm_call_no_usage",
                        execution_id=execution_id,
                        model=model,
                        message="Could not extract usage from response",
                    )

                return response

            except Exception as e:
                # Track error
                latency_ms = (time.time() - start_time) * 1000
                metrics.counter("llm_calls_total", 1, tags={"model": model, "status": "error"})

                logger.error(
                    "llm_call_failed",
                    execution_id=execution_id,
                    model=model,
                    error=str(e),
                    error_type=type(e).__name__,
                    latency_ms=round(latency_ms, 2),
                )

                raise

        return wrapper

    return decorator


def _extract_usage(response: Any, model: str) -> Optional[dict]:
    """
    Extract token usage from LLM response.

    Handles different response formats from various providers.

    Args:
        response: LLM API response object
        model: Model identifier

    Returns:
        Dict with prompt_tokens, completion_tokens, total_tokens or None
    """
    # OpenAI format
    if hasattr(response, "usage"):
        usage = response.usage
        if hasattr(usage, "prompt_tokens"):
            return {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }

    # Anthropic Claude format
    if hasattr(response, "usage"):
        usage = response.usage
        if hasattr(usage, "input_tokens"):
            return {
                "prompt_tokens": usage.input_tokens,
                "completion_tokens": usage.output_tokens,
                "total_tokens": usage.input_tokens + usage.output_tokens,
            }

    # Dict format (for testing or custom wrappers)
    if isinstance(response, dict) and "usage" in response:
        usage = response["usage"]
        if "prompt_tokens" in usage:
            return {
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
            }
        elif "input_tokens" in usage:
            return {
                "prompt_tokens": usage["input_tokens"],
                "completion_tokens": usage["output_tokens"],
                "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            }

    return None


def _get_provider_from_model(model: str) -> str:
    """
    Extract provider name from model identifier.

    Args:
        model: Model identifier

    Returns:
        Provider name (e.g., "openai", "anthropic")
    """
    model_lower = model.lower()

    if any(x in model_lower for x in ["gpt", "o1", "o3"]):
        return "openai"
    elif "claude" in model_lower:
        return "anthropic"
    elif "gemini" in model_lower:
        return "google"
    elif "llama" in model_lower:
        return "meta"
    elif "mistral" in model_lower:
        return "mistral"
    else:
        # Default to first part of model name
        return model.split("-")[0].lower()
