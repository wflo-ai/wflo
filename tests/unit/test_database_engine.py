"""Unit tests for database engine and session management."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool

from wflo.config.settings import Settings
from wflo.db.engine import DatabaseEngine, get_engine, init_db


class TestDatabaseEngine:
    """Tests for DatabaseEngine class."""

    def test_engine_initialization(self):
        """Test DatabaseEngine can be initialized with settings."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        assert engine.settings == settings
        assert engine._engine is None
        assert engine._session_maker is None

    def test_get_engine_creates_engine(self):
        """Test get_engine() creates an AsyncEngine on first call."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert isinstance(async_engine, AsyncEngine)
        assert engine._engine is async_engine

    def test_get_engine_returns_cached_engine(self):
        """Test get_engine() returns the same engine on subsequent calls."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        engine1 = engine.get_engine()
        engine2 = engine.get_engine()

        assert engine1 is engine2

    def test_engine_uses_queue_pool_in_production(self):
        """Test engine uses QueuePool in non-testing environments."""
        settings = Settings(app_env="production")
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert isinstance(async_engine.pool, QueuePool)

    def test_engine_uses_null_pool_in_testing(self):
        """Test engine uses NullPool in testing environment."""
        settings = Settings(app_env="testing")
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert isinstance(async_engine.pool, NullPool)

    def test_get_session_maker_creates_session_maker(self):
        """Test get_session_maker() creates a session factory."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        session_maker = engine.get_session_maker()

        assert session_maker is not None
        assert engine._session_maker is session_maker

    def test_get_session_maker_returns_cached(self):
        """Test get_session_maker() returns cached session maker."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        maker1 = engine.get_session_maker()
        maker2 = engine.get_session_maker()

        assert maker1 is maker2

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session() context manager creates a session."""
        settings = Settings(app_env="testing")
        engine = DatabaseEngine(settings)

        # Mock the session maker to avoid actual database connection
        from unittest.mock import AsyncMock, MagicMock

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_maker = MagicMock()
        mock_maker.return_value.__aenter__.return_value = mock_session
        mock_maker.return_value.__aexit__.return_value = None

        engine._session_maker = mock_maker

        async with engine.session() as session:
            assert session is mock_session

        # Verify commit and close were called
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_rolls_back_on_exception(self):
        """Test session() rolls back on exception."""
        settings = Settings(app_env="testing")
        engine = DatabaseEngine(settings)

        from unittest.mock import AsyncMock, MagicMock

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_maker = MagicMock()
        mock_maker.return_value.__aenter__.return_value = mock_session
        mock_maker.return_value.__aexit__.return_value = None

        engine._session_maker = mock_maker

        with pytest.raises(Exception, match="DB error"):
            async with engine.session() as session:
                pass

        # Verify rollback and close were called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_disposes_engine(self):
        """Test close() disposes the engine."""
        settings = Settings(app_env="testing")
        engine = DatabaseEngine(settings)

        # Create engine first
        _ = engine.get_engine()
        assert engine._engine is not None

        # Mock dispose to avoid actual database cleanup
        from unittest.mock import AsyncMock

        engine._engine.dispose = AsyncMock()

        await engine.close()

        assert engine._engine is None
        assert engine._session_maker is None


class TestGlobalEngine:
    """Tests for global engine functions."""

    def test_init_db_creates_engine(self):
        """Test init_db() creates and stores global engine."""
        settings = Settings()
        engine = init_db(settings)

        assert isinstance(engine, DatabaseEngine)
        assert engine.settings == settings

    def test_get_engine_returns_global_engine(self):
        """Test get_engine() returns the global engine."""
        settings = Settings()
        init_db(settings)

        engine = get_engine()

        assert isinstance(engine, AsyncEngine)

    def test_get_engine_raises_without_init(self):
        """Test get_engine() raises RuntimeError if not initialized."""
        # Reset global engine
        import wflo.db.engine as engine_module

        engine_module._db_engine = None

        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_engine()

    @pytest.mark.asyncio
    async def test_get_session_yields_session(self):
        """Test get_session() yields a database session."""
        settings = Settings(app_env="testing")
        init_db(settings)

        from unittest.mock import AsyncMock, MagicMock

        # Mock the session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        import wflo.db.engine as engine_module

        mock_maker = MagicMock()
        mock_maker.return_value.__aenter__.return_value = mock_session
        mock_maker.return_value.__aexit__.return_value = None

        engine_module._db_engine._session_maker = mock_maker

        async for session in get_session():
            assert session is mock_session
            break

    @pytest.mark.asyncio
    async def test_get_session_raises_without_init(self):
        """Test get_session() raises RuntimeError if not initialized."""
        import wflo.db.engine as engine_module

        engine_module._db_engine = None

        with pytest.raises(RuntimeError, match="Database not initialized"):
            async for _ in get_session():
                pass


class TestDatabaseConfiguration:
    """Tests for database configuration."""

    def test_engine_respects_pool_size(self):
        """Test engine respects configured pool size."""
        settings = Settings(database_pool_size=10)
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert async_engine.pool.size() == 10

    def test_engine_respects_max_overflow(self):
        """Test engine respects configured max overflow."""
        settings = Settings(database_max_overflow=5)
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert async_engine.pool._max_overflow == 5

    def test_engine_respects_pool_timeout(self):
        """Test engine respects configured pool timeout."""
        settings = Settings(database_pool_timeout=60)
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        assert async_engine.pool._timeout == 60

    def test_engine_enables_pre_ping(self):
        """Test engine enables connection health checks (pre_ping)."""
        settings = Settings()
        engine = DatabaseEngine(settings)

        async_engine = engine.get_engine()

        # pre_ping should be enabled by default
        assert async_engine.pool._pre_ping is True
