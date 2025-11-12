#!/usr/bin/env python3
"""Initialize wflo database schema.

This script creates all necessary database tables for wflo.
Works with both local PostgreSQL and Supabase.

Usage:
    python scripts/init_db.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wflo.config import get_settings
from wflo.db.engine import init_db
from wflo.db.models import Base


async def setup_database():
    """Initialize database with wflo schema."""
    print("=" * 60)
    print("wflo Database Initialization")
    print("=" * 60)

    settings = get_settings()

    # Display connection info (hide password)
    db_url = str(settings.database_url)
    if "@" in db_url:
        # Hide password in URL
        parts = db_url.split("@")
        credentials = parts[0].split("//")[1]
        username = credentials.split(":")[0]
        safe_url = db_url.replace(credentials, f"{username}:****")
    else:
        safe_url = db_url

    print(f"\nDatabase URL: {safe_url}")
    print(f"Environment: {settings.app_env}")
    print()

    db = init_db(settings)
    engine = db.get_engine()

    try:
        # Test connection first
        print("Testing database connection...")
        is_healthy = await db.health_check()

        if not is_healthy:
            print("❌ Database connection failed!")
            return 1

        print("✅ Database connection successful!")

        # Create all tables
        print("\nCreating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("\n✅ Database initialized successfully!")
        print("\nCreated tables:")
        print("  - workflow_definitions")
        print("  - workflow_executions")
        print("  - step_executions")
        print("  - state_snapshots")
        print("  - approval_requests")
        print("  - rollback_actions")

        return 0

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await db.close()
        print("\nDatabase connection closed.")


def main():
    """Entry point."""
    exit_code = asyncio.run(setup_database())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
