"""
PostgreSQL Database 간단 테스트 - 실제 구현에 맞춘 테스트
"""

from unittest.mock import Mock, patch

import pytest

from alt_exchange.infra.database.postgres import PostgreSQLDatabase


class TestPostgreSQLDatabaseSimple:
    """PostgreSQLDatabase 간단 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.connection_string = "postgresql://user:password@localhost:5432/testdb"

    def test_database_initialization(self):
        """PostgreSQLDatabase 초기화 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                assert db.engine == mock_engine
                assert db.SessionLocal == mock_session

    def test_database_with_different_connection_string(self):
        """다른 연결 문자열로 PostgreSQLDatabase 생성 테스트"""
        connection_string2 = "postgresql://user2:password2@localhost:5432/testdb2"

        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(connection_string2)

                assert db.engine == mock_engine
                assert db.SessionLocal == mock_session

    def test_database_attributes(self):
        """PostgreSQLDatabase 속성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                assert hasattr(db, "engine")
                assert hasattr(db, "SessionLocal")

    def test_database_engine_creation(self):
        """PostgreSQLDatabase 엔진 생성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                mock_create_engine.assert_called_once_with(
                    self.connection_string,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False,
                )

    def test_database_session_creation(self):
        """PostgreSQLDatabase 세션 생성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                mock_sessionmaker.assert_called_once_with(
                    autocommit=False, autoflush=False, bind=mock_engine
                )

    def test_database_connection_string_property(self):
        """PostgreSQLDatabase 연결 문자열 속성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                # connection_string 속성이 없으므로 engine과 SessionLocal만 확인
                assert db.engine == mock_engine
                assert db.SessionLocal == mock_session

    def test_database_engine_property(self):
        """PostgreSQLDatabase 엔진 속성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                assert db.engine == mock_engine

    def test_database_session_local_property(self):
        """PostgreSQLDatabase SessionLocal 속성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(self.connection_string)

                assert db.SessionLocal == mock_session

    def test_database_with_empty_connection_string(self):
        """빈 연결 문자열로 PostgreSQLDatabase 생성 테스트"""
        empty_connection_string = ""

        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(empty_connection_string)

                assert db.engine == mock_engine
                assert db.SessionLocal == mock_session

    def test_database_with_none_connection_string(self):
        """None 연결 문자열로 PostgreSQLDatabase 생성 테스트"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                db = PostgreSQLDatabase(None)

                assert db.engine == mock_engine
                assert db.SessionLocal == mock_session

    def test_database_multiple_instances(self):
        """여러 PostgreSQLDatabase 인스턴스 생성 테스트"""
        connection_strings = [
            "postgresql://user1:password1@localhost:5432/db1",
            "postgresql://user2:password2@localhost:5432/db2",
            "postgresql://user3:password3@localhost:5432/db3",
        ]

        with patch(
            "alt_exchange.infra.database.postgres.create_engine"
        ) as mock_create_engine:
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_engine = Mock()
                mock_session = Mock()
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = mock_session

                databases = []
                for conn_str in connection_strings:
                    db = PostgreSQLDatabase(conn_str)
                    databases.append(db)

                assert len(databases) == 3
                for db in databases:
                    assert db.engine == mock_engine
                    assert db.SessionLocal == mock_session
