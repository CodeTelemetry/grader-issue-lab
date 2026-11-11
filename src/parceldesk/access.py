"""Customer-facing order access.

Known defect (lab issue "Restrict customer order access"): any customer can read
any order by id.
"""

from __future__ import annotations

from .store import Order, OrderStore


class AccessDenied(PermissionError):
    pass


def get_order_for_customer(store: OrderStore, customer_id: str, order_id: str) -> Order:
    return store.get(order_id)
