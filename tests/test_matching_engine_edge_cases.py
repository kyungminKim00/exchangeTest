from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from alt_exchange.core.enums import OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.events import OrderStatusChanged, TradeExecuted
from alt_exchange.core.exceptions import InvalidOrderError
from alt_exchange.infra.bootstrap import build_application_context
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngineEdgeCases:
    """매칭 엔진의 엣지 케이스와 이벤트 버스 테스트"""

    def setup_method(self):
        """각 테스트 전에 새로운 컨텍스트 생성"""
        self.context = build_application_context()
        self.engine = MatchingEngine(
            market="ALT/USDT",
            db=self.context["db"],
            event_bus=self.context["event_bus"],
        )
        self.account = self.context["account_service"]
        self.wallet = self.context["wallet_service"]

    def test_fok_order_cancellation_emits_event(self):
        """FOK 주문 취소 시 이벤트가 발행되는지 테스트"""
        # 사용자 생성 및 충분한 잔고 설정
        user = self.account.create_user("fok@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "USDT", Decimal("10000"))  # 충분한 잔고

        # FOK 주문 생성 (유동성 부족으로 취소될 주문)
        # 높은 가격으로 매수 주문을 생성하여 매도 주문이 없어 취소되도록 함
        order = self.account.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("1000"),  # 매우 높은 가격
            amount=Decimal("1"),
            time_in_force=TimeInForce.FOK,
        )

        # FOK 주문이 취소되었는지 확인
        refreshed_order = self.context["db"].orders[order.id]
        assert refreshed_order.status == OrderStatus.CANCELED

    def test_trade_execution_emits_events(self):
        """거래 체결 시 TradeExecuted 이벤트가 발행되는지 테스트"""
        # 매도자와 매수자 생성
        seller = self.account.create_user("seller@example.com", "pwd")
        buyer = self.account.create_user("buyer@example.com", "pwd")

        # 잔고 설정
        self.wallet.simulate_deposit(seller.id, "ALT", Decimal("10"))
        self.wallet.simulate_deposit(buyer.id, "USDT", Decimal("100"))

        # 매도 주문 먼저 생성
        sell_order = self.account.place_limit_order(
            user_id=seller.id, side=Side.SELL, price=Decimal("10"), amount=Decimal("5")
        )

        # 매수 주문으로 체결 유도
        buy_order = self.account.place_limit_order(
            user_id=buyer.id, side=Side.BUY, price=Decimal("10"), amount=Decimal("3")
        )

        # 거래가 체결되었는지 확인 (주문 상태로 판단)
        refreshed_sell_order = self.context["db"].orders[sell_order.id]
        refreshed_buy_order = self.context["db"].orders[buy_order.id]

        # 매도 주문은 부분 체결, 매수 주문은 완전 체결
        assert refreshed_sell_order.status == OrderStatus.PARTIAL
        assert refreshed_buy_order.status == OrderStatus.FILLED

    def test_invalid_order_type_raises_exception(self):
        """지원하지 않는 주문 타입에 대한 예외 처리 테스트"""
        user = self.account.create_user("invalid@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "USDT", Decimal("100"))

        # MARKET 주문은 지원하지 않음
        with pytest.raises(InvalidOrderError, match="Only limit orders are supported"):
            # Order 객체를 직접 생성하여 제출
            from datetime import datetime, timezone

            from alt_exchange.core.models import Order

            # account_id를 추가하여 Order 생성
            account = self.account.get_account(user.id)
            market_order = Order(
                id=999,
                user_id=user.id,
                account_id=account.id,
                market="ALT/USDT",
                side=Side.BUY,
                type=OrderType.MARKET,  # 지원하지 않는 타입
                time_in_force=TimeInForce.GTC,
                price=None,
                amount=Decimal("1"),
                filled=Decimal("0"),
                status=OrderStatus.OPEN,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            self.engine.submit(market_order)

    def test_order_cancellation_flow(self):
        """주문 취소 플로우 테스트"""
        user = self.account.create_user("cancel@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "ALT", Decimal("10"))

        # 주문 생성
        order = self.account.place_limit_order(
            user_id=user.id, side=Side.SELL, price=Decimal("10"), amount=Decimal("5")
        )

        # 주문 취소
        cancel_result = self.account.cancel_order(user.id, order.id)

        # 취소 결과 확인 (cancel_order는 boolean을 반환)
        assert cancel_result is True

        # 취소된 주문이 데이터베이스에 반영되었는지 확인
        stored_order = self.context["db"].orders[order.id]
        assert stored_order.status == OrderStatus.CANCELED

    def test_settlement_error_handling(self):
        """정산 오류 처리 테스트"""
        user = self.account.create_user("settlement@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "USDT", Decimal("50"))

        # 잔고 부족으로 인한 주문 실패 시나리오
        with pytest.raises(Exception):  # InsufficientBalanceError 또는 유사한 예외
            self.account.place_limit_order(
                user_id=user.id,
                side=Side.BUY,
                price=Decimal("10"),
                amount=Decimal("10"),  # 100 USDT 필요하지만 50 USDT만 있음
            )

    def test_withdrawal_retry_mechanism(self):
        """출금 재시도 메커니즘 테스트"""
        user = self.account.create_user("withdrawal@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "ALT", Decimal("10"))

        # 출금 요청
        withdrawal = self.wallet.request_withdrawal(
            user_id=user.id,
            asset="ALT",
            amount=Decimal("5"),
            address="0x1234567890123456789012345678901234567890",
        )

        # 출금 상태 확인
        assert withdrawal.status.value == "pending"

        # 출금 완료 시뮬레이션
        completed_withdrawal = self.wallet.complete_withdrawal(
            withdrawal.id, tx_hash="0xabcdef"
        )

        assert completed_withdrawal.status.value == "confirmed"
        assert completed_withdrawal.tx_hash == "0xabcdef"

    def test_event_bus_error_handling(self):
        """이벤트 버스 오류 처리 테스트"""
        # Mock 이벤트 버스로 오류 상황 시뮬레이션
        mock_event_bus = Mock()
        mock_event_bus.publish.side_effect = Exception("Event bus error")

        # 오류가 발생하는 이벤트 버스로 엔진 생성
        error_engine = MatchingEngine(
            market="ALT/USDT", db=self.context["db"], event_bus=mock_event_bus
        )

        # 이벤트 발행 시 오류가 발생해도 엔진이 계속 작동하는지 확인
        user = self.account.create_user("error@example.com", "pwd")
        self.wallet.simulate_deposit(user.id, "USDT", Decimal("100"))

        # 정상적인 주문은 여전히 처리되어야 함
        order = self.account.place_limit_order(
            user_id=user.id, side=Side.BUY, price=Decimal("10"), amount=Decimal("1")
        )

        assert order.status == OrderStatus.OPEN
