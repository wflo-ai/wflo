"""
Advanced Multi-Step Research Workflow with wflo.

Demonstrates all Phase 1 SDK features:
- Multi-step workflow with checkpointing
- Budget enforcement
- LLM call tracking across steps
- Rollback capability
- Cost monitoring
- Execution tracing
"""

import asyncio
from typing import Dict, List
from openai import AsyncOpenAI

from wflo.sdk.workflow import WfloWorkflow, BudgetExceededError
from wflo.sdk.decorators.track_llm import track_llm_call
from wflo.sdk.decorators.checkpoint import checkpoint


# Initialize OpenAI client
client = AsyncOpenAI()


@track_llm_call(model="gpt-4")
@checkpoint(name="research_planning")
async def plan_research(topic: str) -> Dict:
    """
    Step 1: Plan the research approach.

    Checkpoint: Allows rolling back to this state if planning needs revision.
    """
    print(f"\n📋 Step 1: Planning research on '{topic}'...")

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a research planning assistant. Break down topics into key areas to investigate.",
            },
            {
                "role": "user",
                "content": f"Create a research plan for: {topic}. List 3-4 key areas to investigate.",
            },
        ],
        temperature=0.7,
        max_tokens=300,
    )

    plan = response.choices[0].message.content
    print(f"📝 Research plan created")

    return {
        "topic": topic,
        "plan": plan,
        "areas": plan.split("\n")[:4],  # Extract first 4 areas
    }


@track_llm_call(model="gpt-4")
@checkpoint(name="research_execution")
async def conduct_research(state: Dict) -> Dict:
    """
    Step 2: Conduct research on each area.

    Checkpoint: Saves progress after completing research.
    """
    print(f"\n🔍 Step 2: Conducting research on {len(state['areas'])} areas...")

    findings = []
    for i, area in enumerate(state['areas'][:3], 1):  # Research first 3 areas
        print(f"  Researching area {i}/3...")

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant. Provide concise, factual findings.",
                },
                {
                    "role": "user",
                    "content": f"Research this aspect of {state['topic']}: {area}. Provide 2-3 key findings.",
                },
            ],
            temperature=0.5,
            max_tokens=200,
        )

        findings.append({
            "area": area,
            "findings": response.choices[0].message.content,
        })

    print(f"✅ Research completed for {len(findings)} areas")

    return {
        **state,
        "findings": findings,
    }


@track_llm_call(model="gpt-4")
@checkpoint(name="synthesis")
async def synthesize_findings(state: Dict) -> Dict:
    """
    Step 3: Synthesize findings into a summary.

    Checkpoint: Final state before producing output.
    """
    print(f"\n🧠 Step 3: Synthesizing findings...")

    # Combine all findings
    all_findings = "\n\n".join([
        f"{i+1}. {f['area']}\n{f['findings']}"
        for i, f in enumerate(state['findings'])
    ])

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a research synthesis expert. Create clear, coherent summaries.",
            },
            {
                "role": "user",
                "content": f"Synthesize these research findings into a cohesive summary:\n\n{all_findings}",
            },
        ],
        temperature=0.6,
        max_tokens=400,
    )

    summary = response.choices[0].message.content
    print(f"📄 Summary generated")

    return {
        **state,
        "summary": summary,
        "status": "completed",
    }


async def research_workflow(inputs: Dict) -> Dict:
    """
    Main research workflow orchestration.

    Coordinates the three-step research process.
    """
    # Step 1: Plan
    state = await plan_research(inputs["topic"])

    # Step 2: Research
    state = await conduct_research(state)

    # Step 3: Synthesize
    state = await synthesize_findings(state)

    return state


async def main():
    """Run the multi-step research workflow."""
    print("=" * 80)
    print("🚀 Multi-Step Research Workflow with wflo")
    print("=" * 80)

    # Create workflow with strict budget
    workflow = WfloWorkflow(
        name="research-workflow",
        budget_usd=1.50,  # Tight budget to demonstrate enforcement
        enable_checkpointing=True,
        enable_observability=True,
    )

    try:
        # Execute the workflow
        result = await workflow.execute(
            research_workflow,
            {"topic": "Impact of artificial intelligence on software development"},
        )

        print("\n" + "=" * 80)
        print("✅ Research Workflow Complete!")
        print("=" * 80)

        # Display results
        print(f"\n📊 Research Summary:")
        print(f"\n{result['summary']}")

        # Show cost breakdown
        cost_breakdown = await workflow.get_cost_breakdown()
        print(f"\n💰 Cost Analysis:")
        print(f"  Total spent: ${cost_breakdown['total_usd']:.4f}")
        print(f"  Budget limit: ${cost_breakdown['budget_usd']:.2f}")
        print(f"  Remaining: ${cost_breakdown['remaining_usd']:.4f}")
        print(f"  Budget exceeded: {'Yes ⚠️' if cost_breakdown['exceeded'] else 'No ✅'}")

        # Show execution tracking
        print(f"\n🔍 Execution Tracking:")
        print(f"  Execution ID: {workflow.execution_id}")
        print(f"  Trace ID: {workflow.get_trace_id()}")

        # Demonstrate checkpoint listing
        print(f"\n📍 Checkpoints Created:")
        print(f"  1. research_planning - Initial plan created")
        print(f"  2. research_execution - Research completed")
        print(f"  3. synthesis - Final summary generated")
        print(f"\n  💡 Use workflow.rollback_to_checkpoint('checkpoint_name') to restore any state")

    except BudgetExceededError as e:
        print(f"\n⚠️ Budget Exceeded!")
        print(f"  Spent: ${e.spent_usd:.4f}")
        print(f"  Budget: ${e.budget_usd:.2f}")
        print(f"  Overage: ${e.spent_usd - e.budget_usd:.4f}")
        print(f"\n💡 The workflow was stopped to prevent unexpected costs.")
        print(f"   Increase budget_usd or optimize prompts to complete execution.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


async def demo_rollback():
    """Demonstrate checkpoint rollback capability."""
    print("\n" + "=" * 80)
    print("🔄 Checkpoint Rollback Demo")
    print("=" * 80)

    workflow = WfloWorkflow(
        name="rollback-demo",
        budget_usd=2.0,
        enable_checkpointing=True,
    )

    # Execute workflow
    await workflow.execute(
        research_workflow,
        {"topic": "Machine learning in healthcare"},
    )

    # Demonstrate rollback
    print(f"\n📍 Rolling back to 'research_execution' checkpoint...")
    previous_state = await workflow.rollback_to_checkpoint("research_execution")

    if previous_state:
        print(f"✅ Successfully rolled back!")
        print(f"   State contains: {list(previous_state.keys())}")
        print(f"\n💡 You could now:")
        print(f"   - Resume from this state")
        print(f"   - Modify the research approach")
        print(f"   - Re-run synthesis with different parameters")
    else:
        print(f"❌ Checkpoint not found")


if __name__ == "__main__":
    # Run main workflow
    asyncio.run(main())

    # Optionally demonstrate rollback
    # asyncio.run(demo_rollback())
