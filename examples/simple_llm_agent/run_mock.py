#!/usr/bin/env python3
"""Run simple LLM agent example with MOCKED OpenAI responses.

This version mocks the OpenAI API to test the complete flow without
making actual API calls or spending credits.

Usage:
    python examples/simple_llm_agent/run_mock.py --prompt "What is 2+2?"
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load environment variables from .env file if it exists (for consistency)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

try:
    import click
except ImportError:
    print("ERROR: Required package 'click' not installed")
    print("\nInstall dependencies with:")
    print("  poetry install")
    sys.exit(1)

try:
    from wflo.workflow.steps import LLMStep, StepContext
except ImportError as e:
    print(f"ERROR: Failed to import Wflo components: {e}")
    print("\nMake sure you're running from the project root directory")
    sys.exit(1)


def print_header():
    """Print example header."""
    click.echo("🚀 " + click.style("Wflo Simple LLM Agent Example", bold=True))
    click.echo(click.style("   (MOCK MODE - No API calls)", fg="yellow"))
    click.echo("━" * 60)


def print_config(prompt: str, model: str, budget: float):
    """Print configuration."""
    click.echo("\n📝 Configuration:")
    click.echo(f"   Prompt: {click.style(prompt, fg='cyan')}")
    click.echo(f"   Model: {click.style(model, fg='green')} {click.style('(mocked)', fg='yellow')}")
    click.echo(f"   Budget: {click.style(f'${budget:.2f}', fg='yellow')}")


def print_result(result, execution_id: str, budget: float, duration: float):
    """Print execution result."""
    click.echo("\n━" * 60)
    click.echo(click.style("\n📊 Result:", bold=True))
    click.echo("━" * 60)
    click.echo()
    click.echo(result.output["text"])
    click.echo()
    click.echo("━" * 60)
    click.echo(click.style("\n📈 Summary:", bold=True))
    click.echo("━" * 60)
    click.echo()
    click.echo(f"Execution ID:    {click.style(execution_id, fg='cyan')}")
    click.echo(f"Status:          {click.style('COMPLETED', fg='green')}")
    click.echo(f"Duration:        {click.style(f'{duration:.2f} seconds', fg='blue')}")
    click.echo(
        f"Cost:            {click.style(f'${result.cost_usd:.4f} USD', fg='yellow')}"
    )

    budget_pct = (result.cost_usd / budget) * 100
    budget_color = "green" if budget_pct < 50 else "yellow" if budget_pct < 80 else "red"
    click.echo(f"Budget Used:     {click.style(f'{budget_pct:.1f}%', fg=budget_color)}")

    tokens_info = (
        f"{result.metadata['total_tokens']} "
        f"(prompt: {result.metadata['prompt_tokens']}, "
        f"completion: {result.metadata['completion_tokens']})"
    )
    click.echo(f"Tokens:          {click.style(tokens_info, fg='blue')}")


def create_mock_response(prompt: str, model: str):
    """Create a mock OpenAI response based on the prompt.

    This simulates what OpenAI would return, including token counts.
    """
    # Generate mock response based on prompt
    if "2+2" in prompt.lower() or "2 + 2" in prompt.lower():
        response_text = "2+2 equals 4. This is a basic arithmetic operation where we add two identical numbers together to get their sum."
    elif "capital" in prompt.lower():
        response_text = "The capital of France is Paris. It's located in the north-central part of the country on the Seine River."
    elif "quantum" in prompt.lower():
        response_text = "Quantum computing is a revolutionary approach to computation that leverages quantum mechanical phenomena like superposition and entanglement. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or 'qubits' that can exist in multiple states simultaneously. This allows quantum computers to solve certain complex problems exponentially faster than classical computers."
    elif "hello" in prompt.lower() or "hi" in prompt.lower():
        response_text = "Hello! I'm a helpful AI assistant. How can I help you today?"
    else:
        response_text = f"I understand you asked: '{prompt[:50]}...'. This is a mock response simulating what an LLM would return. In production, this would be an actual response from {model}."

    # Calculate realistic token counts
    # Rough estimate: ~4 characters per token
    prompt_tokens = len(prompt) // 4 + 5  # Add base tokens for formatting
    completion_tokens = len(response_text) // 4 + 3
    total_tokens = prompt_tokens + completion_tokens

    # Create mock response object
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = response_text
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = prompt_tokens
    mock_response.usage.completion_tokens = completion_tokens
    mock_response.usage.total_tokens = total_tokens

    return mock_response


@click.command()
@click.option("--prompt", required=True, help="Question for the LLM")
@click.option(
    "--model",
    default="gpt-4",
    help="Model to use (mocked)",
    show_default=True,
)
@click.option(
    "--budget",
    default=1.0,
    type=float,
    help="Maximum cost in USD",
    show_default=True,
)
@click.option(
    "--max-tokens",
    default=500,
    type=int,
    help="Maximum completion tokens",
    show_default=True,
)
@click.option(
    "--temperature",
    default=0.7,
    type=float,
    help="Sampling temperature (0-2)",
    show_default=True,
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    prompt: str,
    model: str,
    budget: float,
    max_tokens: int,
    temperature: float,
    verbose: bool,
):
    """Run simple LLM agent example with MOCKED OpenAI API.

    This version demonstrates the complete workflow without making
    actual API calls. Perfect for testing!

    \b
    Examples:
        python run_mock.py --prompt "What is 2+2?"
        python run_mock.py --prompt "What is the capital of France?"
        python run_mock.py --prompt "Explain quantum computing"
    """
    exit_code = asyncio.run(
        async_main(prompt, model, budget, max_tokens, temperature, verbose)
    )
    sys.exit(exit_code)


async def async_main(
    prompt: str,
    model: str,
    budget: float,
    max_tokens: int,
    temperature: float,
    verbose: bool,
) -> int:
    """Async main function."""

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Print header
    print_header()
    print_config(prompt, model, budget)
    click.echo()
    click.echo("━" * 60)

    try:
        # Create mock OpenAI response
        mock_response = create_mock_response(prompt, model)

        # Mock cost (realistic for GPT-4)
        # GPT-4: ~$0.03/1K input tokens, ~$0.06/1K output tokens
        input_cost = (mock_response.usage.prompt_tokens / 1000) * 0.03
        output_cost = (mock_response.usage.completion_tokens / 1000) * 0.06
        mock_cost = input_cost + output_cost

        click.echo()
        click.echo("✓ Creating LLM step...")
        click.echo("✓ Validating inputs...")
        click.echo(f"✓ Calling {model} API " + click.style("(mocked)", fg="yellow") + "...")

        # Small delay to simulate API call
        await asyncio.sleep(0.5)

        # Mock the OpenAI and CostTracker
        with patch("openai.AsyncOpenAI") as mock_openai:
            with patch("wflo.cost.tracker.CostTracker") as mock_cost_tracker:
                # Setup OpenAI mock
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )
                mock_openai.return_value = mock_client

                # Setup CostTracker mock
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.calculate_cost.return_value = mock_cost
                mock_cost_tracker.return_value = mock_tracker_instance

                # Create LLM step
                llm_step = LLMStep(
                    step_id="llm-call",
                    model=model,
                    prompt_template="{user_prompt}",
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # Create context
                execution_id = f"exec-{int(datetime.now().timestamp())}"
                step_execution_id = f"step-{int(datetime.now().timestamp())}"

                context = StepContext(
                    execution_id=execution_id,
                    step_execution_id=step_execution_id,
                    inputs={"user_prompt": prompt},
                    state={},
                    config={},
                )

                # Execute (with mock)
                # Need to mock the API key check
                with patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"}):
                    started_at = datetime.now()
                    result = await llm_step.execute(context)
                    duration = (datetime.now() - started_at).total_seconds()

                if not result.success:
                    click.echo(click.style(f"\n❌ Error: {result.error}", fg="red"))
                    return 1

                # Check budget
                if result.cost_usd > budget:
                    click.echo()
                    click.echo(
                        click.style(
                            f"❌ Budget exceeded: ${result.cost_usd:.4f} > ${budget:.2f}",
                            fg="red",
                        )
                    )
                    click.echo()
                    return 1

                click.echo("✓ Response received")
                click.echo(
                    f"✓ Cost tracked: {click.style(f'${result.cost_usd:.4f}', fg='green')}"
                )

                # Print result
                print_result(result, execution_id, budget, duration)

                # Footer
                click.echo()
                click.echo("━" * 60)
                click.echo()
                click.echo(click.style("✓ Workflow completed successfully!", fg="green", bold=True))
                click.echo()
                click.echo(click.style("💡 Note:", bold=True) + " This was a MOCK run")
                click.echo("   - No actual API calls were made")
                click.echo("   - Costs and tokens are realistic estimates")
                click.echo("   - Response is generated locally")
                click.echo()
                click.echo(click.style("To run with real OpenAI:", bold=True))
                click.echo('   export OPENAI_API_KEY="sk-..."')
                click.echo(f'   python examples/simple_llm_agent/run.py --prompt "{prompt}"')
                click.echo()

                return 0

    except Exception as e:
        click.echo()
        click.echo(click.style(f"\n❌ Error: {e}", fg="red"))
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
