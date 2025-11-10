"""Database engine and session management.

This module provides async SQLAlchemy engine and session management
with connection pooling and health checks.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from wflo.config.settings import Settings


class DatabaseEngine:
    """Manages database engine and session lifecycle.

    Provides connection pooling, health checks, and session management
    for PostgreSQL using asyncpg.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize database engine.

        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        """Get or create the database engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine

        Note:
            Engine is created with connection pooling enabled by default.
            Use NullPool for testing environments.
        """
        if self._engine is None:
            # Determine pool class based on environment
            pool_class = (
                NullPool if self.settings.app_env == "testing" else QueuePool
            )

            self._engine = create_async_engine(
                str(self.settings.database_url),
                echo=self.settings.database_echo,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_timeout=self.settings.database_pool_timeout,
                pool_recycle=self.settings.database_pool_recycle,
                pool_pre_ping=True,  # Enable connection health checks
                poolclass=pool_class,
            )

        return self._engine

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session maker.

        Returns:
            async_sessionmaker: Session factory for creating database sessions
        """
        if self._session_maker is None:
            self._session_maker = async_sessionmaker(
                bind=self.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

        return self._session_maker

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session with automatic cleanup.

        Yields:
            AsyncSession: Database session

        Example:
            async with engine.session() as session:
                result = await session.execute(select(Workflow))
        """
        session_maker = self.get_session_maker()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity.

        Returns:
            bool: True if database is reachable and responsive

        Raises:
            Exception: If database connection fails
        """
        from sqlalchemy import text

        async with self.session() as session:
            await session.execute(text("SELECT 1"))
        return True

    async def close(self) -> None:
        """Close database engine and cleanup connections.

        Should be called during application shutdown.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None


# Global database engine instance
_db_engine: DatabaseEngine | None = None


def init_db(settings: Settings) -> DatabaseEngine:
    """Initialize the global database engine.

    Args:
        settings: Application settings

    Returns:
        DatabaseEngine: Initialized database engine
    """
    global _db_engine
    _db_engine = DatabaseEngine(settings)
    return _db_engine


def get_engine() -> AsyncEngine:
    """Get the global database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine

    Raises:
        RuntimeError: If database not initialized with init_db()
    """
    if _db_engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db(settings) first."
        )
    return _db_engine.get_engine()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session (dependency injection compatible).

    Yields:
        AsyncSession: Database session

    Example:
        # FastAPI dependency
        async def get_workflows(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Workflow))
            return result.scalars().all()
    """
    if _db_engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db(settings) first."
        )

    async with _db_engine.session() as session:
        yield session
