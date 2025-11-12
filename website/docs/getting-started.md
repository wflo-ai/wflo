---
sidbar_position: 2
title: Getting Started
description: Get your first wflo workflow running in 5 minutes.
---

# Getting Started in 5 Minutes

This guide will get you from zero to running your first `wflo`-protected workflow in less than 5 minutes. You'll see cost-tracking in action without needing to configure a database.

## Step 1: Install `wflo`

First, get the project code and install the dependencies.

```bash
# Clone the repository
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install with Poetry (recommended)
poetry install
```

## Step 2: Set Your API Key

`wflo` loads credentials from a `.env` file in your project root.

```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file and add your OpenAI API key
echo "OPENAI_API_KEY=sk-..." >> .env
```

## Step 3: Run Your First Protected Workflow

The code below defines a simple function that calls OpenAI. The `@track_llm_call` decorator and the `WfloWorkflow` wrapper add cost control and observability without changing the core logic.

1.  Save this code as `my_first_workflow.py` in the root of the `wflo` project.

    ```python
    import asyncio
    from openai import AsyncOpenAI
    from wflo.config import get_settings
    from wflo.sdk.workflow import WfloWorkflow
    from wflo.sdk.decorators.track_llm import track_llm_call

    # Get settings, which loads the .env file automatically
    settings = get_settings()
    client = AsyncOpenAI()

    @track_llm_call(model=settings.openai_model)
    async def generate_greeting(name: str):
        """A simple function that calls an LLM."""
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": f"Generate a friendly, one-sentence greeting for {name}."}],
            max_tokens=50,
        )
        return response.choices[0].message.content

    async def main():
        # Create a workflow with a name and a budget
        workflow = WfloWorkflow(
            name="hello-world-workflow",
            budget_usd=0.05,  # Set a 5-cent budget
        )

        # Execute the function through the wflo wrapper
        result = await workflow.execute(generate_greeting, {"name": "Alice"})

        print(f"\n✅ Agent Result: '{result}'")

        # After execution, get the cost breakdown
        cost_breakdown = await workflow.get_cost_breakdown()
        print(f"\n💰 Cost Analysis:")
        print(f"   Total Cost: ${cost_breakdown['total_usd']:.6f}")
        print(f"   Budget:     ${cost_breakdown['budget_usd']:.2f}")

    if __name__ == "__main__":
        asyncio.run(main())
    ```

2.  Now, run the file from your terminal:

    ```bash
    poetry run python my_first_workflow.py
    ```

### Expected Output

You will see the result from the agent, followed by the cost analysis provided by `wflo`.

```
✅ Agent Result: 'Hello Alice, it's a pleasure to meet you!'

💰 Cost Analysis:
   Total Cost: $0.000084
   Budget:     $0.05
```

**Congratulations!** You've just run your first workflow with `wflo`, complete with cost tracking and budget enforcement. Notice you didn't need to write any complex code to track tokens or calculate costs—the `@track_llm_call` decorator handled it automatically.

## Next Steps

*   **Enable Persistence:** By default, your workflow history isn't saved. Follow the **[Enabling Persistence Guide](./guides/enabling-persistence.md)** to set up a database for long-term execution tracking and checkpointing.
*   **Explore Features:** Learn more about what you can do with `wflo` in the **[Features](./features/overview.md)** guide.
*   **See More Examples:** Check out the `examples/` directory for integrations with LangGraph, CrewAI, and more.