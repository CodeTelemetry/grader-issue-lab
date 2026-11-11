"""Order listing.

Lab issue "Implement cursor pagination" adds ``list_orders_page`` with an
opaque cursor so pages stay stable while orders are added.
"""

from __future__ import annotations

from .store import Order, OrderStore


def list_orders(store: OrderStore, limit: int = 50, offset: int = 0) -> list[Order]:
    if limit < 1 or offset < 0:
        raise ValueError("limit must be >= 1 and offset >= 0")
    return store.all()[offset : offset + limit]
