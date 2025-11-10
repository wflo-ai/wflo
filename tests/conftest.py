"""Shared pytest fixtures for all tests."""

import os
from collections.abc import AsyncGenerator

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from wflo.cache.redis import get_redis_client
from wflo.config.settings import Settings
from wflo.db.engine import DatabaseEngine
from wflo.db.models import Base


@pytest.fixture
def sample_workflow_id() -> str:
    """Sample workflow ID for testing."""
    return "test-workflow-123"


@pytest.fixture
def sample_execution_id() -> str:
    """Sample execution ID for testing."""
    return "exec-abc-123"


# Integration test fixtures for database


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get test database URL from environment or use default.

    Set TEST_DATABASE_URL environment variable to override.
    Default: postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test
    """
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo_test",
    )


@pytest.fixture(scope="session")
def test_settings(test_db_url: str) -> Settings:
    """Create test settings with test database URL."""
    return Settings(
        app_env="testing",
        database_url=test_db_url,
        database_echo=False,  # Set to True for SQL debugging
    )


@pytest.fixture(scope="function")
async def db_engine(test_settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine and setup/teardown tables.

    This fixture:
    1. Creates all tables before the test
    2. Yields the engine for use in tests
    3. Drops all tables after the test (cleanup)
    """
    engine_manager = DatabaseEngine(test_settings)
    engine = engine_manager.get_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables (cleanup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await engine_manager.close()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing.

    This creates a new session for each test and handles cleanup.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Redis fixtures


@pytest.fixture
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Create a Redis client for testing.

    This creates a new Redis connection for each test in the correct event loop,
    preventing "Event loop is closed" errors.
    """
    async with get_redis_client() as client:
        yield client
