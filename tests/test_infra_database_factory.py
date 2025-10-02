"""
Database Factory 테스트
"""

from unittest.mock import patch

import pytest

from alt_exchange.infra.database.factory import DatabaseFactory
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.database.postgres import PostgreSQLDatabase


class TestDatabaseFactory:
    def test_create_in_memory_database(self):
        """인메모리 데이터베이스 생성 테스트"""
        db = DatabaseFactory.create_database("inmemory")
        assert isinstance(db, InMemoryDatabase)

    def test_create_postgres_database(self):
        """PostgreSQL 데이터베이스 생성 테스트"""
        with patch(
            "alt_exchange.infra.database.factory.PostgreSQLDatabase"
        ) as mock_postgres:
            mock_postgres.return_value = "mock_postgres_db"
            db = DatabaseFactory.create_database("postgres", "postgresql://test")
            assert db == "mock_postgres_db"

    def test_create_database_with_invalid_type(self):
        """잘못된 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("invalid_type")

    def test_create_database_with_none_type(self):
        """None 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        # None 타입은 자동으로 "inmemory"로 설정됨
        db = DatabaseFactory.create_database(None)
        assert isinstance(db, InMemoryDatabase)

    def test_create_database_with_empty_string(self):
        """빈 문자열로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("")

    def test_create_database_case_sensitive(self):
        """대소문자 구분 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("IN_MEMORY")

    def test_create_database_with_whitespace(self):
        """공백이 포함된 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database(" in_memory ")

    def test_create_database_with_special_characters(self):
        """특수문자가 포함된 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("in_memory!")

    def test_create_database_with_numbers(self):
        """숫자가 포함된 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("in_memory123")

    def test_create_database_with_unicode(self):
        """유니코드 문자가 포함된 타입으로 데이터베이스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("in_memory_한글")
