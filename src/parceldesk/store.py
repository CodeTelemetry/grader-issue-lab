"""In-memory order store for ParcelDesk."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Order:
    order_id: str
    customer_id: str
    total_cents: int
    refunded_cents: int = 0
    notes: list[str] = field(default_factory=list)


class OrderStore:
    """A deliberately small, insertion-ordered store."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        if order.order_id in self._orders:
            raise ValueError(f"duplicate order id: {order.order_id}")
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise KeyError(f"unknown order: {order_id}") from None

    def all(self) -> list[Order]:
        return list(self._orders.values())

    def __len__(self) -> int:
        return len(self._orders)
