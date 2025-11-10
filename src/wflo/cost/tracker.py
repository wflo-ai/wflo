"""Cost tracking for LLM API usage.

This module provides functionality to track and calculate costs for LLM API calls,
supporting various models from OpenAI, Anthropic, and other providers.
"""

import logging
from dataclasses import dataclass
from typing import Any

import tiktoken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wflo.db.models import WorkflowExecutionModel

logger = logging.getLogger(__name__)


# Model pricing (as of 2024, in USD per 1K tokens)
MODEL_PRICING = {
    # OpenAI GPT-4 models
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-1106-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-0125-preview": {"prompt": 0.01, "completion": 0.03},
    # OpenAI GPT-3.5 models
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "gpt-3.5-turbo-1106": {"prompt": 0.001, "completion": 0.002},
    "gpt-3.5-turbo-0125": {"prompt": 0.0005, "completion": 0.0015},
    # Anthropic Claude models
    "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
    "claude-2.1": {"prompt": 0.008, "completion": 0.024},
    "claude-2.0": {"prompt": 0.008, "completion": 0.024},
    "claude-instant-1.2": {"prompt": 0.0008, "completion": 0.0024},
    # Other models (Llama, Mistral, etc.)
    "llama-2-70b": {"prompt": 0.0007, "completion": 0.0009},
    "llama-2-13b": {"prompt": 0.0002, "completion": 0.0003},
    "llama-2-7b": {"prompt": 0.0001, "completion": 0.0002},
    "mistral-7b": {"prompt": 0.0001, "completion": 0.0002},
    "mistral-8x7b": {"prompt": 0.0003, "completion": 0.0005},
}


@dataclass
class TokenUsage:
    """Token usage for an LLM API call.

    Attributes:
        model: Model name (e.g., "gpt-4", "claude-3-opus")
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
    """

    model: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        """Get total tokens (prompt + completion)."""
        return self.prompt_tokens + self.completion_tokens


class CostTracker:
    """Track costs for LLM API usage.

    This class provides functionality to:
    - Calculate costs based on token usage and model pricing
    - Track costs in the database
    - Estimate costs for prompts before execution
    - Check budget limits

    Example:
        tracker = CostTracker()
        usage = TokenUsage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )
        cost = tracker.calculate_cost(usage)
        print(f"Cost: ${cost:.4f}")
    """

    def __init__(self) -> None:
        """Initialize cost tracker."""
        self._model_pricing = MODEL_PRICING
        self._encoders = {}  # Cache tiktoken encoders

    def calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost for a token usage.

        Args:
            usage: Token usage information

        Returns:
            float: Cost in USD

        Raises:
            ValueError: If model pricing is not available
        """
        model = self._normalize_model_name(usage.model)

        if model not in self._model_pricing:
            logger.warning(
                f"Model pricing not found for {model}, using GPT-4 as fallback"
            )
            model = "gpt-4"

        pricing = self._model_pricing[model]

        prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1000) * pricing["completion"]

        total_cost = prompt_cost + completion_cost

        logger.debug(
            f"Calculated cost for {model}",
            extra={
                "model": model,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": total_cost,
            },
        )

        return total_cost

    async def track_cost(
        self,
        session: AsyncSession,
        execution_id: str,
        usage: TokenUsage,
        step_execution_id: str | None = None,
    ) -> None:
        """Track cost in the database.

        Args:
            session: Database session
            execution_id: Workflow execution ID
            usage: Token usage information
            step_execution_id: Optional step execution ID for step-level tracking
        """
        cost = self.calculate_cost(usage)

        logger.info(
            f"Tracking cost for execution {execution_id}",
            extra={
                "execution_id": execution_id,
                "model": usage.model,
                "cost_usd": cost,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
            },
        )

        # Update workflow execution costs
        result = await session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == execution_id
            )
        )
        execution = result.scalar_one()

        execution.cost_total_usd += cost
        execution.cost_prompt_tokens += usage.prompt_tokens
        execution.cost_completion_tokens += usage.completion_tokens

        # Update step execution costs if provided
        if step_execution_id:
            from wflo.db.models import StepExecutionModel

            result = await session.execute(
                select(StepExecutionModel).where(
                    StepExecutionModel.id == step_execution_id
                )
            )
            step_execution = result.scalar_one()

            step_execution.cost_usd += cost
            step_execution.prompt_tokens += usage.prompt_tokens
            step_execution.completion_tokens += usage.completion_tokens

        await session.commit()

    def estimate_cost(
        self,
        model: str,
        prompt: str,
        max_completion_tokens: int = 500,
    ) -> float:
        """Estimate cost for a prompt before execution.

        Args:
            model: Model name
            prompt: Prompt text
            max_completion_tokens: Maximum completion tokens to generate

        Returns:
            float: Estimated cost in USD
        """
        # Count tokens in prompt
        prompt_tokens = self.count_tokens(prompt, model)

        # Create usage estimate
        usage = TokenUsage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=max_completion_tokens,
        )

        cost = self.calculate_cost(usage)

        logger.debug(
            f"Estimated cost for prompt",
            extra={
                "model": model,
                "prompt_tokens": prompt_tokens,
                "max_completion_tokens": max_completion_tokens,
                "estimated_cost": cost,
            },
        )

        return cost

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text for a given model.

        Args:
            text: Text to count tokens for
            model: Model name (for encoding)

        Returns:
            int: Number of tokens
        """
        model = self._normalize_model_name(model)

        # Get or create encoder for model
        if model not in self._encoders:
            try:
                # Try to get encoding for model
                if model.startswith("gpt-4"):
                    encoding_name = "cl100k_base"
                elif model.startswith("gpt-3.5"):
                    encoding_name = "cl100k_base"
                elif model.startswith("claude"):
                    # Claude uses similar tokenization to GPT-4
                    encoding_name = "cl100k_base"
                else:
                    # Default to GPT-4 encoding
                    encoding_name = "cl100k_base"

                self._encoders[model] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.warning(
                    f"Failed to get encoder for {model}, using cl100k_base: {e}"
                )
                self._encoders[model] = tiktoken.get_encoding("cl100k_base")

        encoder = self._encoders[model]
        tokens = encoder.encode(text)

        return len(tokens)

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name to match pricing keys.

        Args:
            model: Original model name

        Returns:
            str: Normalized model name
        """
        # Remove version suffixes if not in pricing table
        if model in self._model_pricing:
            return model

        # Try to find base model name
        for base_model in self._model_pricing.keys():
            if model.startswith(base_model):
                return base_model

        # Return original if no match found
        return model


async def check_budget(
    session: AsyncSession,
    execution_id: str,
    max_cost_usd: float,
) -> bool:
    """Check if workflow execution is within budget.

    Args:
        session: Database session
        execution_id: Workflow execution ID
        max_cost_usd: Maximum allowed cost in USD

    Returns:
        bool: True if within budget, False otherwise
    """
    result = await session.execute(
        select(WorkflowExecutionModel).where(WorkflowExecutionModel.id == execution_id)
    )
    execution = result.scalar_one()

    current_cost = execution.cost_total_usd
    within_budget = current_cost <= max_cost_usd

    logger.info(
        f"Budget check for execution {execution_id}",
        extra={
            "execution_id": execution_id,
            "current_cost": current_cost,
            "max_cost": max_cost_usd,
            "within_budget": within_budget,
        },
    )

    return within_budget
