"""Audit log with secret redaction."""

from __future__ import annotations

import json
import re

REDACTED = "[REDACTED]"
_SECRET_KEY = re.compile(r"password|secret|token|api[_-]?key|authorization", re.IGNORECASE)
_CARD = re.compile(r"(?<!\d)\d{9,15}(\d{4})(?!\d)")


def _mask_cards(text: str) -> str:
    return _CARD.sub(lambda m: "*" * (len(m.group(0)) - 4) + m.group(1), text)


def redact(value: object, key: str | None = None) -> object:
    if key is not None and _SECRET_KEY.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {k: redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return _mask_cards(value)
    return value


class AuditLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def record(self, event: str, **fields: object) -> str:
        line = json.dumps({"event": event, **redact(fields)}, sort_keys=True)
        self.lines.append(line)
        return line
