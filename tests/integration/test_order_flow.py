"""Repository-level contract: CSV in, customer reads, refunds, listing, audit."""

import json

import pytest

from parceldesk.access import get_order_for_customer
from parceldesk.audit import AuditLog
from parceldesk.csv_import import CsvImportError, import_orders
from parceldesk.pagination import list_orders
from parceldesk.refunds import RefundService
from parceldesk.store import OrderStore

CSV = "order_id,customer_id,total\no1,alice,10.00\no2,bob,5.25\no3,alice,1.10\n"


def test_import_then_refund_then_list():
    store = OrderStore()
    assert import_orders(store, CSV) == 3
    assert get_order_for_customer(store, "alice", "o1").total_cents == 1000
    RefundService(store).refund("o2", 125, "refund-o2-1")
    assert store.get("o2").refunded_cents == 125
    assert [o.order_id for o in list_orders(store, limit=2)] == ["o1", "o2"]
    assert [o.order_id for o in list_orders(store, limit=2, offset=2)] == ["o3"]


def test_import_rejects_missing_columns():
    with pytest.raises(CsvImportError):
        import_orders(OrderStore(), "order_id,total\no1,1.00\n")


def test_import_error_reports_line_number():
    with pytest.raises(CsvImportError, match="line 3"):
        import_orders(OrderStore(), "order_id,customer_id,total\no1,a,1.00\no2,b,abc\n")


def test_audit_round_trip():
    log = AuditLog()
    log.record("import", rows=3)
    assert json.loads(log.lines[0])["rows"] == 3
