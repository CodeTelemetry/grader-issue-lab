"""Refunds.

Known defect (lab issue "Make refunds idempotent"): retrying a refund with the
same idempotency key refunds the customer twice.
"""

from __future__ import annotations

from dataclasses import dataclass

from .store import OrderStore


class RefundError(ValueError):
    pass


@dataclass(frozen=True)
class RefundReceipt:
    order_id: str
    amount_cents: int
    idempotency_key: str
    refunded_total_cents: int


class RefundService:
    def __init__(self, store: OrderStore) -> None:
        self._store = store

    def refund(self, order_id: str, amount_cents: int, idempotency_key: str) -> RefundReceipt:
        if amount_cents <= 0:
            raise RefundError("refund amount must be positive")
        if not idempotency_key:
            raise RefundError("idempotency key is required")
        order = self._store.get(order_id)
        if order.refunded_cents + amount_cents > order.total_cents:
            raise RefundError("refund exceeds order total")
        order.refunded_cents += amount_cents
        return RefundReceipt(order_id, amount_cents, idempotency_key, order.refunded_cents)
