"""Currency helpers.

Known defect (lab issue "Fix currency rounding"): ``to_cents`` goes through a
binary float and Python's round-half-to-even, so half-cent amounts such as
"2.675" or "0.125" round the wrong way.
"""

from __future__ import annotations

from decimal import Decimal


def to_cents(amount: str | Decimal) -> int:
    """Convert a decimal currency amount to integer cents."""
    return int(round(float(amount) * 100))


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
