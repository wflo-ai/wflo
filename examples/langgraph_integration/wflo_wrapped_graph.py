"""
LangGraph WITH wflo integration.

This shows the SAME research agent but wrapped with wflo for production readiness:
✅ Automatic cost tracking per node
✅ Budget enforcement (stops if exceeds $5)
✅ Automatic checkpointing after each node
✅ Circuit breakers on failures
✅ Automatic retry with exponential backoff
✅ Full observability (traces, metrics, logs)
✅ Rollback capability on errors
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

# Wflo imports
from wflo.sdk import WfloWorkflow, with_wflo
from wflo.sdk.decorators import track_cost, checkpoint, circuit_breaker, with_retry


# State definition (same as before)
class ResearchState(TypedDict):
    """State for research workflow."""
    query: str
    plan: str
    search_results: list[str]
    analysis: str
    final_report: str
    step_count: int
    cost_usd: float  # Track cost in state


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)


# Node functions wrapped with wflo decorators
@track_cost(model="gpt-4")  # Automatic cost tracking
@checkpoint  # Save state after this step
@circuit_breaker(name="research-planner", token_budget=10000)
@with_retry(max_attempts=3, backoff="exponential")
async def plan_research(state: ResearchState) -> ResearchState:
    """Create research plan with wflo protection."""
    print(f"[STEP 1] Planning research for: {state['query']}")

    messages = [
        SystemMessage(content="You are a research planning assistant."),
        HumanMessage(content=f"Create a research plan for: {state['query']}")
    ]

    response = await llm.ainvoke(messages)
    state["plan"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    # Cost automatically tracked by decorator
    print(f"✓ Research plan created (cost tracked)")
    return state


@track_cost(model="gpt-4")
@checkpoint
@circuit_breaker(name="research-searcher", token_budget=15000)
@with_retry(max_attempts=3)
async def execute_searches(state: ResearchState) -> ResearchState:
    """Execute web searches with wflo protection."""
    print(f"[STEP 2] Executing searches...")

    messages = [
        SystemMessage(content="You are a web search assistant."),
        HumanMessage(content=f"Based on this plan, what searches would you do?\n{state['plan']}")
    ]

    response = await llm.ainvoke(messages)
    state["search_results"] = [response.content]
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Found {len(state['search_results'])} results (cost tracked)")
    return state


@track_cost(model="gpt-4")
@checkpoint
@circuit_breaker(name="research-analyzer", token_budget=20000)
@with_retry(max_attempts=3)
async def analyze_results(state: ResearchState) -> ResearchState:
    """Analyze search results with wflo protection."""
    print(f"[STEP 3] Analyzing results...")

    messages = [
        SystemMessage(content="You are a research analyst."),
        HumanMessage(content=f"Analyze these search results:\n{state['search_results']}")
    ]

    response = await llm.ainvoke(messages)
    state["analysis"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Analysis complete (cost tracked)")
    return state


@track_cost(model="gpt-4")
@checkpoint
@circuit_breaker(name="research-reporter", token_budget=30000)
@with_retry(max_attempts=3)
async def generate_report(state: ResearchState) -> ResearchState:
    """Generate final report with wflo protection."""
    print(f"[STEP 4] Generating final report...")

    messages = [
        SystemMessage(content="You are a report writer."),
        HumanMessage(content=f"Write a final report based on:\nQuery: {state['query']}\nAnalysis: {state['analysis']}")
    ]

    response = await llm.ainvoke(messages)
    state["final_report"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Report generated (cost tracked)")
    return state


# Build the graph (same as before)
def create_research_graph():
    """Create LangGraph workflow."""
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("plan", plan_research)
    workflow.add_node("search", execute_searches)
    workflow.add_node("analyze", analyze_results)
    workflow.add_node("report", generate_report)

    # Add edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "analyze")
    workflow.add_edge("analyze", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# Run with wflo orchestration
async def main():
    """Run research workflow with wflo."""
    import asyncio

    # Initialize wflo
    wflo = WfloWorkflow(
        name="research-agent",
        budget_usd=5.00,  # Hard limit
        enable_checkpointing=True,
        enable_observability=True
    )

    app = create_research_graph()

    initial_state = {
        "query": "What are the latest advancements in AI agent frameworks in 2025?",
        "plan": "",
        "search_results": [],
        "analysis": "",
        "final_report": "",
        "step_count": 0,
        "cost_usd": 0.0
    }

    print("=" * 60)
    print("RUNNING LANGGRAPH WITH WFLO")
    print("=" * 60)
    print(f"\nQuery: {initial_state['query']}")
    print(f"Budget: $5.00")
    print(f"Checkpointing: ENABLED")
    print(f"Circuit Breakers: ENABLED")
    print(f"Auto-retry: ENABLED\n")

    try:
        # Execute workflow with wflo wrapper
        final_state = await wflo.execute(app, initial_state)

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nSteps executed: {final_state['step_count']}")
        print(f"Total cost: ${final_state.get('cost_usd', 0):.4f}")
        print(f"Budget remaining: ${5.00 - final_state.get('cost_usd', 0):.4f}")
        print(f"\nFinal Report:\n{final_state['final_report'][:200]}...")

        # Wflo automatically provides:
        print("\n" + "=" * 60)
        print("WFLO FEATURES USED")
        print("=" * 60)
        print("✅ Cost tracked: Every LLM call monitored")
        print("✅ Budget enforced: Would stop at $5.00")
        print("✅ Checkpoints saved: 4 checkpoints created")
        print("✅ Circuit breakers: Protected each node")
        print("✅ Retries: Auto-retry on transient failures")
        print("✅ Observability: Full traces in Jaeger")
        print("✅ Rollback: Can restore to any checkpoint")

        # Show trace ID for debugging
        trace_id = wflo.get_trace_id()
        print(f"\nView trace: http://localhost:16686/trace/{trace_id}")

    except wflo.BudgetExceededError as e:
        print(f"\n⛔ BUDGET EXCEEDED: {e}")
        print(f"✅ Wflo stopped execution before burning money!")

        # Can rollback to last checkpoint
        print("\nRolling back to last successful checkpoint...")
        restored_state = await wflo.rollback_to_last_checkpoint()
        print(f"✅ Restored to step {restored_state['step_count']}")

    except wflo.CircuitOpenError as e:
        print(f"\n⚠️  CIRCUIT BREAKER OPENED: {e}")
        print(f"✅ Wflo protected against cascading failures!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

        # Wflo provides detailed error context
        error_context = wflo.get_error_context()
        print(f"\nError details:")
        print(f"  - Step: {error_context['step']}")
        print(f"  - Attempt: {error_context['attempt']}")
        print(f"  - Cost so far: ${error_context['cost_usd']:.4f}")

        # Can rollback
        print("\nRolling back to last checkpoint...")
        restored_state = await wflo.rollback_to_last_checkpoint()
        print(f"✅ Restored to step {restored_state['step_count']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
