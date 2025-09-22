"""
API Main 모듈의 누락된 커버리지 부분을 테스트
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from alt_exchange.api.main import create_order, get_context
from alt_exchange.core.enums import OrderType, Side, TimeInForce
from alt_exchange.core.exceptions import InsufficientBalanceError
from alt_exchange.core.models import Order, OrderStatus


class TestAPIMainCoverage:
    """API Main 모듈 커버리지 테스트"""

    def test_get_context_initialization(self):
        """get_context 함수의 전역 컨텍스트 초기화 테스트"""
        # 전역 컨텍스트를 None으로 리셋
        import alt_exchange.api.main

        alt_exchange.api.main._context = None

        # get_context 호출 시 컨텍스트가 초기화되는지 확인
        context = get_context()
        assert context is not None
        assert isinstance(context, dict)

        # 두 번째 호출 시 같은 인스턴스가 반환되는지 확인
        context2 = get_context()
        assert context is context2

    @pytest.mark.asyncio
    async def test_create_order_exception_handling(self):
        """create_order의 예외 처리 브랜치 테스트"""
        from alt_exchange.api.main import OrderRequest

        # 잘못된 주문 요청 생성
        order_request = OrderRequest(
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price="100",
            amount="invalid_amount",  # 잘못된 금액
        )

        # get_current_user_id를 모킹
        with patch("alt_exchange.api.main.get_current_user_id", return_value=1):
            # 예외가 발생해야 함
            with pytest.raises(Exception):
                await create_order(order_request)

    @pytest.mark.asyncio
    async def test_create_order_insufficient_balance_exception(self):
        """create_order의 잔액 부족 예외 처리 테스트"""
        from alt_exchange.api.main import OrderRequest

        order_request = OrderRequest(
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price="1000000",  # 매우 높은 가격
            amount="1000",  # 큰 수량
        )

        # account_service를 모킹하여 InsufficientBalanceError 발생
        mock_account_service = Mock()
        mock_account_service.place_limit_order.side_effect = InsufficientBalanceError(
            "Insufficient balance"
        )

        with (
            patch("alt_exchange.api.main.get_current_user_id", return_value=1),
            patch("alt_exchange.api.main.get_context") as mock_get_context,
        ):

            mock_context = {"account_service": mock_account_service}
            mock_get_context.return_value = mock_context

            # 예외가 발생해야 함
            with pytest.raises(Exception):
                await create_order(order_request)

    @pytest.mark.asyncio
    async def test_create_order_invalid_price_exception(self):
        """create_order의 잘못된 가격 예외 처리 테스트"""
        from alt_exchange.api.main import OrderRequest

        order_request = OrderRequest(
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price="invalid_price",  # 잘못된 가격 형식
            amount="100",
        )

        with patch("alt_exchange.api.main.get_current_user_id", return_value=1):
            # Decimal 변환 시 예외가 발생해야 함
            with pytest.raises(Exception):
                await create_order(order_request)

    @pytest.mark.asyncio
    async def test_create_order_invalid_amount_exception(self):
        """create_order의 잘못된 수량 예외 처리 테스트"""
        from alt_exchange.api.main import OrderRequest

        order_request = OrderRequest(
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price="100",
            amount="invalid_amount",  # 잘못된 수량 형식
        )

        with patch("alt_exchange.api.main.get_current_user_id", return_value=1):
            # Decimal 변환 시 예외가 발생해야 함
            with pytest.raises(Exception):
                await create_order(order_request)

    @pytest.mark.asyncio
    async def test_create_order_account_service_exception(self):
        """create_order의 account_service 예외 처리 테스트"""
        from alt_exchange.api.main import OrderRequest

        order_request = OrderRequest(
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price="100",
            amount="100",
        )

        # account_service를 모킹하여 일반 예외 발생
        mock_account_service = Mock()
        mock_account_service.place_limit_order.side_effect = Exception(
            "Account service error"
        )

        with (
            patch("alt_exchange.api.main.get_current_user_id", return_value=1),
            patch("alt_exchange.api.main.get_context") as mock_get_context,
        ):

            mock_context = {"account_service": mock_account_service}
            mock_get_context.return_value = mock_context

            # 예외가 발생해야 함
            with pytest.raises(Exception):
                await create_order(order_request)

    def test_get_context_multiple_calls(self):
        """get_context 함수의 여러 호출 테스트"""
        # 전역 컨텍스트를 None으로 리셋
        import alt_exchange.api.main

        alt_exchange.api.main._context = None

        # 첫 번째 호출
        context1 = get_context()
        assert context1 is not None

        # 두 번째 호출 (같은 인스턴스 반환)
        context2 = get_context()
        assert context1 is context2

        # 세 번째 호출 (같은 인스턴스 반환)
        context3 = get_context()
        assert context1 is context3
