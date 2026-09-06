from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

ALEMBIC_VERSION_LENGTH = 255


def ensure_alembic_version_capacity(connection: Connection) -> None:
    """Make Alembic's version table safe for descriptive revision IDs.

    Alembic defaults version_num to VARCHAR(32). This project intentionally uses
    descriptive IDs longer than 32 characters (e.g. 0006_portfolio_execution_semantics).
    Run this before Alembic configures the migration context so both a fresh install
    and an upgrade of an existing VARCHAR(32) table work without manual SQL.
    """
    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(
            text(
                f"CREATE TABLE IF NOT EXISTS alembic_version "
                f"(version_num VARCHAR({ALEMBIC_VERSION_LENGTH}) NOT NULL PRIMARY KEY)"
            )
        )
        connection.execute(
            text(
                f"ALTER TABLE alembic_version ALTER COLUMN version_num "
                f"TYPE VARCHAR({ALEMBIC_VERSION_LENGTH})"
            )
        )
        return

    # Test/dev fallback. SQLite does not enforce VARCHAR length, but creating the
    # table here mirrors the production bootstrap path and lets migration smoke
    # tests exercise fresh/existing version rows.
    tables = inspect(connection).get_table_names()
    if "alembic_version" not in tables:
        connection.execute(
            text(
                f"CREATE TABLE alembic_version "
                f"(version_num VARCHAR({ALEMBIC_VERSION_LENGTH}) NOT NULL PRIMARY KEY)"
            )
        )
