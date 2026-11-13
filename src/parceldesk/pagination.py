"""Order listing with offset and opaque-cursor pagination."""

from __future__ import annotations

import base64
import binascii

from .store import Order, OrderStore

MAX_LIMIT = 100


def list_orders(store: OrderStore, limit: int = 50, offset: int = 0) -> list[Order]:
    if limit < 1 or offset < 0:
        raise ValueError("limit must be >= 1 and offset >= 0")
    return store.all()[offset : offset + limit]


def _encode(order_id: str) -> str:
    return base64.urlsafe_b64encode(order_id.encode()).decode()


def _decode(cursor: str) -> str:
    try:
        return base64.urlsafe_b64decode(cursor.encode()).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError("malformed cursor") from None


def list_orders_page(store: OrderStore, limit: int = 50, cursor: str | None = None) -> tuple[list[Order], str | None]:
    """Return one page of orders as ``(orders, next_cursor)``.

    ``cursor`` is the opaque token from a previous call; it names the last order
    already returned, so the page starts with the order after it. Omit it to
    start from the first order. ``next_cursor`` is ``None`` on the last page.

    Raises ``ValueError`` if ``limit`` is outside ``1..MAX_LIMIT`` or the cursor
    is malformed or names an unknown order.
    """
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    orders = store.all()
    start = 0
    if cursor is not None:
        position = {o.order_id: i for i, o in enumerate(orders)}.get(_decode(cursor))
        if position is None:
            raise ValueError("malformed cursor")
        start = position + 1
    page = orders[start : start + limit]
    has_more = start + limit < len(orders)
    return page, (_encode(page[-1].order_id) if page and has_more else None)
