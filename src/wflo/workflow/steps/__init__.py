"""Workflow step implementations.

This package provides different step types for building workflows:
- LLMStep: Call language model APIs (OpenAI, Anthropic, etc.)
- More step types coming soon (HTTP, Sandbox, Database, etc.)

Example:
    from wflo.workflow.steps import LLMStep, StepContext

    step = LLMStep(
        step_id="summarize",
        model="gpt-4",
        prompt_template="Summarize: {text}"
    )

    context = StepContext(
        execution_id="exec-123",
        step_execution_id="step-456",
        inputs={"text": "Long text..."},
        state={},
        config={}
    )

    result = await step.execute(context)
"""

from wflo.workflow.steps.base import Step, StepContext, StepResult
from wflo.workflow.steps.llm import LLMStep

__all__ = [
    "Step",
    "StepContext",
    "StepResult",
    "LLMStep",
]
