"""
OpenAI function calling agent WITH wflo integration.

This shows the SAME agent but with wflo for production readiness:
✅ Automatic cost tracking per iteration
✅ Budget enforcement (stops if exceeds $2)
✅ Automatic checkpointing after each tool call
✅ Circuit breakers on API failures
✅ Automatic retry with exponential backoff
✅ Full observability of agent loop
✅ Rollback capability on errors
✅ Infinite loop detection and prevention
"""

import openai
import os
import json
from typing import List, Dict, Any

# Wflo imports
from wflo.sdk import WfloAgent, track_llm_call, checkpoint, with_retry
from wflo.sdk.decorators import circuit_breaker, track_tool_call
from wflo.sdk.loop_detection import detect_infinite_loop

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define tools (same as before)
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
            "name": "analyze_data",
            "description": "Analyze numerical data and return insights",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Array of numbers to analyze"
                    }
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a formatted report from findings",
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

# Tool implementations wrapped with wflo tracking
@track_tool_call(tool_name="search_web")
def search_web(query: str) -> str:
    """Simulate web search with tracking."""
    print(f"  🔍 Searching web: {query}")
    return f"Search results for '{query}': Latest AI frameworks show 46% growth..."

@track_tool_call(tool_name="analyze_data")
def analyze_data(data: List[float]) -> Dict[str, Any]:
    """Analyze data with tracking."""
    print(f"  📊 Analyzing {len(data)} data points")
    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "trend": "increasing" if data[-1] > data[0] else "decreasing"
    }

@track_tool_call(tool_name="generate_report")
def generate_report(title: str, findings: List[str]) -> str:
    """Generate report with tracking."""
    print(f"  📝 Generating report: {title}")
    report = f"# {title}\n\n"
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"
    return report

# Tool dispatcher (same as before)
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool and return result."""
    if tool_name == "search_web":
        return search_web(**arguments)
    elif tool_name == "analyze_data":
        result = analyze_data(**arguments)
        return json.dumps(result)
    elif tool_name == "generate_report":
        return generate_report(**arguments)
    else:
        return f"Unknown tool: {tool_name}"

# Agent loop with wflo protection
@circuit_breaker(name="openai-agent", token_budget=100000, error_threshold=0.3)
@detect_infinite_loop(max_iterations=10, similarity_threshold=0.9)
async def run_agent_with_wflo(user_query: str, wflo: WfloAgent):
    """Run agent with wflo orchestration."""

    messages = [
        {"role": "system", "content": "You are a helpful research assistant with access to web search, data analysis, and report generation tools."},
        {"role": "user", "content": user_query}
    ]

    print(f"\nUser Query: {user_query}\n")
    iteration = 0

    while iteration < wflo.max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}]")

        # Checkpoint before LLM call
        await wflo.checkpoint(f"iteration_{iteration}_start", {
            "messages": messages,
            "iteration": iteration
        })

        try:
            # Call OpenAI API with automatic retry and cost tracking
            @track_llm_call(model="gpt-4")
            @with_retry(max_attempts=3, backoff="exponential")
            async def call_llm():
                return client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

            response = await call_llm()
            message = response.choices[0].message

            # Check budget after each call
            await wflo.check_budget()

            # Check if agent wants to call a function
            if message.tool_calls:
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

                    # Checkpoint after each tool call
                    await wflo.checkpoint(f"iteration_{iteration}_tool_{function_name}", {
                        "messages": messages,
                        "tool_call": function_name,
                        "tool_result": tool_result
                    })

            else:
                # Agent has final answer
                final_answer = message.content
                print(f"\n✅ Agent finished!\n")

                # Final checkpoint
                await wflo.checkpoint("final_answer", {
                    "messages": messages,
                    "final_answer": final_answer
                })

                return final_answer

        except wflo.BudgetExceededError as e:
            print(f"\n⛔ BUDGET EXCEEDED at iteration {iteration}")
            print(f"   Spent: ${e.spent_usd:.4f} / ${e.budget_usd:.2f}")
            raise

        except wflo.InfiniteLoopDetectedError as e:
            print(f"\n🔁 INFINITE LOOP DETECTED at iteration {iteration}")
            print(f"   Agent repeating similar actions")
            print(f"   Similarity: {e.similarity:.2%}")
            raise

        except openai.APIError as e:
            print(f"  ❌ API Error: {e}")
            # Wflo automatically retries with backoff
            # This exception only raised after all retries exhausted
            raise

    print(f"\n⚠️  Max iterations ({wflo.max_iterations}) reached!")
    return "Agent did not complete task"


async def main():
    """Run function calling agent with wflo."""
    import asyncio

    query = "Research AI agent frameworks in 2025 and generate a summary report"

    # Initialize wflo
    wflo = WfloAgent(
        name="research-agent",
        budget_usd=2.00,  # Hard budget limit
        max_iterations=10,
        enable_checkpointing=True,
        enable_loop_detection=True,
        enable_observability=True
    )

    print("=" * 60)
    print("RUNNING OPENAI FUNCTION CALLING WITH WFLO")
    print("=" * 60)
    print(f"\nBudget: $2.00")
    print(f"Max iterations: 10")
    print(f"Features enabled:")
    print(f"  ✅ Cost tracking per LLM call")
    print(f"  ✅ Budget enforcement")
    print(f"  ✅ Checkpointing after each tool call")
    print(f"  ✅ Circuit breakers")
    print(f"  ✅ Auto-retry with exponential backoff")
    print(f"  ✅ Infinite loop detection")
    print(f"  ✅ Full observability")

    try:
        result = await run_agent_with_wflo(query, wflo)

        print("=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(result)

        # Show cost breakdown
        cost_breakdown = wflo.get_cost_breakdown()
        print("\n" + "=" * 60)
        print("COST BREAKDOWN")
        print("=" * 60)
        print(f"Total cost: ${cost_breakdown['total_usd']:.4f}")
        print(f"Budget: ${cost_breakdown['budget_usd']:.2f}")
        print(f"Remaining: ${cost_breakdown['remaining_usd']:.4f}")
        print(f"\nLLM calls: {cost_breakdown['llm_calls']}")
        print(f"  Input tokens: {cost_breakdown['input_tokens']:,}")
        print(f"  Output tokens: {cost_breakdown['output_tokens']:,}")
        print(f"\nTool calls: {cost_breakdown['tool_calls']}")
        for tool_name, count in cost_breakdown['tool_counts'].items():
            print(f"  {tool_name}: {count} calls")

        # Show checkpoints
        checkpoints = wflo.list_checkpoints()
        print("\n" + "=" * 60)
        print(f"CHECKPOINTS SAVED ({len(checkpoints)})")
        print("=" * 60)
        for cp in checkpoints[:5]:  # Show first 5
            print(f"  ✓ {cp['name']} - {cp['timestamp']}")

        # Show metrics
        metrics = wflo.get_metrics()
        print("\n" + "=" * 60)
        print("METRICS")
        print("=" * 60)
        print(f"Total iterations: {metrics['iterations']}")
        print(f"Average time per iteration: {metrics['avg_iteration_time_ms']:.0f}ms")
        print(f"Retries: {metrics['retries']}")
        print(f"Circuit breaker trips: {metrics['circuit_breaker_trips']}")

        # Show trace
        trace_id = wflo.get_trace_id()
        print(f"\nView trace: http://localhost:16686/trace/{trace_id}")

    except wflo.BudgetExceededError as e:
        print(f"\n⛔ EXECUTION STOPPED: Budget exceeded")
        print(f"   Spent: ${e.spent_usd:.4f}")
        print(f"   Budget: ${e.budget_usd:.2f}")

        # Can rollback to last successful checkpoint
        print("\nRolling back to last checkpoint...")
        restored = await wflo.rollback_to_last_checkpoint()
        print(f"✅ Restored to: {restored['checkpoint_name']}")
        print(f"   Can resume from here with increased budget")

    except wflo.InfiniteLoopDetectedError as e:
        print(f"\n🔁 EXECUTION STOPPED: Infinite loop detected")
        print(f"   Agent stuck at iteration {e.iteration}")
        print(f"   Similarity: {e.similarity:.2%}")

        # Show what agent was repeating
        print(f"\nRepeated pattern:")
        print(f"   {e.repeated_pattern}")

        # Can rollback and retry with different prompt
        print("\nRolling back to start...")
        restored = await wflo.rollback_to_checkpoint("iteration_1_start")
        print(f"✅ Can retry with modified prompt")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

        error_context = wflo.get_error_context()
        print(f"\nError context:")
        print(f"  Iteration: {error_context['iteration']}")
        print(f"  Cost so far: ${error_context['cost_usd']:.4f}")
        print(f"  Last checkpoint: {error_context['last_checkpoint']}")

        print("\nRolling back...")
        restored = await wflo.rollback_to_last_checkpoint()
        print(f"✅ Restored to: {restored['checkpoint_name']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
