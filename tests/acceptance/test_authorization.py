"""Acceptance for issue #4: Restrict customer order access."""

import pytest

from parceldesk.access import AccessDenied, get_order_for_customer
from parceldesk.store import Order, OrderStore


@pytest.fixture
def store():
    s = OrderStore()
    s.add(Order("o1", "alice", 100))
    s.add(Order("o2", "bob", 200))
    return s


def test_owner_can_read(store):
    assert get_order_for_customer(store, "alice", "o1").total_cents == 100


def test_other_customer_is_denied(store):
    with pytest.raises(AccessDenied):
        get_order_for_customer(store, "alice", "o2")


def test_unknown_order_is_indistinguishable_from_denied(store):
    with pytest.raises(AccessDenied) as unknown:
        get_order_for_customer(store, "alice", "nope")
    with pytest.raises(AccessDenied) as other:
        get_order_for_customer(store, "alice", "o2")
    assert str(unknown.value) == str(other.value)
