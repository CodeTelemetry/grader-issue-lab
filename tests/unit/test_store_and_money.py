import pytest

from parceldesk.money import format_cents, to_cents
from parceldesk.store import Order, OrderStore


def test_to_cents_whole_amounts():
    assert to_cents("12.50") == 1250
    assert to_cents("0") == 0


def test_format_cents():
    assert format_cents(1250) == "12.50"
    assert format_cents(-5) == "-0.05"


def test_store_rejects_duplicate_ids():
    store = OrderStore()
    store.add(Order("o1", "c1", 100))
    with pytest.raises(ValueError):
        store.add(Order("o1", "c2", 200))


def test_store_unknown_order():
    with pytest.raises(KeyError):
        OrderStore().get("missing")
