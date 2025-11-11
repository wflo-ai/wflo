"""
OpenAI function calling WITH wflo integration (Phase 1 features).

This demonstrates the actual implemented features:
✅ Automatic cost tracking per LLM call
✅ Budget enforcement (stops if exceeds budget)
✅ Automatic checkpointing after each iteration
✅ Rollback capability on errors
✅ Full observability (traces, logs)

NOTE: This uses the Phase 1 SDK implementation.
Loop detection, circuit breakers and retry logic will be added in Phase 2.
"""

import openai
import os
import json
from typing import List, Dict, Any
import asyncio

# Wflo imports - Phase 1 features
from wflo.sdk import WfloWorkflow, BudgetExceededError, track_llm_call, checkpoint

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a formatted report",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "findings": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["title", "findings"]
            }
        }
    }
]


# Tool implementations (simulated)
def search_web(query: str) -> str:
    """Simulate web search."""
    print(f"  🔍 Searching: {query}")
    return f"Search results for '{query}': Latest AI frameworks include LangGraph, CrewAI, AutoGen..."


def generate_report(title: str, findings: List[str]) -> str:
    """Generate formatted report."""
    print(f"  📝 Generating report: {title}")
    report = f"# {title}\n\n"
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"
    return report


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool."""
    if tool_name == "search_web":
        return search_web(**arguments)
    elif tool_name == "generate_report":
        return generate_report(**arguments)
    return f"Unknown tool: {tool_name}"


# Wrap LLM call with wflo tracking
@track_llm_call(model="gpt-4")
async def call_openai_with_tools(messages: List[Dict], tools: List[Dict]) -> Any:
    """
    Call OpenAI API with cost tracking.

    This is wrapped as async to match the decorator signature,
    but OpenAI sync client is used internally.
    """
    # Note: OpenAI Python SDK's chat.completions.create is synchronous
    # In a real async app, you'd use the AsyncOpenAI client
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    return response


# Agent loop
async def run_agent_with_wflo(user_query: str, wflo: WfloWorkflow, max_iterations: int = 5):
    """Run agent loop with wflo orchestration."""
    messages = [
        {"role": "system", "content": "You are a helpful research assistant with access to web search and report generation tools."},
        {"role": "user", "content": user_query}
    ]

    print(f"\nUser Query: {user_query}\n")
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}]")

        # Save checkpoint before LLM call
        await wflo.checkpoint(f"iteration_{iteration}_start", {
            "messages": messages,
            "iteration": iteration
        })

        # Call OpenAI with cost tracking
        response = await call_openai_with_tools(messages, tools)
        message = response.choices[0].message

        # Check budget after each call
        await wflo.check_budget()

        # Check if agent wants to call a function
        if message.tool_calls:
            # Agent wants to use tools
            messages.append(message)

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"  🤖 Agent calling: {function_name}({function_args})")

                # Execute tool
                tool_result = execute_tool(function_name, function_args)

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result
                })

                # Checkpoint after tool execution
                await wflo.checkpoint(f"iteration_{iteration}_tool_{function_name}", {
                    "messages": messages,
                    "tool": function_name,
                    "iteration": iteration
                })

        else:
            # Agent has final answer
            final_answer = message.content
            print(f"\n✅ Agent finished!\n")
            return final_answer

    print(f"\n⚠️  Max iterations ({max_iterations}) reached!")
    return "Agent did not complete task"


async def main():
    """Run function calling agent with wflo."""

    query = "Search for AI agent frameworks in 2025 and generate a summary report"

    # Create wflo workflow
    wflo = WfloWorkflow(
        name="research-agent",
        budget_usd=2.00,  # Hard budget limit
        max_iterations=10,
        enable_checkpointing=True,
        enable_observability=True
    )

    print("=" * 60)
    print("RUNNING OPENAI FUNCTION CALLING WITH WFLO (Phase 1)")
    print("=" * 60)
    print(f"\nBudget: $2.00")
    print(f"Max iterations: 10")
    print(f"\nPhase 1 Features:")
    print(f"  ✅ Cost tracking per LLM call")
    print(f"  ✅ Budget enforcement")
    print(f"  ✅ Checkpointing after each iteration")
    print(f"  ✅ Rollback capability")
    print(f"  ✅ Full observability")

    try:
        # Execute agent with wflo
        # Note: We wrap the agent loop in wflo.execute for database tracking
        result = await wflo.execute(
            lambda _: run_agent_with_wflo(query, wflo),
            {}
        )

        print("=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(result)

        # Show cost breakdown
        cost_breakdown = await wflo.get_cost_breakdown()
        print("\n" + "=" * 60)
        print("COST BREAKDOWN")
        print("=" * 60)
        print(f"Total cost: ${cost_breakdown['total_usd']:.4f}")
        print(f"Budget: ${cost_breakdown['budget_usd']:.2f}")
        print(f"Remaining: ${cost_breakdown['remaining_usd']:.4f}")
        print(f"Exceeded: {cost_breakdown['exceeded']}")

        # Show checkpoints
        checkpoints = wflo.list_checkpoints()
        print("\n" + "=" * 60)
        print(f"CHECKPOINTS SAVED ({len(checkpoints)})")
        print("=" * 60)
        for cp in checkpoints[:5]:  # Show first 5
            print(f"  ✓ {cp['name']} (v{cp['version']})")

        # Show trace ID
        trace_id = wflo.get_trace_id()
        print(f"\nTrace ID: {trace_id}")

    except BudgetExceededError as e:
        print(f"\n⛔ EXECUTION STOPPED: Budget exceeded")
        print(f"   Spent: ${e.spent_usd:.4f}")
        print(f"   Budget: ${e.budget_usd:.2f}")
        print(f"\n✅ Wflo stopped agent before burning all budget!")

        # Rollback to last checkpoint
        print("\n📝 Rolling back to last checkpoint...")
        restored = await wflo.rollback_to_last_checkpoint()
        if restored:
            print(f"✅ Restored to iteration {restored.get('iteration', '?')}")
            print(f"   Can resume from here with increased budget")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Type: {type(e).__name__}")

        # Rollback capability
        print("\n📝 Rolling back to last checkpoint...")
        restored = await wflo.rollback_to_last_checkpoint()
        if restored:
            print(f"✅ Restored to iteration {restored.get('iteration', '?')}")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        exit(1)

    asyncio.run(main())
