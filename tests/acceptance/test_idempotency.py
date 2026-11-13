"""Acceptance for issue #2: Make refunds idempotent."""

import pytest

from parceldesk.refunds import RefundError, RefundService
from parceldesk.store import Order, OrderStore


@pytest.fixture
def setup():
    store = OrderStore()
    store.add(Order("o1", "c1", 1000))
    store.add(Order("o2", "c1", 1000))
    return store, RefundService(store)


def test_retry_with_same_key_refunds_once(setup):
    store, service = setup
    first = service.refund("o1", 300, "k1")
    second = service.refund("o1", 300, "k1")
    assert second == first
    assert store.get("o1").refunded_cents == 300


@pytest.mark.parametrize(("order_id", "amount"), [("o1", 200), ("o2", 300)])
def test_key_reuse_for_different_refund_is_rejected(setup, order_id, amount):
    store, service = setup
    service.refund("o1", 300, "k1")
    with pytest.raises(RefundError):
        service.refund(order_id, amount, "k1")
    assert store.get("o1").refunded_cents == 300
    assert store.get("o2").refunded_cents == 0


def test_different_keys_refund_independently(setup):
    store, service = setup
    service.refund("o1", 100, "k1")
    service.refund("o1", 100, "k2")
    assert store.get("o1").refunded_cents == 200
