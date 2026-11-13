"""Acceptance for issue #6: Redact secrets in audit logs."""

import json

import pytest

from parceldesk.audit import REDACTED, AuditLog


def _record(**fields):
    return json.loads(AuditLog().record("e", **fields))


@pytest.mark.parametrize("key", ["password", "client_secret", "accessToken", "api_key", "API-KEY", "Authorization"])
def test_secret_keys_are_redacted(key):
    assert _record(**{key: "hunter2"})[key] == REDACTED


def test_nested_dicts_and_lists():
    out = _record(request={"headers": {"authorization": "Bearer x"}, "items": [{"token": "t"}, "ok"]})
    assert out["request"] == {"headers": {"authorization": REDACTED}, "items": [{"token": REDACTED}, "ok"]}


@pytest.mark.parametrize(("raw", "masked"), [
    ("card 4111111111111111 used", "card ************1111 used"),
    ("4000123412341234567", "***************4567"),
])
def test_card_numbers_keep_last_four(raw, masked):
    assert _record(note=raw)["note"] == masked


def test_non_secret_fields_unchanged():
    assert _record(order_id="o1", amount_cents=5, note="12 items") == {
        "event": "e", "order_id": "o1", "amount_cents": 5, "note": "12 items"}
