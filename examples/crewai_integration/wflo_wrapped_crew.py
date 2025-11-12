"""
CrewAI WITH wflo integration.

This shows the SAME content marketing crew but wrapped with wflo for production:
✅ Per-agent cost tracking
✅ Budget limits per agent (prevents one agent from burning all budget)
✅ Automatic checkpointing after each agent
✅ Circuit breakers per agent
✅ Approval gate before "publishing"
✅ Rollback if editor rejects content
✅ Full observability of agent interactions
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os

# Wflo imports
from wflo.sdk import WfloWorkflow, with_wflo
from wflo.sdk.decorators import (
    track_agent_cost,
    checkpoint_after_agent,
    circuit_breaker_per_agent,
    approval_gate
)
from wflo.sdk.multi_agent import ConsensusVoting

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define agents with wflo tracking
@track_agent_cost(agent_name="researcher", budget_usd=2.00)
@circuit_breaker_per_agent(name="researcher", token_budget=30000)
researcher = Agent(
    role="Content Researcher",
    goal="Research comprehensive information about given topics",
    backstory="""You are an expert researcher with deep knowledge across
    multiple domains. You excel at finding accurate, relevant information
    and presenting it clearly.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

@track_agent_cost(agent_name="writer", budget_usd=3.00)
@circuit_breaker_per_agent(name="writer", token_budget=50000)
writer = Agent(
    role="Content Writer",
    goal="Write engaging, well-structured blog posts",
    backstory="""You are a professional content writer with 10+ years
    of experience. You write clear, engaging content that resonates
    with readers.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

@track_agent_cost(agent_name="editor", budget_usd=1.50)
@circuit_breaker_per_agent(name="editor", token_budget=20000)
editor = Agent(
    role="Content Editor",
    goal="Edit and improve blog posts for quality and readability",
    backstory="""You are a meticulous editor with a keen eye for detail.
    You improve clarity, fix grammar, and ensure content flows well.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Define tasks with wflo checkpointing
def create_content_tasks(topic: str):
    """Create tasks for content creation pipeline."""

    research_task = Task(
        description=f"""Research the topic: {topic}

        Find:
        - Key points and themes
        - Latest trends and developments
        - Interesting statistics or facts
        - Expert opinions

        Provide a comprehensive research summary.""",
        agent=researcher,
        expected_output="Detailed research summary with key points and sources"
    )

    # Checkpoint after research
    research_task = checkpoint_after_agent(research_task, agent_name="researcher")

    writing_task = Task(
        description=f"""Using the research provided, write a blog post about: {topic}

        The blog post should:
        - Be 800-1000 words
        - Have an engaging introduction
        - Include 3-4 main sections
        - Use clear headings
        - End with a strong conclusion
        - Be written in an engaging, accessible style""",
        agent=writer,
        expected_output="Complete blog post in markdown format",
        context=[research_task]
    )

    # Checkpoint after writing
    writing_task = checkpoint_after_agent(writing_task, agent_name="writer")

    editing_task = Task(
        description="""Edit and improve the blog post.

        Focus on:
        - Grammar and spelling
        - Clarity and flow
        - Sentence structure
        - Overall readability
        - SEO optimization

        Provide the final, polished version.""",
        agent=editor,
        expected_output="Final polished blog post ready for publishing",
        context=[writing_task]
    )

    # Checkpoint after editing
    editing_task = checkpoint_after_agent(editing_task, agent_name="editor")

    return [research_task, writing_task, editing_task]


# Create crew with wflo orchestration
def create_content_crew_with_wflo(topic: str, wflo: WfloWorkflow):
    """Create content creation crew with wflo integration."""
    tasks = create_content_tasks(topic)

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )

    # Wrap crew with wflo
    return wflo.wrap_crew(crew)


# Run with wflo orchestration
async def main():
    """Run content creation crew with wflo."""
    import asyncio

    topic = "The Future of AI Agent Frameworks in 2025"

    # Initialize wflo with per-agent budgets
    wflo = WfloWorkflow(
        name="content-crew",
        budget_usd=10.00,  # Total budget for all agents
        per_agent_budgets={
            "researcher": 2.00,
            "writer": 3.00,
            "editor": 1.50
        },
        enable_checkpointing=True,
        enable_consensus=True,  # Enable multi-agent consensus
        enable_approval_gates=True
    )

    print("=" * 60)
    print("RUNNING CREWAI WITH WFLO")
    print("=" * 60)
    print(f"\nTopic: {topic}")
    print(f"\nBudget Allocation:")
    print(f"  Researcher: $2.00")
    print(f"  Writer: $3.00")
    print(f"  Editor: $1.50")
    print(f"  Total: $10.00")
    print(f"\nFeatures enabled:")
    print(f"  ✅ Per-agent cost tracking")
    print(f"  ✅ Per-agent budget enforcement")
    print(f"  ✅ Checkpointing after each agent")
    print(f"  ✅ Circuit breakers per agent")
    print(f"  ✅ Approval gate before publish\n")

    try:
        crew = create_content_crew_with_wflo(topic, wflo)

        # Execute crew with wflo orchestration
        result = await wflo.execute_crew(crew)

        print("\n" + "=" * 60)
        print("ALL AGENTS COMPLETED")
        print("=" * 60)

        # Check if approval needed
        if wflo.requires_approval():
            print("\n⏸️  APPROVAL REQUIRED BEFORE PUBLISHING")
            print("\nContent preview:")
            print(result[:300] + "...")

            # In production, this would notify Slack/email
            print("\n📧 Approval request sent to marketing@company.com")
            print("⏱️  Waiting for approval (timeout: 1 hour)...")

            # Simulate approval (in real app, this would be human decision)
            approved = await wflo.wait_for_approval(
                execution_id=wflo.execution_id,
                timeout_seconds=3600
            )

            if not approved:
                print("\n❌ CONTENT REJECTED")
                print("Rolling back to writer checkpoint...")
                restored = await wflo.rollback_to_checkpoint("writer")
                print(f"✅ Rolled back, can retry from writer")
                return

        print("\n✅ CONTENT APPROVED")
        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nFinal Blog Post:\n{result[:300]}...")

        # Show cost breakdown per agent
        cost_breakdown = wflo.get_cost_breakdown_by_agent()
        print("\n" + "=" * 60)
        print("COST BREAKDOWN BY AGENT")
        print("=" * 60)
        for agent_name, cost_info in cost_breakdown.items():
            print(f"\n{agent_name.upper()}")
            print(f"  Cost: ${cost_info['cost_usd']:.4f}")
            print(f"  Budget: ${cost_info['budget_usd']:.2f}")
            print(f"  Remaining: ${cost_info['remaining_usd']:.4f}")
            print(f"  Tokens: {cost_info['total_tokens']:,}")
            print(f"  API calls: {cost_info['api_calls']}")

        total_cost = sum(c['cost_usd'] for c in cost_breakdown.values())
        print(f"\nTOTAL COST: ${total_cost:.4f} / $10.00")
        print(f"BUDGET REMAINING: ${10.00 - total_cost:.4f}")

        # Show checkpoints
        checkpoints = wflo.list_checkpoints()
        print("\n" + "=" * 60)
        print("CHECKPOINTS SAVED")
        print("=" * 60)
        for cp in checkpoints:
            print(f"  ✓ {cp['agent']} - {cp['timestamp']}")

        # Show trace
        trace_id = wflo.get_trace_id()
        print(f"\nView full trace: http://localhost:16686/trace/{trace_id}")

    except wflo.AgentBudgetExceededError as e:
        print(f"\n⛔ AGENT BUDGET EXCEEDED: {e}")
        print(f"✅ Wflo stopped agent before burning all budget!")

        # Show which agent exceeded
        print(f"\nAgent: {e.agent_name}")
        print(f"Budget: ${e.budget_usd:.2f}")
        print(f"Spent: ${e.spent_usd:.2f}")

        # Can continue with other agents
        print("\nOther agents can still continue...")

    except wflo.CircuitOpenError as e:
        print(f"\n⚠️  CIRCUIT BREAKER OPENED: {e}")
        print(f"✅ Wflo protected against API failures!")

        # Can retry with backoff
        print("\nRetrying in 60s...")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

        # Get detailed error context
        error_context = wflo.get_error_context()
        print(f"\nError details:")
        print(f"  Agent: {error_context['agent']}")
        print(f"  Task: {error_context['task']}")
        print(f"  Cost so far: ${error_context['cost_usd']:.4f}")

        # Can rollback to last successful agent
        print("\nRolling back to last successful checkpoint...")
        restored = await wflo.rollback_to_last_checkpoint()
        print(f"✅ Restored to agent: {restored['agent']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
