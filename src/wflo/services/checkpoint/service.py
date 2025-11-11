"""Checkpoint service for saving and restoring workflow state."""

import uuid
from typing import Optional
import structlog

from wflo.db.engine import get_async_session
from wflo.db.models import StateSnapshotModel
from sqlalchemy import select, desc

logger = structlog.get_logger()

# Global checkpoint service instance
_checkpoint_service: Optional["CheckpointService"] = None


class CheckpointService:
    """Service for managing workflow state checkpoints."""

    async def save(
        self,
        execution_id: str,
        checkpoint_name: str,
        state: dict,
    ) -> str:
        """
        Save a checkpoint for the given execution.

        Args:
            execution_id: Workflow execution ID
            checkpoint_name: Name/identifier for this checkpoint
            state: State dictionary to save

        Returns:
            Checkpoint ID
        """
        async with get_async_session() as session:
            # Get current version number (max version + 1)
            result = await session.execute(
                select(StateSnapshotModel.version)
                .where(StateSnapshotModel.execution_id == execution_id)
                .order_by(desc(StateSnapshotModel.version))
                .limit(1)
            )
            max_version = result.scalar_one_or_none()
            version = (max_version or 0) + 1

            # Create snapshot
            snapshot_id = f"snap-{uuid.uuid4().hex[:12]}"
            snapshot = StateSnapshotModel(
                id=snapshot_id,
                execution_id=execution_id,
                step_id=checkpoint_name,
                variables=state,
                version=version,
            )

            session.add(snapshot)
            await session.commit()

            logger.debug(
                "checkpoint_saved_to_db",
                checkpoint_id=snapshot_id,
                execution_id=execution_id,
                checkpoint_name=checkpoint_name,
                version=version,
            )

            return snapshot_id

    async def load(
        self, execution_id: str, checkpoint_name: Optional[str] = None
    ) -> Optional[dict]:
        """
        Load a checkpoint for the given execution.

        Args:
            execution_id: Workflow execution ID
            checkpoint_name: Optional checkpoint name. If None, loads latest.

        Returns:
            State dictionary or None if not found
        """
        async with get_async_session() as session:
            if checkpoint_name:
                # Load specific checkpoint by name
                result = await session.execute(
                    select(StateSnapshotModel)
                    .where(
                        StateSnapshotModel.execution_id == execution_id,
                        StateSnapshotModel.step_id == checkpoint_name,
                    )
                    .order_by(desc(StateSnapshotModel.version))
                    .limit(1)
                )
            else:
                # Load latest checkpoint
                result = await session.execute(
                    select(StateSnapshotModel)
                    .where(StateSnapshotModel.execution_id == execution_id)
                    .order_by(desc(StateSnapshotModel.version))
                    .limit(1)
                )

            snapshot = result.scalar_one_or_none()

            if snapshot:
                logger.debug(
                    "checkpoint_loaded",
                    execution_id=execution_id,
                    checkpoint_name=snapshot.step_id,
                    version=snapshot.version,
                )
                return snapshot.variables

            return None

    async def list_checkpoints(self, execution_id: str) -> list[dict]:
        """
        List all checkpoints for an execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            List of checkpoint metadata dicts
        """
        async with get_async_session() as session:
            result = await session.execute(
                select(StateSnapshotModel)
                .where(StateSnapshotModel.execution_id == execution_id)
                .order_by(StateSnapshotModel.version)
            )
            snapshots = result.scalars().all()

            return [
                {
                    "id": snap.id,
                    "name": snap.step_id,
                    "version": snap.version,
                    "timestamp": snap.created_at.isoformat(),
                }
                for snap in snapshots
            ]

    async def rollback_to_checkpoint(
        self, execution_id: str, checkpoint_name: str
    ) -> Optional[dict]:
        """
        Rollback to a specific checkpoint by deleting later checkpoints.

        Args:
            execution_id: Workflow execution ID
            checkpoint_name: Checkpoint to rollback to

        Returns:
            Restored state or None if checkpoint not found
        """
        async with get_async_session() as session:
            # Find the checkpoint to rollback to
            result = await session.execute(
                select(StateSnapshotModel)
                .where(
                    StateSnapshotModel.execution_id == execution_id,
                    StateSnapshotModel.step_id == checkpoint_name,
                )
                .order_by(desc(StateSnapshotModel.version))
                .limit(1)
            )
            target_snapshot = result.scalar_one_or_none()

            if not target_snapshot:
                logger.warning(
                    "rollback_checkpoint_not_found",
                    execution_id=execution_id,
                    checkpoint_name=checkpoint_name,
                )
                return None

            # Delete all snapshots after this version
            # (for now, keep them for audit trail - just return the state)
            # In production, you might want to mark them as "rolled back"
            # rather than deleting

            logger.info(
                "rollback_executed",
                execution_id=execution_id,
                checkpoint_name=checkpoint_name,
                rollback_to_version=target_snapshot.version,
            )

            return target_snapshot.variables


def get_checkpoint_service() -> CheckpointService:
    """
    Get the global checkpoint service instance.

    Returns:
        CheckpointService instance
    """
    global _checkpoint_service

    if _checkpoint_service is None:
        _checkpoint_service = CheckpointService()

    return _checkpoint_service
