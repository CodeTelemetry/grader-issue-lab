"""CSV order import.

Expected columns: ``order_id,customer_id,total`` where ``total`` is a decimal
amount such as ``12.50``.

Known defect (lab issue "Make CSV import atomic"): a bad row part-way through
the file leaves the rows before it in the store.
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
    """Import orders from CSV text. Returns the number of rows imported."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise CsvImportError(f"missing columns: {', '.join(missing)}")
    count = 0
    for line, row in enumerate(reader, start=2):
        try:
            order = Order(row["order_id"].strip(), row["customer_id"].strip(), to_cents(row["total"].strip()))
        except (ValueError, AttributeError) as exc:
            raise CsvImportError(f"line {line}: {exc}") from exc
        if not order.order_id or not order.customer_id:
            raise CsvImportError(f"line {line}: order_id and customer_id are required")
        try:
            store.add(order)
        except ValueError as exc:
            raise CsvImportError(f"line {line}: {exc}") from exc
        count += 1
    return count
