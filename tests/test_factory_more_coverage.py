"""
Additional tests for database/factory.py to improve coverage.
Focuses on uncovered lines and edge cases.
"""

import os
from unittest.mock import Mock, patch

import pytest

from alt_exchange.infra.database.factory import DatabaseFactory


class TestFactoryMoreCoverage:
    """Test database factory for better coverage."""

    def test_create_database_inmemory(self):
        """Test create_database with inmemory type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "inmemory"}):
            db = DatabaseFactory.create_database()
            assert db is not None
            # Check that it's an in-memory database
            assert hasattr(db, "accounts")
            assert hasattr(db, "orders")
            assert hasattr(db, "trades")
            assert hasattr(db, "transactions")
            assert hasattr(db, "balances")
            assert hasattr(db, "users")

    def test_create_database_postgres(self):
        """Test create_database with postgres type."""
        with patch.dict(
            os.environ,
            {"DATABASE_TYPE": "postgres", "DATABASE_URL": "postgresql://test"},
        ):
            with patch(
                "alt_exchange.infra.database.factory.PostgreSQLDatabase"
            ) as mock_postgres:
                mock_db = Mock()
                mock_postgres.return_value = mock_db

                db = DatabaseFactory.create_database()
                assert db is mock_db
                mock_postgres.assert_called_once_with("postgresql://test")

    def test_create_database_invalid_type(self):
        """Test create_database with invalid type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "invalid"}):
            with pytest.raises(ValueError, match="Unsupported database type: invalid"):
                DatabaseFactory.create_database()

    def test_create_database_no_env_var(self):
        """Test create_database with no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            db = DatabaseFactory.create_database()
            assert db is not None
            # Should default to inmemory
            assert hasattr(db, "accounts")
            assert hasattr(db, "orders")
            assert hasattr(db, "trades")
            assert hasattr(db, "transactions")
            assert hasattr(db, "balances")
            assert hasattr(db, "users")

    def test_create_database_empty_env_var(self):
        """Test create_database with empty environment variable."""
        with patch.dict(os.environ, {"DATABASE_TYPE": ""}):
            with pytest.raises(ValueError, match="Unsupported database type: "):
                DatabaseFactory.create_database()

    def test_create_database_case_sensitivity(self):
        """Test create_database with different case variations."""
        # Test uppercase
        with patch.dict(
            os.environ,
            {"DATABASE_TYPE": "POSTGRES", "DATABASE_URL": "postgresql://test"},
        ):
            with patch(
                "alt_exchange.infra.database.factory.PostgreSQLDatabase"
            ) as mock_postgres:
                mock_db = Mock()
                mock_postgres.return_value = mock_db

                db = DatabaseFactory.create_database()
                assert db is mock_db
                mock_postgres.assert_called_once_with("postgresql://test")

        # Test mixed case
        with patch.dict(os.environ, {"DATABASE_TYPE": "InMemory"}):
            db = DatabaseFactory.create_database()
            assert db is not None
            assert hasattr(db, "accounts")

    def test_create_database_postgres_no_connection_string(self):
        """Test create_database with postgres but no connection string."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgres"}):
            with pytest.raises(
                ValueError, match="PostgreSQL connection string is required"
            ):
                DatabaseFactory.create_database()

    def test_create_database_postgres_with_connection_string_param(self):
        """Test create_database with postgres and connection string parameter."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgres"}):
            with patch(
                "alt_exchange.infra.database.factory.PostgreSQLDatabase"
            ) as mock_postgres:
                mock_db = Mock()
                mock_postgres.return_value = mock_db

                db = DatabaseFactory.create_database(
                    connection_string="postgresql://test"
                )
                assert db is mock_db
                mock_postgres.assert_called_once_with("postgresql://test")

    def test_create_database_with_type_param(self):
        """Test create_database with type parameter."""
        with patch(
            "alt_exchange.infra.database.factory.PostgreSQLDatabase"
        ) as mock_postgres:
            mock_db = Mock()
            mock_postgres.return_value = mock_db

            db = DatabaseFactory.create_database(
                database_type="postgres", connection_string="postgresql://test"
            )
            assert db is mock_db
            mock_postgres.assert_called_once_with("postgresql://test")

    def test_create_database_inmemory_with_type_param(self):
        """Test create_database with inmemory type parameter."""
        db = DatabaseFactory.create_database(database_type="inmemory")
        assert db is not None
        assert hasattr(db, "accounts")

    def test_create_for_testing(self):
        """Test create_for_testing method."""
        db = DatabaseFactory.create_for_testing()
        assert db is not None
        assert hasattr(db, "accounts")
        assert hasattr(db, "orders")
        assert hasattr(db, "trades")
        assert hasattr(db, "transactions")
        assert hasattr(db, "balances")
        assert hasattr(db, "users")

    def test_create_for_production(self):
        """Test create_for_production method."""
        with patch(
            "alt_exchange.infra.database.factory.PostgreSQLDatabase"
        ) as mock_postgres:
            mock_db = Mock()
            mock_postgres.return_value = mock_db

            db = DatabaseFactory.create_for_production("postgresql://prod")
            assert db is mock_db
            mock_postgres.assert_called_once_with("postgresql://prod")

    def test_create_database_multiple_calls(self):
        """Test create_database with multiple calls."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "inmemory"}):
            db1 = DatabaseFactory.create_database()
            db2 = DatabaseFactory.create_database()

            # Should return different instances
            assert db1 is not db2
            assert db1 is not None
            assert db2 is not None

    def test_create_database_with_whitespace_type(self):
        """Test create_database with whitespace in type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "\t\ninmemory\t\n"}):
            with pytest.raises(
                ValueError, match="Unsupported database type: \\t\\ninmemory\\t\\n"
            ):
                DatabaseFactory.create_database()

    def test_create_database_with_special_characters(self):
        """Test create_database with special characters in type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "inmemory@#$%"}):
            with pytest.raises(
                ValueError, match="Unsupported database type: inmemory@#\\$%"
            ):
                DatabaseFactory.create_database()

    def test_create_database_with_none_type(self):
        """Test create_database with None type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "None"}):
            with pytest.raises(ValueError, match="Unsupported database type: None"):
                DatabaseFactory.create_database()

    def test_create_database_with_numeric_type(self):
        """Test create_database with numeric type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "123"}):
            with pytest.raises(ValueError, match="Unsupported database type: 123"):
                DatabaseFactory.create_database()

    def test_create_database_with_boolean_type(self):
        """Test create_database with boolean type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "true"}):
            with pytest.raises(ValueError, match="Unsupported database type: true"):
                DatabaseFactory.create_database()

    def test_create_database_with_json_type(self):
        """Test create_database with json type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": '{"type": "inmemory"}'}):
            with pytest.raises(
                ValueError, match='Unsupported database type: \\{"type": "inmemory"\\}'
            ):
                DatabaseFactory.create_database()

    def test_create_database_with_sql_type(self):
        """Test create_database with sql type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            with pytest.raises(ValueError, match="Unsupported database type: sqlite"):
                DatabaseFactory.create_database()

    def test_create_database_with_mysql_type(self):
        """Test create_database with mysql type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mysql"}):
            with pytest.raises(ValueError, match="Unsupported database type: mysql"):
                DatabaseFactory.create_database()

    def test_create_database_with_mongodb_type(self):
        """Test create_database with mongodb type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mongodb"}):
            with pytest.raises(ValueError, match="Unsupported database type: mongodb"):
                DatabaseFactory.create_database()

    def test_create_database_with_redis_type(self):
        """Test create_database with redis type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "redis"}):
            with pytest.raises(ValueError, match="Unsupported database type: redis"):
                DatabaseFactory.create_database()

    def test_create_database_with_cassandra_type(self):
        """Test create_database with cassandra type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "cassandra"}):
            with pytest.raises(
                ValueError, match="Unsupported database type: cassandra"
            ):
                DatabaseFactory.create_database()

    def test_create_database_with_elasticsearch_type(self):
        """Test create_database with elasticsearch type."""
        with patch.dict(os.environ, {"DATABASE_TYPE": "elasticsearch"}):
            with pytest.raises(
                ValueError, match="Unsupported database type: elasticsearch"
            ):
                DatabaseFactory.create_database()
