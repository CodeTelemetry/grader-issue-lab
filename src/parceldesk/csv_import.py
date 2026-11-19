"""CSV order import.

Expected columns: ``order_id,customer_id,total`` where ``total`` is a decimal
amount such as ``12.50``. Imports are atomic: if any row is invalid, nothing is
added to the store.
"""

from __future__ import annotations

import csv
import io

from .money import to_cents
from .store import Order, OrderStore

REQUIRED_COLUMNS = ("order_id", "customer_id", "total")


class CsvImportError(ValueError):
    """Raised when a CSV file cannot be imported."""


def import_orders(store: OrderStore, text: str) -> int:
    """Validate every row first, then import them all. Returns the number imported."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise CsvImportError(f"missing columns: {', '.join(missing)}")
    staged: list[Order] = []
    seen: set[str] = set()
    for line, row in enumerate(reader, start=2):
        try:
            order = Order(row["order_id"].strip(), row["customer_id"].strip(), to_cents(row["total"].strip()))
        except (ValueError, AttributeError) as exc:
            raise CsvImportError(f"line {line}: {exc}") from exc
        if not order.order_id or not order.customer_id:
            raise CsvImportError(f"line {line}: order_id and customer_id are required")
        if order.order_id in seen or order.order_id in {o.order_id for o in store.all()}:
            raise CsvImportError(f"line {line}: duplicate order id: {order.order_id}")
        seen.add(order.order_id)
        staged.append(order)
    for order in staged:
        store.add(order)
    return len(staged)
