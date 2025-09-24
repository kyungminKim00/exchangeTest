"""
Database factory for creating database instances
"""

from __future__ import annotations

import os
from typing import Optional

from alt_exchange.infra.database.base import Database
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.database.postgres import PostgreSQLDatabase


class DatabaseFactory:
    """Factory for creating database instances"""

    @staticmethod
    def create_database(
        database_type: Optional[str] = None,
        connection_string: Optional[str] = None,
    ) -> Database:
        """
        Create a database instance based on configuration

        Args:
            database_type: Type of database ('postgres', 'inmemory', or None for auto-detect)
            connection_string: Database connection string

        Returns:
            Database instance
        """
        # Auto-detect database type if not specified
        if database_type is None:
            database_type = os.getenv("DATABASE_TYPE", "inmemory")

        # Get connection string from environment if not provided
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL")

        if database_type.lower() == "postgres":
            if not connection_string:
                raise ValueError("PostgreSQL connection string is required")
            return PostgreSQLDatabase(connection_string)
        elif database_type.lower() == "inmemory":
            return InMemoryDatabase()
        else:
            raise ValueError(f"Unsupported database type: {database_type}")

    @staticmethod
    def create_for_testing() -> Database:
        """Create an in-memory database for testing"""
        return InMemoryDatabase()

    @staticmethod
    def create_for_production(connection_string: str) -> Database:
        """Create a PostgreSQL database for production"""
        return PostgreSQLDatabase(connection_string)
