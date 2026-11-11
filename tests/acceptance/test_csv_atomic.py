"""Acceptance for issue #3: Make CSV import atomic."""

import pytest

from parceldesk.csv_import import CsvImportError, import_orders
from parceldesk.store import Order, OrderStore

HEADER = "order_id,customer_id,total\n"


@pytest.mark.parametrize(
    "bad_rows",
    [
        "o1,a,1.00\no2,b,abc\n",  # bad total
        "o1,a,1.00\n,b,2.00\n",  # missing id
        "o1,a,1.00\no1,b,2.00\n",  # duplicate within file
        "o1,a,1.00\nexisting,b,2.00\n",  # duplicate against store
    ],
)
def test_invalid_row_imports_nothing(bad_rows):
    store = OrderStore()
    store.add(Order("existing", "z", 1))
    with pytest.raises(CsvImportError, match=r"3"):
        import_orders(store, HEADER + bad_rows)
    assert [o.order_id for o in store.all()] == ["existing"]


def test_valid_file_imports_all_in_order():
    store = OrderStore()
    assert import_orders(store, HEADER + "o1,a,1.00\no2,b,2.00\no3,a,3.00\n") == 3
    assert [o.order_id for o in store.all()] == ["o1", "o2", "o3"]
