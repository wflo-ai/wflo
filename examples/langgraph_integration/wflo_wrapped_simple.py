"""
Simple LangGraph example WITH wflo integration (Phase 1 features).

This demonstrates the actual implemented features:
✅ Automatic cost tracking per node (via @track_llm_call)
✅ Budget enforcement (stops if exceeds budget)
✅ Automatic checkpointing after each node (via @checkpoint)
✅ Rollback capability on errors
✅ Full observability (traces, logs)

NOTE: This uses the Phase 1 SDK implementation.
Circuit breakers and retry logic will be added in Phase 2.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import asyncio

# Wflo imports - Phase 1 features
from wflo.sdk import WfloWorkflow, BudgetExceededError, track_llm_call, checkpoint


# State definition
class ResearchState(TypedDict):
    """State for research workflow."""
    query: str
    plan: str
    search_results: list[str]
    analysis: str
    final_report: str
    step_count: int


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)


# Node functions wrapped with wflo decorators
@track_llm_call(model="gpt-4")  # ✅ Phase 1: Automatic cost tracking
@checkpoint  # ✅ Phase 1: Automatic checkpointing
async def plan_research(state: ResearchState) -> ResearchState:
    """Create research plan with cost tracking and checkpointing."""
    print(f"[STEP 1] Planning research for: {state['query']}")

    messages = [
        SystemMessage(content="You are a research planning assistant."),
        HumanMessage(content=f"Create a brief research plan for: {state['query']}")
    ]

    response = await llm.ainvoke(messages)
    state["plan"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Research plan created (cost tracked, checkpoint saved)")
    return state


@track_llm_call(model="gpt-4")
@checkpoint
async def execute_searches(state: ResearchState) -> ResearchState:
    """Execute searches with cost tracking and checkpointing."""
    print(f"[STEP 2] Executing searches...")

    messages = [
        SystemMessage(content="You are a web search assistant."),
        HumanMessage(content=f"Based on this plan, list 3 search queries:\n{state['plan']}")
    ]

    response = await llm.ainvoke(messages)
    state["search_results"] = [response.content]
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Searches executed (cost tracked, checkpoint saved)")
    return state


@track_llm_call(model="gpt-4")
@checkpoint
async def generate_report(state: ResearchState) -> ResearchState:
    """Generate final report with cost tracking and checkpointing."""
    print(f"[STEP 3] Generating final report...")

    messages = [
        SystemMessage(content="You are a report writer."),
        HumanMessage(content=f"Write a brief summary report based on:\nQuery: {state['query']}\nSearches: {state['search_results']}")
    ]

    response = await llm.ainvoke(messages)
    state["final_report"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Report generated (cost tracked, checkpoint saved)")
    return state


# Build the LangGraph workflow
def create_research_graph():
    """Create LangGraph workflow."""
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("plan", plan_research)
    workflow.add_node("search", execute_searches)
    workflow.add_node("report", generate_report)

    # Add edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# Run with wflo orchestration
async def main():
    """Run research workflow with wflo."""

    # Create the LangGraph workflow
    app = create_research_graph()

    # Wrap with wflo for production features
    wflo = WfloWorkflow(
        name="research-agent",
        budget_usd=5.00,  # Hard budget limit
        enable_checkpointing=True,
        enable_observability=True
    )

    initial_state = {
        "query": "What are the latest advancements in AI agent frameworks in 2025?",
        "plan": "",
        "search_results": [],
        "analysis": "",
        "final_report": "",
        "step_count": 0
    }

    print("=" * 60)
    print("RUNNING LANGGRAPH WITH WFLO (Phase 1 Features)")
    print("=" * 60)
    print(f"\nQuery: {initial_state['query']}")
    print(f"Budget: $5.00")
    print(f"\nPhase 1 Features:")
    print(f"  ✅ Cost tracking per node")
    print(f"  ✅ Budget enforcement")
    print(f"  ✅ Automatic checkpointing")
    print(f"  ✅ Rollback capability")
    print(f"  ✅ Full observability\n")

    try:
        # Execute workflow with wflo wrapper
        final_state = await wflo.execute(app, initial_state)

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nSteps executed: {final_state['step_count']}")
        print(f"\nFinal Report:\n{final_state['final_report'][:200]}...")

        # Show cost breakdown
        cost_breakdown = await wflo.get_cost_breakdown()
        print("\n" + "=" * 60)
        print("COST BREAKDOWN")
        print("=" * 60)
        print(f"Total cost: ${cost_breakdown['total_usd']:.4f}")
        print(f"Budget: ${cost_breakdown['budget_usd']:.2f}")
        print(f"Remaining: ${cost_breakdown['remaining_usd']:.4f}")
        print(f"Exceeded: {cost_breakdown['exceeded']}")

        # Show wflo features used
        print("\n" + "=" * 60)
        print("WFLO FEATURES USED")
        print("=" * 60)
        print("✅ Cost tracked: Every LLM call monitored")
        print("✅ Budget enforced: Would stop at $5.00")
        print("✅ Checkpoints saved: 3 checkpoints created")
        print("✅ Rollback: Can restore to any checkpoint")
        print("✅ Observability: Full execution tracking")

        # Show trace ID
        trace_id = wflo.get_trace_id()
        print(f"\nTrace ID: {trace_id}")

    except BudgetExceededError as e:
        print(f"\n⛔ BUDGET EXCEEDED")
        print(f"   Spent: ${e.spent_usd:.4f}")
        print(f"   Budget: ${e.budget_usd:.2f}")
        print(f"\n✅ Wflo stopped execution before burning more money!")

        # Rollback to last checkpoint
        print("\n📝 Rolling back to last successful checkpoint...")
        restored_state = await wflo.rollback_to_last_checkpoint()
        if restored_state:
            print(f"✅ Restored to step {restored_state.get('step_count', 0)}")
            print("   You can resume from here with increased budget")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Type: {type(e).__name__}")

        # Rollback capability
        print("\n📝 Rolling back to last checkpoint...")
        restored_state = await wflo.rollback_to_last_checkpoint()
        if restored_state:
            print(f"✅ Restored to step {restored_state.get('step_count', 0)}")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        exit(1)

    asyncio.run(main())
