"""Audit log.

Known defect (lab issue "Redact secrets in audit logs"): secret-looking fields
(card numbers, API keys, passwords, tokens) are written verbatim.
"""

from __future__ import annotations

import json


class AuditLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def record(self, event: str, **fields: object) -> str:
        line = json.dumps({"event": event, **fields}, sort_keys=True)
        self.lines.append(line)
        return line
