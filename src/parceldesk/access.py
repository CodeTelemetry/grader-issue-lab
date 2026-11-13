"""Customer-facing order access: customers can read only their own orders."""

from __future__ import annotations

from .store import Order, OrderStore


class AccessDenied(PermissionError):
    pass


def get_order_for_customer(store: OrderStore, customer_id: str, order_id: str) -> Order:
    try:
        order = store.get(order_id)
    except KeyError:
        raise AccessDenied("order not found") from None
    if order.customer_id != customer_id:
        raise AccessDenied("order not found")
    return order
