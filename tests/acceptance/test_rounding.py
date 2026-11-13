"""Acceptance for issue #1: Fix currency rounding."""

from decimal import Decimal

import pytest

from parceldesk.money import to_cents


@pytest.mark.parametrize(
    ("amount", "cents"),
    [("2.675", 268), ("0.125", 13), ("1.005", 101), ("0.004", 0), ("19.999", 2000), (Decimal("0.115"), 12)],
)
def test_half_up_exact_decimal(amount, cents):
    assert to_cents(amount) == cents


def test_negative_rounds_half_away_from_zero():
    assert to_cents("-2.675") == -268


@pytest.mark.parametrize("bad", ["abc", "", "1.2.3", "NaN", "Infinity"])
def test_rejects_non_numeric(bad):
    with pytest.raises(ValueError):
        to_cents(bad)
