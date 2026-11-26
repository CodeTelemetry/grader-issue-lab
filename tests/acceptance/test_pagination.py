"""Acceptance for issue #5: Implement cursor pagination."""

import pytest

from parceldesk.pagination import list_orders_page
from parceldesk.store import Order, OrderStore


def _store(n):
    s = OrderStore()
    for i in range(n):
        s.add(Order(f"o{i}", "c", i))
    return s


def test_walks_all_pages_without_gaps_or_repeats():
    store = _store(7)
    seen, cursor = [], None
    while True:
        page, cursor = list_orders_page(store, limit=3, cursor=cursor)
        seen += [o.order_id for o in page]
        if cursor is None:
            break
    assert seen == [f"o{i}" for i in range(7)]


def test_orders_added_between_pages_do_not_shift_later_pages():
    store = _store(4)
    first, cursor = list_orders_page(store, limit=2)
    store.add(Order("late", "c", 0))
    second, _ = list_orders_page(store, limit=2, cursor=cursor)
    assert [o.order_id for o in first + second] == ["o0", "o1", "o2", "o3"]


def test_last_page_has_no_cursor():
    _, cursor = list_orders_page(_store(2), limit=2)
    assert cursor is None


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_bounds(limit):
    with pytest.raises(ValueError):
        list_orders_page(_store(1), limit=limit)


@pytest.mark.parametrize("cursor", ["%%%", "bm9wZQ=="])
def test_malformed_cursor(cursor):
    with pytest.raises(ValueError):
        list_orders_page(_store(3), limit=1, cursor=cursor)
