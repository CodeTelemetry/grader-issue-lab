import json

import pytest

from parceldesk.audit import AuditLog
from parceldesk.refunds import RefundError, RefundService
from parceldesk.store import Order, OrderStore


def _service():
    store = OrderStore()
    store.add(Order("o1", "c1", 1000))
    return store, RefundService(store)


def test_refund_reduces_balance():
    store, service = _service()
    receipt = service.refund("o1", 250, "k1")
    assert receipt.refunded_total_cents == 250
    assert store.get("o1").refunded_cents == 250


def test_refund_cannot_exceed_total():
    _, service = _service()
    with pytest.raises(RefundError):
        service.refund("o1", 1001, "k1")


def test_refund_requires_key():
    _, service = _service()
    with pytest.raises(RefundError):
        service.refund("o1", 1, "")


def test_audit_records_json_line():
    log = AuditLog()
    line = log.record("refund", order_id="o1", amount_cents=5)
    assert json.loads(line) == {"event": "refund", "order_id": "o1", "amount_cents": 5}
