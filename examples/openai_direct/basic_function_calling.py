"""
OpenAI function calling agent WITHOUT wflo integration.

This shows a simple agent that can:
1. Search the web
2. Analyze data
3. Generate reports

PROBLEMS with vanilla OpenAI:
- No automatic cost tracking
- No budget limits (could burn thousands in a loop)
- Manual retry logic prone to errors
- Hard to debug when things go wrong
- No rollback if agent makes mistakes
- No approval before expensive operations
"""

import openai
import os
import json
from typing import List, Dict, Any

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define tools (functions the agent can call)
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

# Tool implementations
def search_web(query: str) -> str:
    """Simulate web search."""
    print(f"  🔍 Searching web: {query}")
    return f"Search results for '{query}': Latest AI frameworks show 46% growth..."

def analyze_data(data: List[float]) -> Dict[str, Any]:
    """Analyze data and return insights."""
    print(f"  📊 Analyzing {len(data)} data points")
    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "trend": "increasing" if data[-1] > data[0] else "decreasing"
    }

def generate_report(title: str, findings: List[str]) -> str:
    """Generate formatted report."""
    print(f"  📝 Generating report: {title}")
    report = f"# {title}\n\n"
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"
    return report

# Tool dispatcher
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

# Agent loop
def run_agent(user_query: str, max_iterations: int = 10):
    """Run agent with function calling."""

    messages = [
        {"role": "system", "content": "You are a helpful research assistant with access to web search, data analysis, and report generation tools."},
        {"role": "user", "content": user_query}
    ]

    print(f"\nUser Query: {user_query}\n")
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}]")

        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

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

            else:
                # Agent has final answer
                final_answer = message.content
                print(f"\n✅ Agent finished!\n")
                return final_answer

        except openai.APIError as e:
            print(f"  ❌ API Error: {e}")
            # Manual retry logic (prone to errors)
            print("  🔄 Retrying in 2s...")
            import time
            time.sleep(2)
            continue

    print(f"\n⚠️  Max iterations ({max_iterations}) reached!")
    return "Agent did not complete task"


def main():
    """Run function calling agent."""

    query = "Research AI agent frameworks in 2025 and generate a summary report"

    print("=" * 60)
    print("RUNNING VANILLA OPENAI FUNCTION CALLING (NO WFLO)")
    print("=" * 60)

    try:
        result = run_agent(query)

        print("=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(result)

        # PROBLEMS:
        print("\n" + "=" * 60)
        print("PROBLEMS WITH VANILLA OPENAI")
        print("=" * 60)
        print("⚠️  No idea how much this cost!")
        print("⚠️  No budget enforcement!")
        print("⚠️  If agent gets stuck in loop, could burn $$$!")
        print("⚠️  Manual retry logic is fragile!")
        print("⚠️  No checkpoints, can't rollback!")
        print("⚠️  Hard to debug what happened!")
        print("⚠️  No approval before expensive operations!")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("⚠️  Lost all progress!")


if __name__ == "__main__":
    main()
