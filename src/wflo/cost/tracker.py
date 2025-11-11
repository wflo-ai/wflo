"""Cost tracking for LLM API usage.

This module provides functionality to track and calculate costs for LLM API calls,
supporting 400+ models from OpenAI, Anthropic, and other providers via tokencost library.
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tokencost import calculate_cost_by_tokens, calculate_prompt_cost, count_string_tokens

from wflo.db.models import WorkflowExecutionModel

logger = logging.getLogger(__name__)


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
    """Track costs for LLM API usage using tokencost library.

    This class provides functionality to:
    - Calculate costs based on token usage (400+ models supported)
    - Track costs in the database
    - Estimate costs for prompts before execution
    - Check budget limits

    Uses tokencost library for automatic model pricing updates.

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

    def calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost for a token usage using tokencost library.

        Args:
            usage: Token usage information

        Returns:
            float: Cost in USD

        Raises:
            ValueError: If model pricing is not available in tokencost
        """
        try:
            # Calculate input (prompt) cost
            input_cost = calculate_cost_by_tokens(
                num_tokens=usage.prompt_tokens,
                model=usage.model,
                token_type="input",
            )

            # Calculate output (completion) cost
            output_cost = calculate_cost_by_tokens(
                num_tokens=usage.completion_tokens,
                model=usage.model,
                token_type="output",
            )

            total_cost = input_cost + output_cost

            logger.debug(
                f"Calculated cost for {usage.model}",
                extra={
                    "model": usage.model,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "input_cost": input_cost,
                    "output_cost": output_cost,
                    "total_cost": total_cost,
                },
            )

            return total_cost

        except Exception as e:
            logger.error(
                f"Failed to calculate cost for model {usage.model}: {e}",
                extra={"model": usage.model, "error": str(e)},
            )
            raise ValueError(
                f"Model '{usage.model}' not supported by tokencost. "
                f"Check https://github.com/AgentOps-AI/tokencost for supported models."
            ) from e

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

        execution.cost_total_usd += float(cost)
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

            step_execution.cost_usd += float(cost)
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
        # Count tokens in prompt using tokencost
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
        """Count tokens in text for a given model using tokencost.

        Args:
            text: Text to count tokens for
            model: Model name (for encoding)

        Returns:
            int: Number of tokens
        """
        try:
            return count_string_tokens(text, model)
        except Exception as e:
            logger.warning(
                f"Failed to count tokens for model {model}, falling back to GPT-4: {e}"
            )
            # Fallback to GPT-4 tokenizer if model not supported
            return count_string_tokens(text, "gpt-4")


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
