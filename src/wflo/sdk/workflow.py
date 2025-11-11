"""Main WfloWorkflow class for wrapping AI agent workflows with production features."""

import uuid
from typing import Any, Dict, Optional
import structlog

from wflo.sdk.context import ExecutionContext
from wflo.cost import CostTracker
from wflo.services.checkpoint import get_checkpoint_service
from wflo.db.engine import get_async_session
from wflo.db.models import WorkflowExecutionModel

logger = structlog.get_logger()


class BudgetExceededError(Exception):
    """Raised when workflow execution exceeds budget."""

    def __init__(self, message: str, spent_usd: float, budget_usd: float):
        super().__init__(message)
        self.spent_usd = spent_usd
        self.budget_usd = budget_usd


class WfloWorkflow:
    """
    Main wflo workflow wrapper for production-ready AI agent orchestration.

    Provides:
    - Automatic cost tracking
    - Budget enforcement
    - Automatic checkpointing
    - Rollback capability
    - Full observability

    Usage:
        wflo = WfloWorkflow(
            name="my-workflow",
            budget_usd=10.00,
            enable_checkpointing=True
        )

        result = await wflo.execute(workflow, inputs)
    """

    def __init__(
        self,
        name: str,
        budget_usd: float,
        per_agent_budgets: Optional[Dict[str, float]] = None,
        max_iterations: int = 100,
        enable_checkpointing: bool = True,
        enable_observability: bool = True,
    ):
        """
        Initialize wflo workflow wrapper.

        Args:
            name: Workflow name/identifier
            budget_usd: Total budget limit in USD
            per_agent_budgets: Optional per-agent budget limits
            max_iterations: Maximum iterations for iterative workflows
            enable_checkpointing: Enable automatic state checkpointing
            enable_observability: Enable metrics and tracing
        """
        self.name = name
        self.budget_usd = budget_usd
        self.per_agent_budgets = per_agent_budgets or {}
        self.max_iterations = max_iterations
        self.enable_checkpointing = enable_checkpointing
        self.enable_observability = enable_observability

        self.execution_id: Optional[str] = None
        self.cost_tracker = CostTracker()
        self.checkpoint_service = get_checkpoint_service()

    async def execute(self, workflow: Any, inputs: Dict[str, Any]) -> Any:
        """
        Execute workflow with wflo orchestration.

        Args:
            workflow: Workflow object (LangGraph, CrewAI, etc.)
            inputs: Input data for workflow

        Returns:
            Workflow execution result

        Raises:
            BudgetExceededError: If budget exceeded during execution
        """
        # Generate execution ID
        self.execution_id = f"exec-{uuid.uuid4().hex[:12]}"

        logger.info(
            "workflow_execution_started",
            execution_id=self.execution_id,
            workflow_name=self.name,
            budget_usd=self.budget_usd,
        )

        # Create execution record in database
        await self._create_execution_record(inputs)

        # Set execution context
        async with ExecutionContext(
            execution_id=self.execution_id, workflow_name=self.name
        ):
            try:
                # Detect workflow type and execute accordingly
                result = await self._execute_workflow(workflow, inputs)

                # Mark as completed
                await self._mark_completed(result)

                logger.info(
                    "workflow_execution_completed",
                    execution_id=self.execution_id,
                    workflow_name=self.name,
                )

                return result

            except BudgetExceededError:
                await self._mark_failed("budget_exceeded")
                raise

            except Exception as e:
                await self._mark_failed(str(e))
                logger.error(
                    "workflow_execution_failed",
                    execution_id=self.execution_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

    async def _execute_workflow(self, workflow: Any, inputs: Dict[str, Any]) -> Any:
        """
        Execute workflow based on its type.

        Args:
            workflow: Workflow object
            inputs: Input data

        Returns:
            Workflow result
        """
        # Check budget before execution
        await self.check_budget()

        # LangGraph workflow
        if hasattr(workflow, "__ainvoke__"):
            return await self._execute_langgraph(workflow, inputs)

        # CrewAI crew
        elif hasattr(workflow, "kickoff"):
            return await self._execute_crewai(workflow)

        # Generic callable
        elif callable(workflow):
            return await workflow(inputs)

        else:
            raise ValueError(f"Unsupported workflow type: {type(workflow)}")

    async def _execute_langgraph(self, workflow: Any, inputs: Dict[str, Any]) -> Any:
        """
        Execute LangGraph workflow with budget checking.

        Args:
            workflow: LangGraph compiled workflow
            inputs: Input state

        Returns:
            Final state
        """
        logger.debug("executing_langgraph_workflow", execution_id=self.execution_id)

        # Execute workflow
        # LangGraph workflows use ainvoke
        result = await workflow.ainvoke(inputs)

        # Check budget after execution
        await self.check_budget()

        return result

    async def _execute_crewai(self, crew: Any) -> Any:
        """
        Execute CrewAI crew with budget checking.

        Args:
            crew: CrewAI Crew object

        Returns:
            Crew execution result
        """
        logger.debug("executing_crewai_crew", execution_id=self.execution_id)

        # Execute crew
        result = crew.kickoff()

        # Check budget after execution
        await self.check_budget()

        return result

    async def check_budget(self) -> None:
        """
        Check if budget has been exceeded.

        Raises:
            BudgetExceededError: If budget exceeded
        """
        if not self.execution_id:
            return

        # Get total cost so far
        total_cost = await self.cost_tracker.get_total_cost(self.execution_id)

        if total_cost > self.budget_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${total_cost:.4f} > ${self.budget_usd:.2f}",
                spent_usd=total_cost,
                budget_usd=self.budget_usd,
            )

        logger.debug(
            "budget_check",
            execution_id=self.execution_id,
            spent_usd=total_cost,
            budget_usd=self.budget_usd,
            remaining_usd=self.budget_usd - total_cost,
        )

    async def checkpoint(self, name: str, state: Dict[str, Any]) -> None:
        """
        Manually create a checkpoint.

        Args:
            name: Checkpoint name
            state: State to save
        """
        if not self.enable_checkpointing or not self.execution_id:
            return

        await self.checkpoint_service.save(
            execution_id=self.execution_id, checkpoint_name=name, state=state
        )

    async def rollback_to_checkpoint(self, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        Rollback to a previous checkpoint.

        Args:
            checkpoint_name: Name of checkpoint to restore

        Returns:
            Restored state or None if not found
        """
        if not self.execution_id:
            return None

        return await self.checkpoint_service.rollback_to_checkpoint(
            execution_id=self.execution_id, checkpoint_name=checkpoint_name
        )

    async def rollback_to_last_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Rollback to the most recent checkpoint.

        Returns:
            Restored state or None if no checkpoints
        """
        if not self.execution_id:
            return None

        return await self.checkpoint_service.load(execution_id=self.execution_id)

    def list_checkpoints(self) -> list[dict]:
        """
        List all checkpoints for current execution.

        Returns:
            List of checkpoint metadata
        """
        if not self.execution_id:
            return []

        import asyncio

        return asyncio.run(self.checkpoint_service.list_checkpoints(self.execution_id))

    async def get_cost_breakdown(self) -> Dict[str, Any]:
        """
        Get cost breakdown for current execution.

        Returns:
            Dictionary with cost details
        """
        if not self.execution_id:
            return {}

        total_cost = await self.cost_tracker.get_total_cost(self.execution_id)

        return {
            "total_usd": total_cost,
            "budget_usd": self.budget_usd,
            "remaining_usd": max(0, self.budget_usd - total_cost),
            "exceeded": total_cost > self.budget_usd,
        }

    async def _create_execution_record(self, inputs: Dict[str, Any]) -> None:
        """Create execution record in database."""
        async with get_async_session() as session:
            execution = WorkflowExecutionModel(
                id=self.execution_id,
                workflow_definition_id=self.name,  # For now, use name as definition ID
                status="RUNNING",
                inputs=inputs,
                total_cost_usd=0.0,
            )
            session.add(execution)
            await session.commit()

    async def _mark_completed(self, result: Any) -> None:
        """Mark execution as completed."""
        async with get_async_session() as session:
            result = await session.get(WorkflowExecutionModel, self.execution_id)
            if result:
                result.status = "COMPLETED"
                result.outputs = {"result": str(result)} if result else {}
                await session.commit()

    async def _mark_failed(self, error: str) -> None:
        """Mark execution as failed."""
        async with get_async_session() as session:
            execution = await session.get(WorkflowExecutionModel, self.execution_id)
            if execution:
                execution.status = "FAILED"
                execution.error_message = error
                await session.commit()

    def get_trace_id(self) -> str:
        """
        Get trace ID for observability.

        Returns:
            Trace ID (same as execution ID)
        """
        return self.execution_id or "no-execution"
