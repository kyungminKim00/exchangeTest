"""
Database coverage analysis and reporting
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from alt_exchange.core.enums import Asset
from alt_exchange.core.models import (
    Account,
    AuditLog,
    Balance,
    Order,
    Trade,
    Transaction,
    User,
)
from alt_exchange.infra.database.base import Database


@dataclass
class CoverageMetrics:
    """Database coverage metrics"""

    # Method coverage
    methods_called: Set[str] = field(default_factory=set)
    methods_total: int = 0
    methods_coverage: float = 0.0

    # Data type coverage
    data_types_used: Set[str] = field(default_factory=set)
    data_types_total: int = 0
    data_types_coverage: float = 0.0

    # Query pattern coverage
    query_patterns: Set[str] = field(default_factory=set)
    query_patterns_total: int = 0
    query_patterns_coverage: float = 0.0

    # Error scenario coverage
    error_scenarios: Set[str] = field(default_factory=set)
    error_scenarios_total: int = 0
    error_scenarios_coverage: float = 0.0

    # Transaction coverage
    transaction_patterns: Set[str] = field(default_factory=set)
    transaction_patterns_total: int = 0
    transaction_patterns_coverage: float = 0.0

    # Overall coverage
    overall_coverage: float = 0.0

    # Performance metrics
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float("inf")

    # Error metrics
    total_errors: int = 0
    error_rate: float = 0.0


@dataclass
class CoverageReport:
    """Comprehensive coverage report"""

    timestamp: float = field(default_factory=time.time)
    metrics: CoverageMetrics = field(default_factory=CoverageMetrics)
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "timestamp": self.timestamp,
            "metrics": {
                "methods_coverage": self.metrics.methods_coverage,
                "data_types_coverage": self.metrics.data_types_coverage,
                "query_patterns_coverage": self.metrics.query_patterns_coverage,
                "error_scenarios_coverage": self.metrics.error_scenarios_coverage,
                "transaction_patterns_coverage": self.metrics.transaction_patterns_coverage,
                "overall_coverage": self.metrics.overall_coverage,
                "avg_response_time": self.metrics.avg_response_time,
                "max_response_time": self.metrics.max_response_time,
                "min_response_time": self.metrics.min_response_time,
                "total_errors": self.metrics.total_errors,
                "error_rate": self.metrics.error_rate,
            },
            "detailed_metrics": self.detailed_metrics,
            "recommendations": self.recommendations,
        }


class DatabaseCoverageAnalyzer:
    """Analyzes database coverage and generates reports"""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        self.errors: Dict[str, int] = defaultdict(int)
        self.data_types_used: Set[str] = set()
        self.query_patterns: Set[str] = set()
        self.error_scenarios: Set[str] = set()
        self.transaction_patterns: Set[str] = set()

        # Define expected coverage targets
        self.expected_methods = self._get_expected_methods()
        self.expected_data_types = self._get_expected_data_types()
        self.expected_query_patterns = self._get_expected_query_patterns()
        self.expected_error_scenarios = self._get_expected_error_scenarios()
        self.expected_transaction_patterns = self._get_expected_transaction_patterns()

    def _get_expected_methods(self) -> Set[str]:
        """Get all expected database methods"""
        return {
            # User methods
            "insert_user",
            "get_user",
            "get_user_by_email",
            # Account methods
            "insert_account",
            "get_account",
            "get_accounts_by_user",
            # Balance methods
            "upsert_balance",
            "find_balance",
            "get_balances_by_account",
            # Order methods
            "insert_order",
            "update_order",
            "get_order",
            "get_orders_by_user",
            "get_orders_by_account",
            # Trade methods
            "insert_trade",
            "get_trade",
            "get_trades_by_user",
            # Transaction methods
            "insert_transaction",
            "update_transaction",
            "get_transaction",
            "get_transactions_by_user",
            # Audit methods
            "insert_audit",
            "get_audit_logs",
            # Utility methods
            "next_id",
        }

    def _get_expected_data_types(self) -> Set[str]:
        """Get all expected data types"""
        return {
            "User",
            "Account",
            "Balance",
            "Order",
            "Trade",
            "Transaction",
            "AuditLog",
            "Asset",
            "OrderStatus",
            "OrderType",
            "Side",
            "TimeInForce",
            "TransactionStatus",
            "TransactionType",
            "AccountStatus",
        }

    def _get_expected_query_patterns(self) -> Set[str]:
        """Get all expected query patterns"""
        return {
            "single_select",
            "multi_select",
            "insert",
            "update",
            "upsert",
            "delete",
            "join",
            "filter",
            "order_by",
            "limit",
            "count",
            "aggregate",
            "group_by",
            "having",
            "subquery",
            "union",
        }

    def _get_expected_error_scenarios(self) -> Set[str]:
        """Get all expected error scenarios"""
        return {
            "not_found",
            "duplicate_key",
            "foreign_key_violation",
            "check_constraint_violation",
            "not_null_violation",
            "connection_timeout",
            "deadlock",
            "lock_timeout",
            "insufficient_privileges",
            "database_unavailable",
        }

    def _get_expected_transaction_patterns(self) -> Set[str]:
        """Get all expected transaction patterns"""
        return {
            "single_transaction",
            "nested_transaction",
            "distributed_transaction",
            "rollback",
            "commit",
            "savepoint",
            "isolation_levels",
            "concurrent_transactions",
            "long_running_transaction",
        }

    def record_method_call(
        self,
        method_name: str,
        response_time: float,
        success: bool = True,
        error_type: Optional[str] = None,
    ) -> None:
        """Record a method call for coverage analysis"""
        self.call_counts[method_name] += 1
        self.response_times[method_name].append(response_time)

        if not success and error_type:
            self.errors[error_type] += 1
            self.error_scenarios.add(error_type)

        # Determine query pattern
        if method_name.startswith("get_"):
            if "by_" in method_name:
                self.query_patterns.add("filter")
            self.query_patterns.add("select")
        elif method_name.startswith("insert_"):
            self.query_patterns.add("insert")
        elif method_name.startswith("update_"):
            self.query_patterns.add("update")
        elif method_name.startswith("upsert_"):
            self.query_patterns.add("upsert")

    def record_data_type_usage(self, data_type: str) -> None:
        """Record usage of a data type"""
        self.data_types_used.add(data_type)

    def record_transaction_pattern(self, pattern: str) -> None:
        """Record a transaction pattern"""
        self.transaction_patterns.add(pattern)

    def generate_report(self) -> CoverageReport:
        """Generate comprehensive coverage report"""
        metrics = CoverageMetrics()

        # Calculate method coverage
        called_methods = set(self.call_counts.keys())
        metrics.methods_called = called_methods
        metrics.methods_total = len(self.expected_methods)
        metrics.methods_coverage = (
            len(called_methods & self.expected_methods)
            / len(self.expected_methods)
            * 100
        )

        # Calculate data type coverage
        metrics.data_types_used = self.data_types_used
        metrics.data_types_total = len(self.expected_data_types)
        metrics.data_types_coverage = (
            len(self.data_types_used & self.expected_data_types)
            / len(self.expected_data_types)
            * 100
        )

        # Calculate query pattern coverage
        metrics.query_patterns = self.query_patterns
        metrics.query_patterns_total = len(self.expected_query_patterns)
        metrics.query_patterns_coverage = (
            len(self.query_patterns & self.expected_query_patterns)
            / len(self.expected_query_patterns)
            * 100
        )

        # Calculate error scenario coverage
        metrics.error_scenarios = self.error_scenarios
        metrics.error_scenarios_total = len(self.expected_error_scenarios)
        metrics.error_scenarios_coverage = (
            len(self.error_scenarios & self.expected_error_scenarios)
            / len(self.expected_error_scenarios)
            * 100
        )

        # Calculate transaction pattern coverage
        metrics.transaction_patterns = self.transaction_patterns
        metrics.transaction_patterns_total = len(self.expected_transaction_patterns)
        metrics.transaction_patterns_coverage = (
            len(self.transaction_patterns & self.expected_transaction_patterns)
            / len(self.expected_transaction_patterns)
            * 100
        )

        # Calculate overall coverage
        coverage_scores = [
            metrics.methods_coverage,
            metrics.data_types_coverage,
            metrics.query_patterns_coverage,
            metrics.error_scenarios_coverage,
            metrics.transaction_patterns_coverage,
        ]
        metrics.overall_coverage = sum(coverage_scores) / len(coverage_scores)

        # Calculate performance metrics
        all_response_times = []
        for times in self.response_times.values():
            all_response_times.extend(times)

        if all_response_times:
            metrics.avg_response_time = sum(all_response_times) / len(
                all_response_times
            )
            metrics.max_response_time = max(all_response_times)
            metrics.min_response_time = min(all_response_times)

        # Calculate error metrics
        total_calls = sum(self.call_counts.values())
        total_errors = sum(self.errors.values())
        metrics.total_errors = total_errors
        metrics.error_rate = (
            (total_errors / total_calls * 100) if total_calls > 0 else 0
        )

        # Generate detailed metrics
        detailed_metrics = {
            "method_call_counts": dict(self.call_counts),
            "method_response_times": {
                method: {
                    "avg": sum(times) / len(times) if times else 0,
                    "max": max(times) if times else 0,
                    "min": min(times) if times else 0,
                    "count": len(times),
                }
                for method, times in self.response_times.items()
            },
            "error_counts": dict(self.errors),
            "missing_methods": self.expected_methods - called_methods,
            "missing_data_types": self.expected_data_types - self.data_types_used,
            "missing_query_patterns": self.expected_query_patterns
            - self.query_patterns,
            "missing_error_scenarios": self.expected_error_scenarios
            - self.error_scenarios,
            "missing_transaction_patterns": self.expected_transaction_patterns
            - self.transaction_patterns,
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, detailed_metrics)

        return CoverageReport(
            metrics=metrics,
            detailed_metrics=detailed_metrics,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, metrics: CoverageMetrics, detailed_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Method coverage recommendations
        if metrics.methods_coverage < 90:
            missing_methods = detailed_metrics.get("missing_methods", set())
            if missing_methods:
                recommendations.append(
                    f"Add tests for missing methods: {', '.join(sorted(missing_methods))}"
                )

        # Data type coverage recommendations
        if metrics.data_types_coverage < 90:
            missing_types = detailed_metrics.get("missing_data_types", set())
            if missing_types:
                recommendations.append(
                    f"Add tests for missing data types: {', '.join(sorted(missing_types))}"
                )

        # Query pattern recommendations
        if metrics.query_patterns_coverage < 80:
            missing_patterns = detailed_metrics.get("missing_query_patterns", set())
            if missing_patterns:
                recommendations.append(
                    f"Add tests for missing query patterns: {', '.join(sorted(missing_patterns))}"
                )

        # Error scenario recommendations
        if metrics.error_scenarios_coverage < 70:
            missing_scenarios = detailed_metrics.get("missing_error_scenarios", set())
            if missing_scenarios:
                recommendations.append(
                    f"Add tests for missing error scenarios: {', '.join(sorted(missing_scenarios))}"
                )

        # Performance recommendations
        if metrics.avg_response_time > 100:  # 100ms
            recommendations.append(
                "Optimize slow queries - average response time exceeds 100ms"
            )

        if metrics.max_response_time > 1000:  # 1s
            recommendations.append(
                "Investigate slowest queries - max response time exceeds 1s"
            )

        # Error rate recommendations
        if metrics.error_rate > 1:  # 1%
            recommendations.append(
                "High error rate detected - investigate and fix errors"
            )

        # Transaction pattern recommendations
        if metrics.transaction_patterns_coverage < 80:
            missing_patterns = detailed_metrics.get(
                "missing_transaction_patterns", set()
            )
            if missing_patterns:
                recommendations.append(
                    f"Add tests for missing transaction patterns: {', '.join(sorted(missing_patterns))}"
                )

        return recommendations


class CoverageTrackingDatabase:
    """Database wrapper that tracks coverage metrics"""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.analyzer = DatabaseCoverageAnalyzer(database)

    def _track_call(self, method_name: str, func, *args, **kwargs):
        """Track a method call with timing and error handling"""
        start_time = time.time()
        success = True
        error_type = None

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error_type = type(e).__name__
            raise
        finally:
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            self.analyzer.record_method_call(
                method_name, response_time, success, error_type
            )

    # User operations
    def insert_user(self, user: User) -> User:
        self.analyzer.record_data_type_usage("User")
        return self._track_call("insert_user", self.database.insert_user, user)

    def get_user(self, user_id: int) -> Optional[User]:
        return self._track_call("get_user", self.database.get_user, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self._track_call(
            "get_user_by_email", self.database.get_user_by_email, email
        )

    # Account operations
    def insert_account(self, account: Account) -> Account:
        self.analyzer.record_data_type_usage("Account")
        return self._track_call("insert_account", self.database.insert_account, account)

    def get_account(self, account_id: int) -> Optional[Account]:
        return self._track_call("get_account", self.database.get_account, account_id)

    def get_accounts_by_user(self, user_id: int) -> List[Account]:
        return self._track_call(
            "get_accounts_by_user", self.database.get_accounts_by_user, user_id
        )

    # Balance operations
    def upsert_balance(self, balance: Balance) -> Balance:
        self.analyzer.record_data_type_usage("Balance")
        return self._track_call("upsert_balance", self.database.upsert_balance, balance)

    def find_balance(self, account_id: int, asset: Asset) -> Optional[Balance]:
        self.analyzer.record_data_type_usage("Asset")
        return self._track_call(
            "find_balance", self.database.find_balance, account_id, asset
        )

    def get_balances_by_account(self, account_id: int) -> List[Balance]:
        return self._track_call(
            "get_balances_by_account", self.database.get_balances_by_account, account_id
        )

    # Order operations
    def insert_order(self, order: Order) -> Order:
        self.analyzer.record_data_type_usage("Order")
        return self._track_call("insert_order", self.database.insert_order, order)

    def update_order(self, order: Order) -> None:
        return self._track_call("update_order", self.database.update_order, order)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self._track_call("get_order", self.database.get_order, order_id)

    def get_orders_by_user(self, user_id: int) -> List[Order]:
        return self._track_call(
            "get_orders_by_user", self.database.get_orders_by_user, user_id
        )

    def get_orders_by_account(self, account_id: int) -> List[Order]:
        return self._track_call(
            "get_orders_by_account", self.database.get_orders_by_account, account_id
        )

    # Trade operations
    def insert_trade(self, trade: Trade) -> Trade:
        self.analyzer.record_data_type_usage("Trade")
        return self._track_call("insert_trade", self.database.insert_trade, trade)

    def get_trade(self, trade_id: int) -> Optional[Trade]:
        return self._track_call("get_trade", self.database.get_trade, trade_id)

    def get_trades_by_user(self, user_id: int) -> List[Trade]:
        return self._track_call(
            "get_trades_by_user", self.database.get_trades_by_user, user_id
        )

    # Transaction operations
    def insert_transaction(self, transaction: Transaction) -> Transaction:
        self.analyzer.record_data_type_usage("Transaction")
        return self._track_call(
            "insert_transaction", self.database.insert_transaction, transaction
        )

    def update_transaction(self, transaction: Transaction) -> None:
        return self._track_call(
            "update_transaction", self.database.update_transaction, transaction
        )

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        return self._track_call(
            "get_transaction", self.database.get_transaction, transaction_id
        )

    def get_transactions_by_user(self, user_id: int) -> List[Transaction]:
        return self._track_call(
            "get_transactions_by_user", self.database.get_transactions_by_user, user_id
        )

    # Audit log operations
    def insert_audit(self, audit_log: AuditLog) -> AuditLog:
        self.analyzer.record_data_type_usage("AuditLog")
        return self._track_call("insert_audit", self.database.insert_audit, audit_log)

    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        return self._track_call("get_audit_logs", self.database.get_audit_logs, limit)

    # Utility operations
    def next_id(self, table: str) -> int:
        return self._track_call("next_id", self.database.next_id, table)

    def generate_coverage_report(self) -> CoverageReport:
        """Generate coverage report"""
        return self.analyzer.generate_report()
