"""Currency helpers."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_CENT = Decimal("0.01")


def to_cents(amount: str | Decimal) -> int:
    """Convert a decimal currency amount to integer cents, rounding half away from zero."""
    try:
        value = amount if isinstance(amount, Decimal) else Decimal(str(amount).strip())
    except InvalidOperation:
        raise ValueError(f"not a decimal amount: {amount!r}") from None
    if not value.is_finite():
        raise ValueError(f"not a finite amount: {amount!r}")
    return int(value.quantize(_CENT, rounding=ROUND_HALF_UP) * 100)


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
