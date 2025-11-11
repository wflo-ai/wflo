"""
Basic AutoGen conversation example.

Shows how AutoGen works without wflo - simple multi-agent conversation.
"""

import os
from autogen import ConversableAgent

# Configure the LLM
llm_config = {
    "model": "gpt-4",
    "api_key": os.environ.get("OPENAI_API_KEY"),
    "temperature": 0.7,
}


def main():
    """Run a basic two-agent conversation."""
    # Create a user proxy agent (represents the human)
    user_proxy = ConversableAgent(
        name="UserProxy",
        system_message="You are a helpful assistant.",
        llm_config=llm_config,
        human_input_mode="NEVER",  # Don't ask for human input
        max_consecutive_auto_reply=5,
    )

    # Create an assistant agent
    assistant = ConversableAgent(
        name="Assistant",
        system_message="You are an AI assistant that helps with coding questions.",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # Start the conversation
    print("🚀 Starting AutoGen conversation...")
    print("=" * 60)

    user_proxy.initiate_chat(
        assistant,
        message="Can you explain what a decorator is in Python and provide a simple example?",
    )

    print("=" * 60)
    print("✅ Conversation complete!")


if __name__ == "__main__":
    main()
