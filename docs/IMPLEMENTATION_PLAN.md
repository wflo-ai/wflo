# Wflo Implementation Plan - Working OpenAI Example

**Date**: 2025-11-11
**Branch**: `claude/explore-repository-structure-011CV1P2D1ahjod1A8LQ6QxE`
**Goal**: Create working end-to-end example with OpenAI integration
**Timeline**: 3 days
**Status**: In Progress

---

## Overview

This plan details the implementation of a complete, working example that demonstrates Wflo's core capabilities with OpenAI integration. This is the **highest priority** task as it validates the entire architecture and enables all future development.

---

## Implementation Checklist

### Day 1: Sandbox & Foundation (6-8 hours)

#### ✅ Morning: Documentation & Structure (COMPLETED)
- [x] Create comprehensive assessment document
- [x] Create examples folder structure
- [x] Create Dockerfile.python311
- [x] Create example README
- [x] Commit and push

#### ⏳ Afternoon: Sandbox Runtime (IN PROGRESS)

**Task 1.1: Build Docker Image** (30 minutes)
- [ ] Build wflo/runtime:python3.11 image
- [ ] Test image can run Python
- [ ] Verify openai package installed
- [ ] Tag image properly

```bash
# Build command
docker build -t wflo/runtime:python3.11 -f docker/Dockerfile.python311 .

# Test command
docker run --rm wflo/runtime:python3.11 python -c "import openai; print('OK')"
```

**Task 1.2: Fix Sandbox Runtime Bug** (2-3 hours)
- [ ] Read runtime.py around line 210
- [ ] Identify UnboundLocalError source
- [ ] Fix variable scoping issue
- [ ] Add error handling improvements
- [ ] Run sandbox integration tests
- [ ] Verify 27/27 tests pass

**Files to Modify:**
- `src/wflo/sandbox/runtime.py` (line 210 area)

**Expected Issue:**
```python
# Likely issue pattern:
try:
    container = ...
    result = container.wait()
except Exception:
    # Bug: 'container' not defined if error occurs before assignment
    await container.delete()  # ← UnboundLocalError here
```

**Fix Pattern:**
```python
container = None
try:
    container = ...
    result = container.wait()
except Exception:
    if container is not None:
        await container.delete()
```

**Task 1.3: Verify Sandbox Tests** (30 minutes)
- [ ] Run: `poetry run pytest tests/integration/test_sandbox.py -v`
- [ ] All 27 tests should pass
- [ ] Fix any remaining issues
- [ ] Commit fixes

---

### Day 2: LLM Integration (6-8 hours)

#### Morning: Step Type System (3-4 hours)

**Task 2.1: Create Step Base Classes** (1 hour)

Create new directory structure:
```
src/wflo/workflow/
└── steps/
    ├── __init__.py
    ├── base.py          ← Base Step class
    ├── llm.py           ← LLM step implementation
    ├── http.py          ← HTTP step (future)
    └── sandbox.py       ← Sandbox step (future)
```

**File: `src/wflo/workflow/steps/base.py`**
```python
"""Base classes for workflow steps."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4


@dataclass
class StepContext:
    """Context passed to step execution.

    Attributes:
        execution_id: Workflow execution ID
        step_execution_id: This step's execution ID
        inputs: Input data for the step
        state: Current workflow state
        config: Configuration for the step
    """
    execution_id: str
    step_execution_id: str
    inputs: Dict[str, Any]
    state: Dict[str, Any]
    config: Dict[str, Any]


@dataclass
class StepResult:
    """Result of step execution.

    Attributes:
        success: Whether step succeeded
        output: Step output data
        error: Error message if failed
        cost_usd: Cost incurred (if applicable)
        metadata: Additional metadata
        started_at: Execution start time
        completed_at: Execution completion time
    """
    success: bool
    output: Dict[str, Any]
    error: str | None = None
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.completed_at is None:
            self.completed_at = datetime.now()


class Step(ABC):
    """Base class for all workflow steps.

    Subclasses must implement execute() method.
    """

    def __init__(self, step_id: str, **kwargs):
        """Initialize step.

        Args:
            step_id: Unique step identifier
            **kwargs: Step-specific configuration
        """
        self.step_id = step_id
        self.config = kwargs

    @abstractmethod
    async def execute(self, context: StepContext) -> StepResult:
        """Execute the step.

        Args:
            context: Step execution context

        Returns:
            StepResult: Execution result

        Raises:
            Exception: If step execution fails
        """
        raise NotImplementedError

    async def validate(self, context: StepContext) -> bool:
        """Validate step can execute with given context.

        Args:
            context: Step execution context

        Returns:
            bool: True if valid, False otherwise
        """
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step to dictionary.

        Returns:
            dict: Step configuration
        """
        return {
            "type": self.__class__.__name__,
            "step_id": self.step_id,
            "config": self.config
        }
```

**Task 2.2: Implement LLM Step** (2-3 hours)

**File: `src/wflo/workflow/steps/llm.py`**
```python
"""LLM step for calling language model APIs."""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from openai import AsyncOpenAI

from wflo.cost.tracker import CostTracker
from wflo.workflow.steps.base import Step, StepContext, StepResult

logger = logging.getLogger(__name__)


class LLMStep(Step):
    """Step that calls an LLM API (OpenAI, Anthropic, etc.).

    Supports:
    - OpenAI (GPT-4, GPT-3.5-turbo)
    - Automatic cost tracking
    - Token counting
    - Error handling and retries

    Example:
        step = LLMStep(
            step_id="summarize",
            model="gpt-4",
            prompt_template="Summarize: {input_text}",
            max_tokens=200
        )
    """

    def __init__(
        self,
        step_id: str,
        model: str = "gpt-4",
        prompt_template: str = "{input}",
        system_prompt: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ):
        """Initialize LLM step.

        Args:
            step_id: Unique step identifier
            model: Model name (e.g., "gpt-4")
            prompt_template: Template with {variables}
            system_prompt: Optional system message
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature (0-2)
            **kwargs: Additional config
        """
        super().__init__(step_id, **kwargs)
        self.model = model
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cost_tracker = CostTracker()

    async def execute(self, context: StepContext) -> StepResult:
        """Execute LLM API call.

        Args:
            context: Step execution context

        Returns:
            StepResult: Execution result with LLM response
        """
        started_at = datetime.now()

        try:
            # Render prompt template
            prompt = self._render_prompt(context.inputs)

            logger.info(
                f"Executing LLM step: {self.step_id}",
                extra={
                    "step_id": self.step_id,
                    "model": self.model,
                    "prompt_length": len(prompt)
                }
            )

            # Call OpenAI API
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            messages = []
            if self.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Extract response
            output_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            # Calculate cost
            cost = self.cost_tracker.calculate_cost(
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.info(
                f"LLM step completed: {self.step_id}",
                extra={
                    "step_id": self.step_id,
                    "cost_usd": float(cost),
                    "tokens": prompt_tokens + completion_tokens,
                    "duration_seconds": duration
                }
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
                    "total_tokens": prompt_tokens + completion_tokens,
                    "finish_reason": response.choices[0].finish_reason,
                },
                started_at=started_at,
                completed_at=completed_at
            )

        except Exception as e:
            logger.error(
                f"LLM step failed: {self.step_id}",
                exc_info=e,
                extra={"step_id": self.step_id}
            )

            return StepResult(
                success=False,
                output={},
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )

    def _render_prompt(self, inputs: Dict[str, Any]) -> str:
        """Render prompt template with inputs.

        Args:
            inputs: Input variables

        Returns:
            str: Rendered prompt
        """
        try:
            return self.prompt_template.format(**inputs)
        except KeyError as e:
            raise ValueError(
                f"Missing required input variable: {e}"
            )

    async def validate(self, context: StepContext) -> bool:
        """Validate API key and inputs.

        Args:
            context: Step execution context

        Returns:
            bool: True if valid
        """
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not set")
            return False

        # Check required inputs
        try:
            self._render_prompt(context.inputs)
            return True
        except ValueError:
            return False
```

**Task 2.3: Add to __init__.py** (5 minutes)

**File: `src/wflo/workflow/steps/__init__.py`**
```python
"""Workflow step implementations."""

from wflo.workflow.steps.base import Step, StepContext, StepResult
from wflo.workflow.steps.llm import LLMStep

__all__ = [
    "Step",
    "StepContext",
    "StepResult",
    "LLMStep",
]
```

**Task 2.4: Write Unit Tests** (1 hour)

**File: `tests/unit/test_llm_step.py`**
```python
"""Unit tests for LLM step."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from wflo.workflow.steps import LLMStep, StepContext


@pytest.mark.unit
class TestLLMStep:
    """Test LLM step implementation."""

    def test_init(self):
        """Test LLM step initialization."""
        step = LLMStep(
            step_id="test-step",
            model="gpt-4",
            prompt_template="Hello {name}"
        )

        assert step.step_id == "test-step"
        assert step.model == "gpt-4"
        assert step.prompt_template == "Hello {name}"

    def test_render_prompt(self):
        """Test prompt template rendering."""
        step = LLMStep(
            step_id="test",
            prompt_template="Hello {name}, you are {age}"
        )

        prompt = step._render_prompt({"name": "Alice", "age": 30})
        assert prompt == "Hello Alice, you are 30"

    def test_render_prompt_missing_variable(self):
        """Test prompt rendering with missing variable."""
        step = LLMStep(
            step_id="test",
            prompt_template="Hello {name}"
        )

        with pytest.raises(ValueError, match="Missing required"):
            step._render_prompt({"age": 30})

    @pytest.mark.asyncio
    async def test_validate_no_api_key(self):
        """Test validation fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            step = LLMStep(step_id="test", prompt_template="Hello")
            context = StepContext(
                execution_id="ex-1",
                step_execution_id="step-1",
                inputs={},
                state={},
                config={}
            )

            is_valid = await step.validate(context)
            assert not is_valid

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful LLM execution."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # Mock OpenAI client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello, Alice!"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5

            with patch('wflo.workflow.steps.llm.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )
                mock_openai.return_value = mock_client

                step = LLMStep(
                    step_id="test",
                    model="gpt-4",
                    prompt_template="Say hello to {name}"
                )

                context = StepContext(
                    execution_id="ex-1",
                    step_execution_id="step-1",
                    inputs={"name": "Alice"},
                    state={},
                    config={}
                )

                result = await step.execute(context)

                assert result.success
                assert result.output["text"] == "Hello, Alice!"
                assert result.cost_usd > 0
                assert result.metadata["prompt_tokens"] == 10
                assert result.metadata["completion_tokens"] == 5
```

---

#### Afternoon: Example Implementation (3-4 hours)

**Task 2.5: Create Example Workflow** (1 hour)

**File: `examples/simple_llm_agent/workflow.py`**
```python
"""Simple LLM agent workflow definition."""

from wflo.workflow.steps import LLMStep


def create_simple_llm_workflow() -> dict:
    """Create simple LLM workflow definition.

    Returns:
        dict: Workflow configuration
    """
    return {
        "name": "simple-llm-agent",
        "description": "Call OpenAI GPT-4 with cost tracking",
        "version": "1.0",
        "steps": [
            LLMStep(
                step_id="llm-call",
                model="gpt-4",
                prompt_template="{user_prompt}",
                system_prompt="You are a helpful assistant that provides clear, concise answers.",
                max_tokens=500,
                temperature=0.7
            )
        ]
    }
```

**Task 2.6: Create Execution Script** (2 hours)

**File: `examples/simple_llm_agent/run.py`**
```python
"""Run simple LLM agent example."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wflo.workflow.steps import LLMStep, StepContext
from wflo.db.engine import get_session
from wflo.db.models import WorkflowExecutionModel
from wflo.observability.logging import setup_logging


@click.command()
@click.option("--prompt", required=True, help="Question for the LLM")
@click.option("--model", default="gpt-4", help="Model to use")
@click.option("--budget", default=1.0, help="Max cost in USD")
@click.option("--verbose", is_flag=True, help="Verbose logging")
async def main(prompt: str, model: str, budget: float, verbose: bool):
    """Run simple LLM agent example."""

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level)

    # Header
    click.echo("🚀 Starting Wflo Simple LLM Agent Example")
    click.echo("━" * 50)
    click.echo(f"\n📝 Configuration:")
    click.echo(f"   Prompt: {prompt}")
    click.echo(f"   Model: {model}")
    click.echo(f"   Budget: ${budget:.2f}")
    click.echo("\n" + "━" * 50 + "\n")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        click.echo("❌ Error: OPENAI_API_KEY environment variable not set\n")
        click.echo("   Set your API key:")
        click.echo("   export OPENAI_API_KEY=\"sk-...\"\n")
        click.echo("   Get API key: https://platform.openai.com/api-keys")
        return 1

    try:
        # Create LLM step
        llm_step = LLMStep(
            step_id="llm-call",
            model=model,
            prompt_template="{user_prompt}",
            system_prompt="You are a helpful assistant.",
            max_tokens=500
        )

        # Create context
        execution_id = f"exec-{datetime.now().timestamp()}"
        context = StepContext(
            execution_id=execution_id,
            step_execution_id=f"step-{datetime.now().timestamp()}",
            inputs={"user_prompt": prompt},
            state={},
            config={}
        )

        # Execute
        click.echo("✓ Calling OpenAI API...")
        started_at = datetime.now()
        result = await llm_step.execute(context)
        duration = (datetime.now() - started_at).total_seconds()

        if not result.success:
            click.echo(f"❌ Error: {result.error}")
            return 1

        # Check budget
        if result.cost_usd > budget:
            click.echo(f"❌ Budget exceeded: ${result.cost_usd:.4f} > ${budget:.2f}")
            return 1

        click.echo("✓ Response received")
        click.echo("✓ Cost tracked\n")
        click.echo("━" * 50)
        click.echo("\n📊 Result:")
        click.echo("━" * 50)
        click.echo()
        click.echo(result.output["text"])
        click.echo()
        click.echo("━" * 50)
        click.echo("\n📈 Summary:")
        click.echo("━" * 50)
        click.echo()
        click.echo(f"Execution ID:    {execution_id}")
        click.echo(f"Status:          COMPLETED")
        click.echo(f"Duration:        {duration:.2f} seconds")
        click.echo(f"Cost:            ${result.cost_usd:.4f} USD")
        click.echo(f"Budget Used:     {(result.cost_usd/budget)*100:.1f}%")
        click.echo(f"Tokens:          {result.metadata['total_tokens']} "
                   f"(prompt: {result.metadata['prompt_tokens']}, "
                   f"completion: {result.metadata['completion_tokens']})")
        click.echo()
        click.echo("━" * 50)
        click.echo("\n✓ Workflow completed successfully!\n")

        return 0

    except Exception as e:
        click.echo(f"\n❌ Error: {e}\n")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

**Task 2.7: Test Example** (30 minutes)
- [ ] Set OPENAI_API_KEY
- [ ] Run: `poetry run python examples/simple_llm_agent/run.py --prompt "What is 2+2?"`
- [ ] Verify output looks correct
- [ ] Test with different prompts
- [ ] Test budget enforcement
- [ ] Fix any issues

---

### Day 3: Integration & Documentation (4-6 hours)

#### Morning: Full Integration (2-3 hours)

**Task 3.1: Integrate with Temporal** (2 hours)

Create Temporal workflow that uses the LLM step:

**File: `src/wflo/temporal/workflows.py`** (update existing)

Add new workflow class:
```python
@workflow.defn
class SimpleLLMWorkflow:
    """Simple LLM workflow using step system."""

    @workflow.run
    async def run(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_cost_usd: float | None = None
    ) -> dict[str, Any]:
        """Execute simple LLM workflow."""

        execution_id = str(uuid4())

        # Call LLM via activity
        result = await workflow.execute_activity(
            execute_llm_step_activity,
            args=[prompt, model, execution_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Check budget if specified
        if max_cost_usd and result["cost_usd"] > max_cost_usd:
            raise ValueError(f"Budget exceeded: {result['cost_usd']} > {max_cost_usd}")

        return result
```

**File: `src/wflo/temporal/activities.py`** (update existing)

Add new activity:
```python
@activity.defn
async def execute_llm_step_activity(
    prompt: str,
    model: str,
    execution_id: str
) -> dict:
    """Execute LLM step as Temporal activity."""

    from wflo.workflow.steps import LLMStep, StepContext

    step = LLMStep(
        step_id="llm-call",
        model=model,
        prompt_template="{user_prompt}"
    )

    context = StepContext(
        execution_id=execution_id,
        step_execution_id=str(uuid4()),
        inputs={"user_prompt": prompt},
        state={},
        config={}
    )

    result = await step.execute(context)

    if not result.success:
        raise RuntimeError(f"LLM step failed: {result.error}")

    return {
        "output": result.output["text"],
        "cost_usd": result.cost_usd,
        "tokens": result.metadata["total_tokens"],
        "model": model
    }
```

**Task 3.2: Create Temporal Example** (1 hour)

**File: `examples/simple_llm_agent/run_with_temporal.py`**
```python
"""Run simple LLM agent with Temporal."""

# Similar to run.py but uses Temporal client
# Demonstrates full Temporal integration
```

---

#### Afternoon: Documentation & Testing (2-3 hours)

**Task 3.3: Update Main README** (30 minutes)

Update `/home/user/wflo/README.md`:
- Add "Quick Start" section at top
- Include working example
- Link to examples/
- Show 5-minute setup

**Task 3.4: Create Quickstart Guide** (1 hour)

**File: `docs/QUICKSTART.md`**

5-minute guide to run first example.

**Task 3.5: Final Testing** (1 hour)
- [ ] Fresh install test
- [ ] Run all examples
- [ ] Verify documentation accuracy
- [ ] Test error cases
- [ ] Create screencast/demo

**Task 3.6: Commit & Push** (30 minutes)
- [ ] Review all changes
- [ ] Write comprehensive commit message
- [ ] Push to remote
- [ ] Create summary document

---

## Files to Create/Modify

### New Files (Create)
- [ ] `src/wflo/workflow/steps/__init__.py`
- [ ] `src/wflo/workflow/steps/base.py`
- [ ] `src/wflo/workflow/steps/llm.py`
- [ ] `tests/unit/test_llm_step.py`
- [ ] `examples/simple_llm_agent/workflow.py`
- [ ] `examples/simple_llm_agent/run.py`
- [ ] `examples/simple_llm_agent/run_with_temporal.py`
- [ ] `docs/QUICKSTART.md`

### Files to Modify
- [ ] `src/wflo/sandbox/runtime.py` (fix line 210)
- [ ] `src/wflo/temporal/workflows.py` (add SimpleLLMWorkflow)
- [ ] `src/wflo/temporal/activities.py` (add execute_llm_step_activity)
- [ ] `README.md` (add quick start)
- [ ] `pyproject.toml` (add openai dependency if missing)

---

## Testing Strategy

### Unit Tests
- [ ] LLMStep initialization
- [ ] Prompt template rendering
- [ ] Validation logic
- [ ] Mocked API calls

### Integration Tests
- [ ] Sandbox runtime with Docker
- [ ] LLM step with real API (optional)
- [ ] Temporal workflow execution
- [ ] Database persistence

### Manual Testing
- [ ] Run example with various prompts
- [ ] Test budget enforcement
- [ ] Test error handling
- [ ] Verify cost tracking
- [ ] Check Temporal UI

---

## Success Criteria

### Functional
- [ ] Can run: `python examples/simple_llm_agent/run.py --prompt "Hello"`
- [ ] Receives response from OpenAI
- [ ] Cost correctly calculated and displayed
- [ ] Budget enforcement works
- [ ] Error handling graceful

### Quality
- [ ] All new tests passing
- [ ] Sandbox tests passing (27/27)
- [ ] Code follows project style
- [ ] Comprehensive documentation
- [ ] Example works on fresh install

### Demonstration
- [ ] 5-minute demo video ready
- [ ] README shows working example
- [ ] Can onboard new developer in < 30 minutes
- [ ] Stakeholders impressed

---

## Risk Mitigation

### Risk: OpenAI API Rate Limits
**Mitigation**: Add retry logic with exponential backoff

### Risk: Docker image too large
**Mitigation**: Multi-stage build, minimal dependencies

### Risk: Temporal integration complex
**Mitigation**: Start with simple workflow, add features incrementally

### Risk: Cost tracking inaccurate
**Mitigation**: Use tokencost library, validate against OpenAI billing

---

## Next Steps After Completion

1. **Additional Examples** (Week 2)
   - Multi-step workflow
   - Sandbox execution
   - Custom step types

2. **CLI Tool** (Week 2)
   - `wflo run` command
   - `wflo status` command
   - `wflo list` command

3. **REST API** (Week 3-4)
   - FastAPI implementation
   - OpenAPI docs
   - Authentication

4. **Production Ready** (Month 2-3)
   - Security hardening (Phase 5)
   - CI/CD pipeline
   - Kubernetes deployment

---

## Progress Tracking

**Last Updated**: 2025-11-11
**Current Stage**: Day 1 - Documentation Complete
**Next Milestone**: Build Docker image and fix sandbox bug
**Blockers**: None
**ETA**: 2 days remaining

---

*Document Version: 1.0*
