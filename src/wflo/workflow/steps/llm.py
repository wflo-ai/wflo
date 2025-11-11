"""LLM step for calling language model APIs.

This module provides the LLMStep class for executing LLM API calls
with automatic cost tracking, token counting, and error handling.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from wflo.workflow.steps.base import Step, StepContext, StepResult

logger = logging.getLogger(__name__)


class LLMStep(Step):
    """Step that calls an LLM API (OpenAI, Anthropic, etc.).

    Supports:
    - OpenAI models: GPT-5, GPT-4, GPT-3.5-turbo, o1, o3 series
    - Automatic cost tracking using tokencost library
    - Token counting for prompt and completion
    - Error handling and proper logging
    - Template-based prompt rendering
    - Model-specific parameter handling (max_completion_tokens, temperature)

    Model Compatibility:
        - GPT-5/o-series: Uses max_completion_tokens, temperature=1.0 only
        - GPT-4/GPT-3.5: Uses max_tokens, temperature 0-2 supported

    Example:
        # GPT-5 model (uses max_completion_tokens, no temperature customization)
        step = LLMStep(
            step_id="summarize",
            model="gpt-5-mini",
            prompt_template="Summarize this text: {input_text}",
            max_tokens=200
        )

        # GPT-4 model (uses max_tokens, temperature customizable)
        step = LLMStep(
            step_id="creative",
            model="gpt-4",
            prompt_template="Write a story about {topic}",
            max_tokens=500,
            temperature=0.9  # Supported for GPT-4
        )

        context = StepContext(
            execution_id="exec-123",
            step_execution_id="step-456",
            inputs={"input_text": "Long article here..."},
            state={},
            config={}
        )

        result = await step.execute(context)
        print(result.output["text"])  # AI-generated summary
        print(f"Cost: ${result.cost_usd}")
    """

    def __init__(
        self,
        step_id: str,
        model: str = "gpt-4",
        prompt_template: str = "{input}",
        system_prompt: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs,
    ):
        """Initialize LLM step.

        Args:
            step_id: Unique step identifier
            model: Model name (e.g., "gpt-5-mini", "gpt-4", "gpt-3.5-turbo")
            prompt_template: Template with {variables} for rendering
            system_prompt: Optional system message to set context
            max_tokens: Maximum completion tokens (name used for both max_tokens
                       and max_completion_tokens depending on model)
            temperature: Sampling temperature (0-2, default 0.7)
                        Note: GPT-5 and o-series models only support temperature=1.0
                        Custom values will be ignored with a warning
            **kwargs: Additional config passed to parent
        """
        super().__init__(step_id, **kwargs)
        self.model = model
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def execute(self, context: StepContext) -> StepResult:
        """Execute LLM API call.

        Renders the prompt template with context inputs, calls the OpenAI API,
        calculates cost, and returns the result with full metadata.

        Args:
            context: Step execution context with inputs

        Returns:
            StepResult: Execution result with LLM response and metadata
        """
        started_at = datetime.now()

        try:
            # Lazy import to avoid dependency issues
            from openai import AsyncOpenAI
            from wflo.cost.tracker import CostTracker

            # Render prompt template
            prompt = self._render_prompt(context.inputs)

            logger.info(
                f"Executing LLM step: {self.step_id}",
                extra={
                    "step_id": self.step_id,
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "max_tokens": self.max_tokens,
                },
            )

            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Get your API key from https://platform.openai.com/api-keys"
                )

            client = AsyncOpenAI(api_key=api_key)

            # Build messages
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Determine API parameter compatibility based on model
            # GPT-5 and o-series models have different requirements:
            #   - Use max_completion_tokens instead of max_tokens
            #   - Temperature must be omitted or set to 1 (default)
            # Older models (GPT-4, GPT-3.5, etc.):
            #   - Use max_tokens
            #   - Temperature range 0-2 is supported
            is_reasoning_model = (
                self.model.startswith("gpt-5")
                or self.model.startswith("o1")
                or self.model.startswith("o3")
            )

            # Build API parameters with model-appropriate settings
            api_params = {
                "model": self.model,
                "messages": messages,
            }

            # Add token limit parameter (model-specific)
            if is_reasoning_model:
                api_params["max_completion_tokens"] = self.max_tokens
                # Temperature for GPT-5/o-series: only default (1) is supported
                # Only include if explicitly set to 1, otherwise omit
                if self.temperature == 1.0:
                    api_params["temperature"] = 1.0
                # If user set a different value, log warning and omit parameter
                elif self.temperature != 0.7:  # 0.7 is our default
                    logger.warning(
                        f"Temperature {self.temperature} not supported for {self.model}. "
                        f"Using model default (1.0). "
                        f"GPT-5 and o-series models only support temperature=1.0"
                    )
            else:
                # Legacy models support max_tokens and full temperature range
                api_params["max_tokens"] = self.max_tokens
                api_params["temperature"] = self.temperature

            # Call OpenAI API
            logger.debug(
                f"Calling OpenAI API with parameters: {list(api_params.keys())}"
            )
            response = await client.chat.completions.create(**api_params)

            # Extract response data
            output_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost using CostTracker
            from wflo.cost.tracker import TokenUsage

            cost_tracker = CostTracker()
            usage = TokenUsage(
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            cost = cost_tracker.calculate_cost(usage)

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.info(
                f"LLM step completed: {self.step_id}",
                extra={
                    "step_id": self.step_id,
                    "cost_usd": float(cost),
                    "tokens": total_tokens,
                    "duration_seconds": duration,
                    "model": self.model,
                },
            )

            return StepResult(
                success=True,
                output={
                    "text": output_text,
                    "prompt": prompt,
                    "model": self.model,
                },
                cost_usd=float(cost),
                metadata={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "finish_reason": response.choices[0].finish_reason,
                    "model": self.model,
                    "temperature": self.temperature,
                },
                started_at=started_at,
                completed_at=completed_at,
            )

        except ImportError as e:
            logger.error(
                f"Failed to import required libraries: {e}",
                extra={"step_id": self.step_id},
            )
            return StepResult(
                success=False,
                output={},
                error=f"Missing required library: {e}. Run: pip install openai",
                started_at=started_at,
                completed_at=datetime.now(),
            )

        except ValueError as e:
            logger.error(
                f"Validation error in LLM step: {e}",
                extra={"step_id": self.step_id},
            )
            return StepResult(
                success=False,
                output={},
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now(),
            )

        except Exception as e:
            logger.error(
                f"LLM step failed: {self.step_id}",
                exc_info=e,
                extra={"step_id": self.step_id},
            )
            return StepResult(
                success=False,
                output={},
                error=f"LLM API call failed: {str(e)}",
                started_at=started_at,
                completed_at=datetime.now(),
            )

    def _render_prompt(self, inputs: Dict[str, Any]) -> str:
        """Render prompt template with inputs.

        Uses Python string formatting to replace {variable} placeholders
        with values from the inputs dictionary.

        Args:
            inputs: Input variables for template

        Returns:
            str: Rendered prompt

        Raises:
            ValueError: If required template variable is missing
        """
        try:
            return self.prompt_template.format(**inputs)
        except KeyError as e:
            raise ValueError(
                f"Missing required input variable for prompt template: {e}. "
                f"Template: {self.prompt_template}, "
                f"Available inputs: {list(inputs.keys())}"
            )

    async def validate(self, context: StepContext) -> bool:
        """Validate API key and inputs before execution.

        Checks that:
        1. OpenAI API key is set
        2. All required template variables are present in inputs

        Args:
            context: Step execution context

        Returns:
            bool: True if valid, False otherwise
        """
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable not set")
            return False

        # Check required inputs for template
        try:
            self._render_prompt(context.inputs)
            return True
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize LLM step to dictionary.

        Returns:
            dict: Step configuration with all parameters
        """
        return {
            **super().to_dict(),
            "model": self.model,
            "prompt_template": self.prompt_template,
            "system_prompt": self.system_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
