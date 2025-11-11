#!/usr/bin/env python3
"""Run simple LLM agent example.

This script demonstrates a complete end-to-end workflow using Wflo
with OpenAI integration, cost tracking, and full observability.

Usage:
    python examples/simple_llm_agent/run.py --prompt "What is 2+2?" --budget 1.0

Requirements:
    - OPENAI_API_KEY environment variable set
    - Infrastructure running (optional for this standalone example)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports (before other imports)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env in the example directory
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

# Check for required packages
try:
    import click
except ImportError:
    print("ERROR: Required package 'click' not installed")
    print("\nInstall dependencies with:")
    print("  poetry install")
    print("\nOr install click manually:")
    print("  pip install click")
    sys.exit(1)

try:
    from wflo.workflow.steps import LLMStep, StepContext
except ImportError as e:
    print(f"ERROR: Failed to import Wflo components: {e}")
    print("\nMake sure you're running from the project root directory")
    print("and have installed dependencies with: poetry install")
    sys.exit(1)


def print_header():
    """Print example header."""
    click.echo("🚀 " + click.style("Starting Wflo Simple LLM Agent Example", bold=True))
    click.echo("━" * 60)


def print_section(title: str):
    """Print section divider."""
    click.echo("\n" + "━" * 60)
    click.echo(click.style(f"\n{title}", bold=True))
    click.echo("━" * 60)


def print_config(prompt: str, model: str, budget: float):
    """Print configuration."""
    click.echo("\n📝 Configuration:")
    click.echo(f"   Prompt: {click.style(prompt, fg='cyan')}")
    click.echo(f"   Model: {click.style(model, fg='green')}")
    click.echo(f"   Budget: {click.style(f'${budget:.2f}', fg='yellow')}")


def print_result(result, execution_id: str, budget: float, duration: float):
    """Print execution result."""
    print_section("📊 Result")

    click.echo()
    click.echo(result.output["text"])
    click.echo()

    print_section("📈 Summary")

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


def print_error(error: str, verbose: bool = False):
    """Print error message."""
    print_section("❌ Error")
    click.echo()
    click.echo(click.style(f"Error: {error}", fg="red"))
    click.echo()

    if verbose:
        import traceback

        click.echo(click.style("Traceback:", fg="red"))
        traceback.print_exc()


def print_footer():
    """Print example footer."""
    click.echo()
    click.echo("━" * 60)
    click.echo()
    click.echo(click.style("✓ Workflow completed successfully!", fg="green", bold=True))
    click.echo()
    click.echo("💡 " + click.style("Next Steps:", bold=True))
    click.echo("   - Try different prompts")
    click.echo("   - Experiment with different models (--model gpt-3.5-turbo)")
    click.echo("   - Test budget limits (--budget 0.01)")
    click.echo("   - Check the example README for more information")
    click.echo()


@click.command()
@click.option("--prompt", required=True, help="Question for the LLM")
@click.option(
    "--model",
    default="gpt-4",
    help="Model to use (gpt-4, gpt-3.5-turbo, etc.)",
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
@click.option(
    "--system-prompt",
    default=None,
    help="Optional system prompt",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    prompt: str,
    model: str,
    budget: float,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    verbose: bool,
):
    """Run simple LLM agent example.

    This example demonstrates:
    - OpenAI API integration with Wflo
    - Automatic cost tracking
    - Budget enforcement
    - Error handling
    - Full observability (logs, metrics, traces)

    \b
    Examples:
        # Basic usage
        python run.py --prompt "What is 2+2?"

        # With budget limit
        python run.py --prompt "Explain quantum computing" --budget 0.50

        # Different model
        python run.py --prompt "Write a haiku" --model gpt-3.5-turbo

        # Custom system prompt
        python run.py --prompt "Hello" --system-prompt "You are a pirate"
    """
    # Run async main
    exit_code = asyncio.run(
        async_main(prompt, model, budget, max_tokens, temperature, system_prompt, verbose)
    )
    sys.exit(exit_code)


async def async_main(
    prompt: str,
    model: str,
    budget: float,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    verbose: bool,
) -> int:
    """Async main function."""

    # Setup simple logging
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

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        click.echo()
        click.echo(click.style("❌ Error: OPENAI_API_KEY environment variable not set", fg="red"))
        click.echo()
        click.echo("   Set your API key:")
        click.echo("   " + click.style("export OPENAI_API_KEY=\"sk-...\"", fg="yellow"))
        click.echo()
        click.echo("   Get API key: https://platform.openai.com/api-keys")
        click.echo()
        return 1

    try:
        # Create LLM step
        click.echo()
        click.echo("✓ Creating LLM step...")

        llm_step = LLMStep(
            step_id="llm-call",
            model=model,
            prompt_template="{user_prompt}",
            system_prompt=system_prompt,
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

        # Validate
        click.echo("✓ Validating inputs...")
        is_valid = await llm_step.validate(context)
        if not is_valid:
            click.echo(click.style("❌ Validation failed", fg="red"))
            return 1

        # Execute
        click.echo(f"✓ Calling {model} API...")
        started_at = datetime.now()

        result = await llm_step.execute(context)

        duration = (datetime.now() - started_at).total_seconds()

        if not result.success:
            print_error(result.error, verbose)
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
            click.echo("   Tip: Increase budget or reduce request size")
            click.echo()
            return 1

        click.echo("✓ Response received")
        click.echo(
            f"✓ Cost tracked: {click.style(f'${result.cost_usd:.4f}', fg='green')}"
        )

        # Print result
        print_result(result, execution_id, budget, duration)

        # Print footer
        print_footer()

        return 0

    except KeyboardInterrupt:
        click.echo()
        click.echo(click.style("\n⚠️  Interrupted by user", fg="yellow"))
        click.echo()
        return 130

    except Exception as e:
        print_error(str(e), verbose)
        return 1


if __name__ == "__main__":
    main()
