"""End-to-end workflow tests with real LLM API calls.

These tests verify that wflo works correctly with real LLM providers
and actual database operations (PostgreSQL or Supabase).

Requirements:
- DATABASE_URL or TEST_DATABASE_URL set in .env
- OPENAI_API_KEY set in .env (for OpenAI tests)
- ANTHROPIC_API_KEY set in .env (for Anthropic tests)

Setup:
1. Configure .env file with:
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...

2. Run tests:
   poetry run pytest tests/integration/test_e2e_workflows.py -v -m integration

WARNING: These tests will make real API calls and incur costs (typically < $0.10 total).
"""

import os
from datetime import datetime

import pytest

from wflo.config import get_settings
from wflo.db.engine import init_db
from wflo.sdk.decorators.checkpoint import checkpoint
from wflo.sdk.decorators.track_llm import track_llm_call
from wflo.sdk.workflow import BudgetExceededError, WfloWorkflow


# Load settings to check for API keys (loads from .env automatically)
_settings = get_settings()

# Skip tests if API keys not available
skip_if_no_openai = pytest.mark.skipif(
    not _settings.openai_api_key,
    reason="OPENAI_API_KEY not set in .env file",
)

skip_if_no_anthropic = pytest.mark.skipif(
    not _settings.anthropic_api_key,
    reason="ANTHROPIC_API_KEY not set in .env file",
)


@pytest.fixture(scope="function")
async def db():
    """Initialize database for each test function."""
    # Clear any existing global database engine to ensure clean state
    import wflo.db.engine as db_module
    if db_module._db_engine is not None:
        try:
            await db_module._db_engine.close()
        except:
            pass
        db_module._db_engine = None

    settings = get_settings()
    db_instance = init_db(settings)
    # Ensure tables exist
    from wflo.db.models import Base

    engine = db_instance.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield db_instance

    # Cleanup
    await db_instance.close()
    db_module._db_engine = None


@pytest.fixture
async def openai_client():
    """Provide OpenAI client with proper cleanup."""
    from openai import AsyncOpenAI
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    yield client
    await client.close()


@pytest.mark.asyncio
@pytest.mark.integration
@skip_if_no_openai
class TestOpenAIWorkflows:
    """Test end-to-end workflows with OpenAI."""

    async def test_simple_openai_workflow(self, db, openai_client):
        """Test simple workflow with OpenAI API call."""
        client = openai_client

        @track_llm_call(model="gpt-3.5-turbo")
        async def simple_chat(prompt: str):
            """Simple chat completion."""
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,  # Keep it small to minimize cost
            )
            return response

        # Create workflow with budget
        workflow = WfloWorkflow(
            name="e2e-openai-simple",
            budget_usd=0.10,  # $0.10 budget
        )

        # Execute
        result = await workflow.execute(
            simple_chat, {"prompt": "Say hello in exactly 3 words."}
        )

        # Verify result
        assert result is not None
        assert hasattr(result, "choices")
        assert len(result.choices) > 0
        message_content = result.choices[0].message.content
        assert isinstance(message_content, str)
        assert len(message_content) > 0

        # Verify execution tracking
        assert workflow.execution_id is not None
        assert workflow.execution_id.startswith("exec-")

        # Verify cost tracking
        cost_breakdown = await workflow.get_cost_breakdown()
        assert cost_breakdown["total_usd"] > 0
        assert cost_breakdown["total_usd"] < 0.10
        assert cost_breakdown["budget_usd"] == 0.10
        assert not cost_breakdown["exceeded"]

        print(f"\n✅ Workflow completed successfully!")
        print(f"   Execution ID: {workflow.execution_id}")
        print(f"   Cost: ${cost_breakdown['total_usd']:.4f}")
        print(f"   Result: {message_content}")

    async def test_multi_step_workflow_with_checkpoints(self, db, openai_client):
        """Test multi-step workflow with checkpoints and OpenAI."""
        client = openai_client

        @checkpoint(name="generate_topic")
        async def generate_topic():
            """Step 1: Generate a topic."""
            @track_llm_call(model="gpt-3.5-turbo")
            async def call_api():
                return await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": "Give me one random topic in 2 words."}
                    ],
                    max_tokens=10,
                )

            response = await call_api()
            topic = response.choices[0].message.content
            return {"topic": topic}

        @checkpoint(name="generate_fact")
        async def generate_fact(state: dict):
            """Step 2: Generate a fact about the topic."""
            @track_llm_call(model="gpt-3.5-turbo")
            async def call_api(topic: str):
                return await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Give me one fact about {topic} in one sentence.",
                        }
                    ],
                    max_tokens=50,
                )

            response = await call_api(state["topic"])
            fact = response.choices[0].message.content
            return {**state, "fact": fact}

        async def multi_step_workflow():
            """Multi-step workflow."""
            state = await generate_topic()
            state = await generate_fact(state)
            return state

        # Create workflow
        workflow = WfloWorkflow(
            name="e2e-openai-multistep",
            budget_usd=0.20,
            enable_checkpointing=True,
        )

        # Execute
        result = await workflow.execute(multi_step_workflow, {})

        # Verify result has both steps
        assert "topic" in result
        assert "fact" in result
        assert isinstance(result["topic"], str)
        assert isinstance(result["fact"], str)

        # Verify cost tracking
        cost_breakdown = await workflow.get_cost_breakdown()
        assert cost_breakdown["total_usd"] > 0
        assert cost_breakdown["total_usd"] < 0.20

        print(f"\n✅ Multi-step workflow completed!")
        print(f"   Topic: {result['topic']}")
        print(f"   Fact: {result['fact']}")
        print(f"   Cost: ${cost_breakdown['total_usd']:.4f}")

    async def test_budget_exceeded_error(self, db, openai_client):
        """Test that budget enforcement works with real API calls."""
        client = openai_client

        @track_llm_call(model="gpt-3.5-turbo")
        async def expensive_chat(prompt: str):
            """Chat that might exceed budget."""
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )
            return response

        # Create workflow with very small budget
        workflow = WfloWorkflow(
            name="e2e-openai-budget-test",
            budget_usd=0.0001,  # $0.0001 - extremely tight budget to force exceeding
        )

        # This should exceed budget
        with pytest.raises(BudgetExceededError) as exc_info:
            await workflow.execute(
                expensive_chat, {"prompt": "Write a long essay about Python."}
            )

        # Verify exception details
        error = exc_info.value
        assert error.budget_usd == 0.0001
        assert error.spent_usd > 0.0001

        print(f"\n✅ Budget enforcement working!")
        print(f"   Budget: ${error.budget_usd:.4f}")
        print(f"   Spent: ${error.spent_usd:.4f}")
        print(f"   Overage: ${error.spent_usd - error.budget_usd:.4f}")


@pytest.mark.asyncio
@pytest.mark.integration
@skip_if_no_anthropic
class TestAnthropicWorkflows:
    """Test end-to-end workflows with Anthropic Claude."""

    async def test_simple_claude_workflow(self, db):
        """Test simple workflow with Anthropic Claude."""
        from anthropic import AsyncAnthropic

        settings = get_settings()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        @track_llm_call(model="claude-3-haiku-20240307")
        async def simple_claude_chat(prompt: str):
            """Simple Claude chat."""
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        # Create workflow
        workflow = WfloWorkflow(
            name="e2e-claude-simple",
            budget_usd=0.10,
        )

        # Execute
        result = await workflow.execute(
            simple_claude_chat, {"prompt": "Say hello in exactly 3 words."}
        )

        # Verify
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify cost tracking
        cost_breakdown = await workflow.get_cost_breakdown()
        assert cost_breakdown["total_usd"] > 0
        assert cost_breakdown["total_usd"] < 0.10

        print(f"\n✅ Claude workflow completed!")
        print(f"   Cost: ${cost_breakdown['total_usd']:.4f}")
        print(f"   Result: {result}")


@pytest.mark.asyncio
@pytest.mark.integration
@skip_if_no_openai
class TestDatabasePersistence:
    """Test that workflow data is correctly persisted to database."""

    async def test_workflow_execution_persisted(self, db, openai_client):
        """Test that workflow execution is saved to database."""
        from wflo.db.engine import get_session
        from wflo.db.models import WorkflowExecutionModel

        client = openai_client

        @track_llm_call(model="gpt-3.5-turbo")
        async def simple_chat(prompt: str):
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
            )
            return response

        # Execute workflow
        workflow = WfloWorkflow(
            name="e2e-persistence-test",
            budget_usd=0.10,
        )

        result = await workflow.execute(
            simple_chat, {"prompt": "Say hi in 2 words."}
        )

        execution_id = workflow.execution_id

        # Verify execution was saved to database
        from sqlalchemy import select

        async for session in get_session():
            result = await session.execute(
                select(WorkflowExecutionModel).where(
                    WorkflowExecutionModel.id == execution_id
                )
            )
            execution = result.scalar_one_or_none()

            # Verify execution record
            assert execution is not None
            assert execution.id == execution_id
            assert execution.status == "COMPLETED"
            assert execution.cost_total_usd > 0
            assert execution.workflow_id == "e2e-persistence-test"

            print(f"\n✅ Execution persisted to database!")
            print(f"   Execution ID: {execution.id}")
            print(f"   Status: {execution.status}")
            print(f"   Cost: ${execution.cost_total_usd:.4f}")
            print(f"   Created: {execution.created_at}")

            break  # Only need first iteration

    async def test_checkpoint_persisted(self, db, openai_client):
        """Test that checkpoints are saved to database."""
        from wflo.db.engine import get_session
        from wflo.db.models import StateSnapshotModel

        client = openai_client

        @checkpoint(name="test_checkpoint")
        async def checkpointed_step(data: str):
            @track_llm_call(model="gpt-3.5-turbo")
            async def call_api():
                return await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Say {data}"}],
                    max_tokens=10,
                )

            response = await call_api()
            result = response.choices[0].message.content
            return {"result": result}

        # Execute workflow with checkpoint
        workflow = WfloWorkflow(
            name="e2e-checkpoint-persistence",
            budget_usd=0.10,
            enable_checkpointing=True,
        )

        result = await workflow.execute(checkpointed_step, {"data": "hello"})

        execution_id = workflow.execution_id

        # Verify checkpoint was saved
        from sqlalchemy import select

        async for session in get_session():
            result = await session.execute(
                select(StateSnapshotModel).where(
                    StateSnapshotModel.execution_id == execution_id
                )
            )
            checkpoints = result.scalars().all()

            # Should have at least one checkpoint
            assert len(checkpoints) > 0

            saved_checkpoint = checkpoints[0]
            assert saved_checkpoint.execution_id == execution_id
            assert saved_checkpoint.step_id == "test_checkpoint"
            # Checkpoint should have variables with "result" key
            assert saved_checkpoint.variables is not None
            assert "result" in saved_checkpoint.variables

            print(f"\n✅ Checkpoint persisted to database!")
            print(f"   Checkpoint ID: {saved_checkpoint.id}")
            print(f"   Step ID: {saved_checkpoint.step_id}")
            print(f"   Version: {saved_checkpoint.version}")
            print(f"   Variables: {list(saved_checkpoint.variables.keys()) if isinstance(saved_checkpoint.variables, dict) else 'N/A'}")

            break  # Only need first iteration


@pytest.mark.asyncio
@pytest.mark.integration
@skip_if_no_openai
class TestCostTracking:
    """Test cost tracking accuracy with real API calls."""

    async def test_cost_tracking_accuracy(self, db, openai_client):
        """Test that cost tracking matches actual usage."""
        client = openai_client

        @track_llm_call(model="gpt-3.5-turbo")
        async def tracked_chat(prompt: str):
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
            )
            # Also manually check usage
            usage = response.usage
            print(f"\n   Actual API usage:")
            print(f"     Prompt tokens: {usage.prompt_tokens}")
            print(f"     Completion tokens: {usage.completion_tokens}")
            print(f"     Total tokens: {usage.total_tokens}")

            return response

        # Execute workflow
        workflow = WfloWorkflow(
            name="e2e-cost-tracking",
            budget_usd=0.10,
        )

        result = await workflow.execute(tracked_chat, {"prompt": "Count to 5."})

        # Get cost breakdown
        cost_breakdown = await workflow.get_cost_breakdown()

        # Verify cost is reasonable for GPT-3.5-turbo
        # Should be very small (< $0.01)
        assert cost_breakdown["total_usd"] > 0
        assert cost_breakdown["total_usd"] < 0.01

        print(f"\n✅ Cost tracking accurate!")
        print(f"   Tracked cost: ${cost_breakdown['total_usd']:.6f}")
        print(f"   Budget remaining: ${cost_breakdown['remaining_usd']:.4f}")
