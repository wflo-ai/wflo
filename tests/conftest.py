"""Shared pytest fixtures for all tests."""

import pytest


@pytest.fixture
def sample_workflow_id() -> str:
    """Sample workflow ID for testing."""
    return "test-workflow-123"


@pytest.fixture
def sample_execution_id() -> str:
    """Sample execution ID for testing."""
    return "exec-abc-123"
