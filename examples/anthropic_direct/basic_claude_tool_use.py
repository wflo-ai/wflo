"""
Basic Anthropic Claude tool use WITHOUT wflo.

Shows document analysis agent with tools.

PROBLEMS:
- No cost tracking (Claude charges per token)
- No budget limits
- Manual retries
- No checkpointing for long-running analysis
"""

import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [
    {
        "name": "analyze_document",
        "description": "Analyze a document and extract key insights",
        "input_schema": {
            "type": "object",
            "properties": {
                "document": {"type": "string"},
                "focus_areas": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["document"]
        }
    }
]

def analyze_document(document: str, focus_areas: list = None):
    """Analyze document."""
    print(f"📄 Analyzing document ({len(document)} chars)")
    return {"summary": "Document analyzed", "key_points": ["Point 1", "Point 2"]}

def run_claude_agent(query: str):
    """Run Claude with tool use."""
    messages = [{"role": "user", "content": query}]

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Claude finished
            return response.content[0].text

        elif response.stop_reason == "tool_use":
            # Claude wants to use a tool
            for content in response.content:
                if content.type == "tool_use":
                    tool_result = analyze_document(**content.input)
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": str(tool_result)
                        }]
                    })

def main():
    print("Running Claude WITHOUT wflo...")
    result = run_claude_agent("Analyze this document and summarize key points")
    print(f"\nResult: {result}")
    print("\n⚠️  No cost tracking!")
    print("⚠️  No budget limits!")

if __name__ == "__main__":
    main()
