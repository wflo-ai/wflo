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
                    from wflo.cost.tracker import TokenUsage
                    from wflo.db.engine import get_session

                    token_usage = TokenUsage(
                        model=model,
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                    )
                    cost_usd = cost_tracker.calculate_cost(token_usage)

                    # Track in database and check budget
                    async for session in get_session():
                        await cost_tracker.track_cost(
                            session=session,
                            execution_id=execution_id,
                            usage=token_usage,
                        )
                        break  # Only need first iteration

                    # Check if budget exceeded after tracking cost
                    from wflo.sdk.context import get_current_budget
                    from sqlalchemy import select
                    from wflo.db.models import WorkflowExecutionModel, WorkflowDefinitionModel
                    from wflo.sdk.workflow import BudgetExceededError

                    # Try to get cached budget from context (performance optimization)
                    # Eliminates 1 DB query when budget is cached by WfloWorkflow
                    cached_budget = get_current_budget()

                    async for session in get_session():
                        # Get execution to find current cost
                        exec_result = await session.execute(
                            select(WorkflowExecutionModel).where(
                                WorkflowExecutionModel.id == execution_id
                            )
                        )
                        execution = exec_result.scalar_one_or_none()

                        if execution:
                            # Use cached budget if available, otherwise query workflow definition
                            budget = cached_budget
                            if budget is None:
                                # Fallback: query workflow definition for budget
                                # This maintains backward compatibility when decorator used directly
                                wf_result = await session.execute(
                                    select(WorkflowDefinitionModel).where(
                                        WorkflowDefinitionModel.id == execution.workflow_id
                                    )
                                )
                                workflow_def = wf_result.scalar_one_or_none()
                                if workflow_def and "budget_usd" in workflow_def.policies:
                                    budget = workflow_def.policies["budget_usd"]

                            # Check budget if available
                            if budget is not None and execution.cost_total_usd > budget:
                                raise BudgetExceededError(
                                    f"Budget exceeded: ${execution.cost_total_usd:.4f} > ${budget:.2f}",
                                    spent_usd=float(execution.cost_total_usd),
                                    budget_usd=budget,
                                )

                        break  # Only need first iteration

                    # Emit metrics
                    metrics.llm_api_calls_total.labels(model=model, status="success").inc()
                    metrics.llm_tokens_total.labels(model=model, token_type="input").inc(usage["prompt_tokens"])
                    metrics.llm_tokens_total.labels(model=model, token_type="output").inc(usage["completion_tokens"])
                    metrics.llm_cost_total_usd.labels(model=model).inc(float(cost_usd))

                    # Structured logging
                    logger.info(
                        "llm_call_completed",
                        execution_id=execution_id,
                        model=model,
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                        total_tokens=usage["total_tokens"],
                        cost_usd=round(float(cost_usd), 6),
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
                metrics.llm_api_calls_total.labels(model=model, status="error").inc()

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
