"""
AutoGen conversation with wflo orchestration.

Demonstrates how wflo adds production features to AutoGen:
- Budget enforcement
- LLM call tracking
- Automatic cost calculation
- Checkpoint/rollback capability
"""

import asyncio
import os
from autogen import ConversableAgent

from wflo.sdk.workflow import WfloWorkflow
from wflo.sdk.decorators.track_llm import track_llm_call
from wflo.sdk.decorators.checkpoint import checkpoint


# Configure the LLM
llm_config = {
    "model": "gpt-4",
    "api_key": os.environ.get("OPENAI_API_KEY"),
    "temperature": 0.7,
}


class WfloAutogenAgent(ConversableAgent):
    """AutoGen agent wrapped with wflo tracking."""

    @track_llm_call(model="gpt-4")
    async def a_generate_reply(self, *args, **kwargs):
        """Override generate_reply to add LLM tracking."""
        # Call the original generate_reply method
        return await super().a_generate_reply(*args, **kwargs)


@checkpoint(name="conversation_complete")
async def run_conversation(user_message: str) -> dict:
    """
    Run AutoGen conversation with checkpoint.

    This allows rolling back to this state if needed.
    """
    # Create agents with wflo tracking
    user_proxy = WfloAutogenAgent(
        name="UserProxy",
        system_message="You are a helpful assistant.",
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
    )

    assistant = WfloAutogenAgent(
        name="Assistant",
        system_message="You are an AI assistant that helps with coding questions.",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # Run the conversation
    print(f"💬 Starting conversation: {user_message}")

    # Note: AutoGen's initiate_chat is sync, so we run it in executor
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(
            user_proxy.initiate_chat,
            assistant,
            message=user_message,
        )
        result = future.result()

    return {
        "status": "completed",
        "message_count": len(user_proxy.chat_messages.get(assistant, [])),
        "conversation": result,
    }


async def main():
    """Run AutoGen conversation with wflo orchestration."""
    print("🚀 Starting wflo-orchestrated AutoGen conversation...")
    print("=" * 60)

    # Create wflo workflow with budget
    workflow = WfloWorkflow(
        name="autogen-conversation",
        budget_usd=2.0,  # $2 budget
        enable_checkpointing=True,
        enable_observability=True,
    )

    try:
        # Execute the conversation
        result = await workflow.execute(
            run_conversation,
            {
                "user_message": "Can you explain what a decorator is in Python and provide a simple example?"
            },
        )

        print("\n" + "=" * 60)
        print("✅ Conversation complete!")
        print(f"📊 Messages exchanged: {result['message_count']}")

        # Get cost breakdown
        cost_breakdown = await workflow.get_cost_breakdown()
        print(f"\n💰 Cost Summary:")
        print(f"  Total: ${cost_breakdown['total_usd']:.4f}")
        print(f"  Budget: ${cost_breakdown['budget_usd']:.2f}")
        print(f"  Remaining: ${cost_breakdown['remaining_usd']:.4f}")
        print(f"  Budget exceeded: {cost_breakdown['exceeded']}")

        # Show execution ID for tracking
        print(f"\n🔍 Execution ID: {workflow.execution_id}")
        print(f"   Use this ID to retrieve execution details from the database")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
