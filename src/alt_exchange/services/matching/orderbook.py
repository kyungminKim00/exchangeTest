from __future__ import annotations

from bisect import bisect_left
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Deque, Dict, Generator, Iterable, Optional, Tuple

from alt_exchange.core.models import Order


@dataclass
class PriceLevel:
    price: Decimal
    orders: Deque[Order]


class OrderBookSide:
    def __init__(self, is_buy: bool) -> None:
        self.is_buy = is_buy
        self._levels: Dict[Decimal, PriceLevel] = {}
        self._prices: list[Decimal] = []  # always sorted ascending

    def add_order(self, order: Order) -> None:
        if order.price is None:
            raise ValueError("Limit price is required for resting orders")
        level = self._levels.get(order.price)
        if level is None:
            level = PriceLevel(price=order.price, orders=deque())
            self._insert_price(order.price)
            self._levels[order.price] = level
        level.orders.append(order)

    def _insert_price(self, price: Decimal) -> None:
        index = bisect_left(self._prices, price)
        if index >= len(self._prices) or self._prices[index] != price:
            self._prices.insert(index, price)

    def _remove_price(self, price: Decimal) -> None:
        index = bisect_left(self._prices, price)
        if index < len(self._prices) and self._prices[index] == price:
            self._prices.pop(index)
            self._levels.pop(price, None)

    def best_price(self) -> Optional[Decimal]:
        if not self._prices:
            return None
        return self._prices[-1] if self.is_buy else self._prices[0]

    def iter_price_levels(self) -> Generator[PriceLevel, None, None]:
        prices = reversed(self._prices) if self.is_buy else self._prices
        for price in prices:
            level = self._levels.get(price)
            if level and level.orders:
                yield level

    def pop_best_order(self) -> Optional[Order]:
        best_price = self.best_price()
        if best_price is None:
            return None
        level = self._levels[best_price]
        if not level.orders:
            self._remove_price(best_price)
            return None
        order = level.orders.popleft()
        if not level.orders:
            self._remove_price(best_price)
        return order

    def peek_best_order(self) -> Optional[Order]:
        best_price = self.best_price()
        if best_price is None:
            return None
        level = self._levels[best_price]
        return level.orders[0] if level.orders else None

    def summary(self) -> Iterable[Tuple[Decimal, Decimal]]:
        for level in self.iter_price_levels():
            total = sum(order.remaining() for order in level.orders)
            yield level.price, total
