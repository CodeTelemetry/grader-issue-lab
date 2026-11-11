"""Refunds. Each idempotency key refunds at most once."""

from __future__ import annotations

import os
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
        self._receipts: dict[str, RefundReceipt] = {}

    def refund(self, order_id: str, amount_cents: int, idempotency_key: str) -> RefundReceipt:
        if amount_cents <= 0:
            raise RefundError("refund amount must be positive")
        if not idempotency_key:
            raise RefundError("idempotency key is required")
        previous = self._receipts.get(idempotency_key)
        if previous is not None:
            if (previous.order_id, previous.amount_cents) != (order_id, amount_cents):
                raise RefundError("idempotency key was already used for a different refund")
            return previous
        order = self._store.get(order_id)
        if order.refunded_cents + amount_cents > order.total_cents:
            raise RefundError("refund exceeds order total")
        order.refunded_cents += amount_cents
        receipt = RefundReceipt(order_id, amount_cents, idempotency_key, order.refunded_cents)
        self._receipts[idempotency_key] = receipt
        return receipt
