#!/usr/bin/env python3
"""Test that the example can be imported and basic setup works."""

import sys
from pathlib import Path

# Add src to path (go up 2 levels from examples/simple_llm_agent/ to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

print("Testing imports...")

try:
    from wflo.workflow.steps import LLMStep, StepContext, StepResult
    print("✓ Step imports successful")
except ImportError as e:
    print(f"✗ Step import failed: {e}")
    sys.exit(1)

try:
    # Create a basic step
    step = LLMStep(
        step_id="test",
        model="gpt-4",
        prompt_template="Hello {name}",
    )
    print("✓ LLMStep instantiation successful")
except Exception as e:
    print(f"✗ LLMStep instantiation failed: {e}")
    sys.exit(1)

try:
    # Create a context
    context = StepContext(
        execution_id="test-exec",
        step_execution_id="test-step",
        inputs={"name": "World"},
        state={},
        config={},
    )
    print("✓ StepContext instantiation successful")
except Exception as e:
    print(f"✗ StepContext instantiation failed: {e}")
    sys.exit(1)

try:
    # Test prompt rendering
    rendered = step._render_prompt(context.inputs)
    assert rendered == "Hello World"
    print("✓ Prompt rendering successful")
except Exception as e:
    print(f"✗ Prompt rendering failed: {e}")
    sys.exit(1)

print("\n✓ All basic checks passed!")
print("\nTo run the full example:")
print('  export OPENAI_API_KEY="sk-..."')
print('  python examples/simple_llm_agent/run.py --prompt "What is 2+2?"')
