---
title: Enabling Persistence
description: Set up a PostgreSQL database to save workflow history and enable checkpoints.
---

# Enabling Persistence

By default, `wflo` runs in an in-memory mode where execution history is not saved. To enable long-term persistence, state checkpointing, and durable execution records, you need to connect `wflo` to a PostgreSQL database.

This guide provides two options: using a managed database with Supabase (recommended for production) or running PostgreSQL locally (great for development).

## Prerequisites

- A running PostgreSQL instance (either local or cloud-based).
- Your database connection string.

## Option 1: Supabase (Recommended)

Supabase provides a managed, production-ready PostgreSQL database with a generous free tier.

1.  **Create a Supabase Project**
    *   Sign up or log in at [supabase.com](https://supabase.com).
    *   Click "New project" and give it a name (e.g., `wflo-data`).
    *   Securely save your database password when prompted.

2.  **Get Your Connection String**
    *   In your Supabase project dashboard, navigate to **Settings** > **Database**.
    *   Under **Connection string**, find the URI that starts with `postgresql://`.
    *   **Important:** You must modify the driver to `postgresql+asyncpg://` for `wflo`'s async library to work.

3.  **Configure Your `.env` File**
    *   In the root of the `wflo` project, open your `.env` file.
    *   Add or update the `DATABASE_URL` variable with your modified Supabase connection string.

    ```bash
    # .env

    # Replace YOUR-PASSWORD and the host details from Supabase
    DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxxxxxx.supabase.co:5432/postgres
    ```

## Option 2: Local PostgreSQL

If you prefer to run everything locally, you can use a local PostgreSQL server.

1.  **Install and Run PostgreSQL**
    *   **macOS (Homebrew):**
        ```bash
        brew install postgresql
        brew services start postgresql
        ```
    *   **Ubuntu/Debian:**
        ```bash
        sudo apt-get update
        sudo apt-get install postgresql postgresql-contrib
        sudo systemctl start postgresql
        ```

2.  **Create a Database**
    *   Open your terminal and create a new database for `wflo`.

    ```bash
    createdb wflo
    ```

3.  **Configure Your `.env` File**
    *   Open your `.env` file and set the `DATABASE_URL` to point to your local database.

    ```bash
    # .env

    # Assumes default user and port, with no password
    DATABASE_URL=postgresql+asyncpg://localhost:5432/wflo
    ```

## Step 4: Initialize the Database Schema

Once your `DATABASE_URL` is configured, you need to create the necessary tables for `wflo`.

Run the `init_db.py` script from the root of the project:

```bash
poetry run python scripts/init_db.py
```

If successful, you will see a confirmation message listing the created tables:
```
✅ Database initialized successfully!

Created tables:
  - workflow_definitions
  - workflow_executions
  - step_executions
  - state_snapshots
  - approval_requests
  - rollback_actions
```

## Step 5: Verify the Connection

You can run a dedicated test script to ensure everything is configured correctly.

```bash
poetry run python scripts/test_supabase_connection.py
```
*(Note: The script is named `test_supabase_connection.py` but works for any PostgreSQL database).*

A successful connection will run a series of tests and confirm that `wflo` can communicate with your database.

**Your setup is now complete!** With persistence enabled, all `WfloWorkflow` executions will be saved, and you can now use features like `@checkpoint` that require a database.
