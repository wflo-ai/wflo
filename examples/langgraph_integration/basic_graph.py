"""
Basic LangGraph example WITHOUT wflo integration.

This shows a simple research agent that:
1. Plans research steps
2. Executes web searches
3. Analyzes results
4. Generates final report

PROBLEMS with vanilla LangGraph:
- No cost tracking (could burn $$$)
- No budget limits
- No automatic retries on API failures
- Limited observability
- No rollback on errors
- No approval gates for expensive operations
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

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


# Node functions
async def plan_research(state: ResearchState) -> ResearchState:
    """Create research plan."""
    print(f"[STEP 1] Planning research for: {state['query']}")

    messages = [
        SystemMessage(content="You are a research planning assistant."),
        HumanMessage(content=f"Create a research plan for: {state['query']}")
    ]

    response = await llm.ainvoke(messages)
    state["plan"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Research plan created")
    return state


async def execute_searches(state: ResearchState) -> ResearchState:
    """Execute web searches based on plan."""
    print(f"[STEP 2] Executing searches...")

    # Simulate searches (in real app, would use tools)
    messages = [
        SystemMessage(content="You are a web search assistant."),
        HumanMessage(content=f"Based on this plan, what searches would you do?\n{state['plan']}")
    ]

    response = await llm.ainvoke(messages)
    state["search_results"] = [response.content]
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Found {len(state['search_results'])} results")
    return state


async def analyze_results(state: ResearchState) -> ResearchState:
    """Analyze search results."""
    print(f"[STEP 3] Analyzing results...")

    messages = [
        SystemMessage(content="You are a research analyst."),
        HumanMessage(content=f"Analyze these search results:\n{state['search_results']}")
    ]

    response = await llm.ainvoke(messages)
    state["analysis"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Analysis complete")
    return state


async def generate_report(state: ResearchState) -> ResearchState:
    """Generate final report."""
    print(f"[STEP 4] Generating final report...")

    messages = [
        SystemMessage(content="You are a report writer."),
        HumanMessage(content=f"Write a final report based on:\nQuery: {state['query']}\nAnalysis: {state['analysis']}")
    ]

    response = await llm.ainvoke(messages)
    state["final_report"] = response.content
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"✓ Report generated")
    return state


# Build the graph
def create_research_graph():
    """Create LangGraph workflow."""
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("plan", plan_research)
    workflow.add_node("search", execute_searches)
    workflow.add_node("analyze", analyze_results)
    workflow.add_node("report", generate_report)

    # Add edges (define flow)
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "analyze")
    workflow.add_edge("analyze", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# Run the workflow
async def main():
    """Run research workflow."""
    import asyncio

    app = create_research_graph()

    initial_state = {
        "query": "What are the latest advancements in AI agent frameworks in 2025?",
        "plan": "",
        "search_results": [],
        "analysis": "",
        "final_report": "",
        "step_count": 0
    }

    print("=" * 60)
    print("RUNNING VANILLA LANGGRAPH (NO WFLO)")
    print("=" * 60)
    print(f"\nQuery: {initial_state['query']}\n")

    try:
        # Execute workflow
        final_state = await app.ainvoke(initial_state)

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nSteps executed: {final_state['step_count']}")
        print(f"\nFinal Report:\n{final_state['final_report'][:200]}...")

        # PROBLEM: No cost tracking!
        print("\n⚠️  WARNING: No idea how much this cost!")
        print("⚠️  WARNING: No budget enforcement!")
        print("⚠️  WARNING: If this failed midway, we'd lose all state!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("⚠️  No automatic retry!")
        print("⚠️  No rollback capability!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
