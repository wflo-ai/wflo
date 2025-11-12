#!/usr/bin/env python3
"""Test Supabase database connection.

This script verifies that wflo can successfully connect to Supabase
and perform basic database operations.

Usage:
    python scripts/test_supabase_connection.py

Environment Variables:
    DATABASE_URL - Supabase PostgreSQL connection string
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, text
from wflo.config import get_settings
from wflo.db.engine import init_db
from wflo.db.models import WorkflowDefinitionModel, WorkflowExecutionModel


async def test_connection():
    """Test Supabase connection and basic operations."""
    print("=" * 60)
    print("Supabase Connection Test")
    print("=" * 60)

    settings = get_settings()

    # Display connection info
    db_url = str(settings.database_url)
    if "@" in db_url:
        parts = db_url.split("@")
        host_part = parts[1].split("/")[0]
        database_part = parts[1].split("/")[-1] if "/" in parts[1] else "postgres"
        username = parts[0].split("//")[1].split(":")[0]
        safe_url = f"postgresql://{username}:****@{host_part}/..."
    else:
        safe_url = db_url
        host_part = "unknown"
        database_part = "unknown"

    print(f"\nConnection: {safe_url}")
    print(f"Host: {host_part}")
    print(f"Database: {database_part}")
    print()

    db = init_db(settings)

    try:
        # Test 1: Basic health check
        print("Test 1: Health Check")
        print("-" * 40)
        is_healthy = await db.health_check()
        if is_healthy:
            print("✅ Successfully connected to Supabase!")
        else:
            print("❌ Health check failed")
            return 1

        # Test 2: Check database version
        print("\nTest 2: Database Version")
        print("-" * 40)
        async with db.session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"PostgreSQL Version: {version}")

        # Test 3: List tables
        print("\nTest 3: List Tables")
        print("-" * 40)
        async with db.session() as session:
            result = await session.execute(
                text(
                    """
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
                )
            )
            tables = result.scalars().all()
            if tables:
                print(f"Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠️  No tables found. Run 'python scripts/init_db.py' first.")

        # Test 4: Write and read test data
        print("\nTest 4: Write and Read Operations")
        print("-" * 40)
        async with db.session() as session:
            # Create test workflow
            test_id = str(uuid4())
            workflow = WorkflowDefinitionModel(
                id=test_id,
                name=f"connection-test-{datetime.now(timezone.utc).timestamp()}",
                version=1,
                steps=[],
                policies={},
            )
            session.add(workflow)
            await session.commit()
            print(f"✅ Created test workflow: {test_id}")

            # Read it back
            result = await session.execute(
                select(WorkflowDefinitionModel).where(
                    WorkflowDefinitionModel.id == test_id
                )
            )
            found = result.scalar_one_or_none()

            if found:
                print(f"✅ Successfully read test workflow: {found.name}")

                # Create test execution
                exec_id = str(uuid4())
                execution = WorkflowExecutionModel(
                    id=exec_id,
                    workflow_id=test_id,
                    status="COMPLETED",
                    trace_id=f"trace-{uuid4()}",
                    correlation_id=f"corr-{uuid4()}",
                    cost_total_usd=0.001,
                )
                session.add(execution)
                await session.commit()
                print(f"✅ Created test execution: {exec_id}")

                # Clean up test data
                await session.delete(execution)
                await session.delete(found)
                await session.commit()
                print("✅ Cleaned up test data")
            else:
                print("❌ Failed to read test workflow")
                return 1

        # Test 5: Connection pool info
        print("\nTest 5: Connection Pool Info")
        print("-" * 40)
        engine = db.get_engine()
        pool = engine.pool
        print(f"Pool size: {pool.size()}")
        print(f"Pool checked out: {pool.checkedout()}")
        print(f"Pool overflow: {pool.overflow()}")
        print(f"Pool checked in: {pool.size() - pool.checkedout()}")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nSupabase connection is working correctly.")
        print("You can now run wflo workflows with this database.")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        await db.close()
        print("\nConnection closed.")


def main():
    """Entry point."""
    exit_code = asyncio.run(test_connection())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
