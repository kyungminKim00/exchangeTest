"""
Database performance tests
"""

import asyncio
import concurrent.futures
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

import pytest

from alt_exchange.core.enums import Asset, OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.models import Account, Balance, Order, User
from alt_exchange.infra.database import DatabaseFactory
from alt_exchange.infra.database.coverage import CoverageTrackingDatabase


class TestDatabasePerformance:
    """Database performance tests"""

    @pytest.fixture
    def db(self):
        """Create database with coverage tracking"""
        base_db = DatabaseFactory.create_for_testing()
        return CoverageTrackingDatabase(base_db)

    @pytest.fixture
    def sample_data(self, db):
        """Create sample data for performance tests"""
        users = []
        accounts = []
        balances = []
        orders = []

        # Create 100 users with accounts and balances
        for i in range(100):
            user = User(
                id=db.next_id("users"),
                email=f"user{i}@example.com",
                password_hash=f"hash{i}",
            )
            db.insert_user(user)
            users.append(user)

            account = Account(id=db.next_id("accounts"), user_id=user.id)
            db.insert_account(account)
            accounts.append(account)

            # Create balances for each asset
            for asset in [Asset.ALT, Asset.USDT]:
                balance = Balance(
                    id=db.next_id("balances"),
                    account_id=account.id,
                    asset=asset,
                    available=Decimal("1000.0"),
                    locked=Decimal("0.0"),
                )
                db.upsert_balance(balance)
                balances.append(balance)

        # Create 1000 orders
        for i in range(1000):
            user = users[i % len(users)]
            account = accounts[i % len(accounts)]

            order = Order(
                id=db.next_id("orders"),
                user_id=user.id,
                account_id=account.id,
                market="ALT/USDT",
                side=Side.BUY if i % 2 == 0 else Side.SELL,
                type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
                price=Decimal("100.0") + Decimal(str(i % 100)),
                amount=Decimal("1.0"),
                status=OrderStatus.OPEN,
            )
            db.insert_order(order)
            orders.append(order)

        return {
            "users": users,
            "accounts": accounts,
            "balances": balances,
            "orders": orders,
        }

    def test_single_query_performance(self, db, sample_data):
        """Test single query performance"""
        users = sample_data["users"]

        # Test get_user performance
        start_time = time.time()
        for _ in range(100):
            user = db.get_user(users[0].id)
            assert user is not None
        end_time = time.time()

        avg_time = (end_time - start_time) / 100 * 1000  # Convert to ms
        assert avg_time < 10, f"Average get_user time {avg_time:.2f}ms exceeds 10ms"

    def test_bulk_insert_performance(self, db):
        """Test bulk insert performance"""
        start_time = time.time()

        # Insert 1000 users
        for i in range(1000):
            user = User(
                id=db.next_id("users"),
                email=f"bulk_user{i}@example.com",
                password_hash=f"bulk_hash{i}",
            )
            db.insert_user(user)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to ms
        avg_time = total_time / 1000

        assert avg_time < 5, f"Average insert time {avg_time:.2f}ms exceeds 5ms"
        assert (
            total_time < 5000
        ), f"Total bulk insert time {total_time:.2f}ms exceeds 5s"

    def test_concurrent_read_performance(self, db, sample_data):
        """Test concurrent read performance"""
        users = sample_data["users"]

        def read_user(user_id: int):
            return db.get_user(user_id)

        # Test with 10 concurrent threads
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(read_user, users[i % len(users)].id) for i in range(100)
            ]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to ms

        assert all(result is not None for result in results)
        assert total_time < 1000, f"Concurrent read time {total_time:.2f}ms exceeds 1s"

    def test_concurrent_write_performance(self, db):
        """Test concurrent write performance"""

        def create_user(user_id: int):
            user = User(
                id=user_id,
                email=f"concurrent_user{user_id}@example.com",
                password_hash=f"concurrent_hash{user_id}",
            )
            return db.insert_user(user)

        # Test with 5 concurrent threads
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user, i) for i in range(50)]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to ms

        assert len(results) == 50
        assert total_time < 2000, f"Concurrent write time {total_time:.2f}ms exceeds 2s"

    def test_complex_query_performance(self, db, sample_data):
        """Test complex query performance"""
        users = sample_data["users"]

        # Test get_orders_by_user performance
        start_time = time.time()
        for user in users[:10]:  # Test with first 10 users
            orders = db.get_orders_by_user(user.id)
            assert isinstance(orders, list)
        end_time = time.time()

        avg_time = (end_time - start_time) / 10 * 1000  # Convert to ms
        assert (
            avg_time < 50
        ), f"Average complex query time {avg_time:.2f}ms exceeds 50ms"

    def test_balance_operations_performance(self, db, sample_data):
        """Test balance operations performance"""
        balances = sample_data["balances"]

        # Test find_balance performance
        start_time = time.time()
        for _ in range(100):
            balance = db.find_balance(balances[0].account_id, balances[0].asset)
            assert balance is not None
        end_time = time.time()

        avg_time = (end_time - start_time) / 100 * 1000  # Convert to ms
        assert avg_time < 10, f"Average find_balance time {avg_time:.2f}ms exceeds 10ms"

    def test_memory_usage(self, db, sample_data):
        """Test memory usage during operations"""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        # Perform memory-intensive operations
        for i in range(1000):
            user = User(
                id=db.next_id("users"),
                email=f"memory_user{i}@example.com",
                password_hash=f"memory_hash{i}",
            )
            db.insert_user(user)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 100MB for 1000 users)
            assert (
                memory_increase < 100
            ), f"Memory increase {memory_increase:.2f}MB exceeds 100MB"

    def test_coverage_metrics(self, db, sample_data):
        """Test coverage metrics collection"""
        # Perform various operations
        users = sample_data["users"]
        accounts = sample_data["accounts"]
        balances = sample_data["balances"]
        orders = sample_data["orders"]

        # Test different operations
        db.get_user(users[0].id)
        db.get_account(accounts[0].id)
        db.find_balance(balances[0].account_id, balances[0].asset)
        db.get_order(orders[0].id)
        db.get_orders_by_user(users[0].id)
        db.get_balances_by_account(accounts[0].id)

        # Generate coverage report
        report = db.generate_coverage_report()

        # Verify coverage metrics
        assert report.metrics.methods_coverage > 0
        assert report.metrics.data_types_coverage > 0
        assert report.metrics.overall_coverage > 0
        assert report.metrics.avg_response_time > 0

        # Verify detailed metrics
        assert "method_call_counts" in report.detailed_metrics
        assert "method_response_times" in report.detailed_metrics

        # Print coverage report for debugging
        print(f"\nCoverage Report:")
        print(f"Methods Coverage: {report.metrics.methods_coverage:.1f}%")
        print(f"Data Types Coverage: {report.metrics.data_types_coverage:.1f}%")
        print(f"Overall Coverage: {report.metrics.overall_coverage:.1f}%")
        print(f"Average Response Time: {report.metrics.avg_response_time:.2f}ms")

        if report.recommendations:
            print(f"Recommendations: {report.recommendations}")


class TestDatabaseStress:
    """Database stress tests"""

    @pytest.fixture
    def db(self):
        """Create database with coverage tracking"""
        base_db = DatabaseFactory.create_for_testing()
        return CoverageTrackingDatabase(base_db)

    def test_high_volume_inserts(self, db):
        """Test high volume insert performance"""
        start_time = time.time()

        # Insert 10,000 users
        for i in range(10000):
            user = User(
                id=db.next_id("users"),
                email=f"stress_user{i}@example.com",
                password_hash=f"stress_hash{i}",
            )
            db.insert_user(user)

        end_time = time.time()
        total_time = end_time - start_time
        throughput = 10000 / total_time  # operations per second

        assert (
            throughput > 1000
        ), f"Insert throughput {throughput:.0f} ops/sec below 1000"
        assert total_time < 30, f"High volume insert time {total_time:.2f}s exceeds 30s"

    def test_concurrent_stress(self, db):
        """Test concurrent operations stress"""

        def stress_operation(thread_id: int):
            results = []
            for i in range(100):
                user = User(
                    id=db.next_id("users"),
                    email=f"stress_{thread_id}_{i}@example.com",
                    password_hash=f"stress_hash_{thread_id}_{i}",
                )
                result = db.insert_user(user)
                results.append(result)
            return results

        # Test with 20 concurrent threads
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(20)]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = end_time - start_time
        total_operations = sum(len(result) for result in results)
        throughput = total_operations / total_time

        assert (
            throughput > 500
        ), f"Concurrent throughput {throughput:.0f} ops/sec below 500"
        assert total_time < 60, f"Concurrent stress time {total_time:.2f}s exceeds 60s"

    def test_memory_stress(self, db):
        """Test memory usage under stress"""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        # Create large number of objects
        users = []
        for i in range(5000):
            user = User(
                id=db.next_id("users"),
                email=f"memory_stress_user{i}@example.com",
                password_hash=f"memory_stress_hash{i}",
            )
            db.insert_user(user)
            users.append(user)

        # Perform operations on all users
        for user in users:
            retrieved_user = db.get_user(user.id)
            assert retrieved_user is not None

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert (
                memory_increase < 200
            ), f"Memory stress increase {memory_increase:.2f}MB exceeds 200MB"

    def test_error_handling_stress(self, db):
        """Test error handling under stress"""
        # Test with invalid data
        error_count = 0

        for i in range(1000):
            try:
                # Try to get non-existent user
                user = db.get_user(999999 + i)
                assert user is None
            except Exception:
                error_count += 1

        # Should handle errors gracefully
        assert error_count == 0, f"Unexpected errors: {error_count}"

    def test_coverage_under_stress(self, db):
        """Test coverage collection under stress"""
        # Perform stress operations
        for i in range(1000):
            user = User(
                id=db.next_id("users"),
                email=f"coverage_stress_user{i}@example.com",
                password_hash=f"coverage_stress_hash{i}",
            )
            db.insert_user(user)
            db.get_user(user.id)

        # Generate coverage report
        report = db.generate_coverage_report()

        # Verify coverage is still collected correctly
        assert report.metrics.methods_coverage > 0
        assert report.metrics.overall_coverage > 0
        assert len(report.detailed_metrics["method_call_counts"]) > 0

        # Print stress test results
        print(f"\nStress Test Coverage Report:")
        print(f"Methods Coverage: {report.metrics.methods_coverage:.1f}%")
        print(f"Overall Coverage: {report.metrics.overall_coverage:.1f}%")
        print(f"Average Response Time: {report.metrics.avg_response_time:.2f}ms")
        print(
            f"Total Operations: {sum(report.detailed_metrics['method_call_counts'].values())}"
        )
