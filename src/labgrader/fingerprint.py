"""Exact command fingerprints for the plain ``make <target>`` commands this lab uses.

The format mirrors the fingerprints Code Telemetry records for shell commands. It was
checked on 2026-11-11 against the backend normalizer, which yields
``v1|shell|||make|org-lint||`` for ``make org-lint`` (and
``v1|shell|||npm|run|test:unit|`` for ``npm run test:unit``, the form HotROD uses).

This is not a general shell normalizer. Anything other than a single ``make <target>``
gets an opaque fingerprint that no lab check matches, so the simulator never credits a
command it does not understand.
"""

from __future__ import annotations

import re

_MAKE = re.compile(r"^\s*make\s+([A-Za-z0-9][A-Za-z0-9_.-]*)\s*$")


def fingerprint(command: str) -> str:
    m = _MAKE.match(command)
    if m:
        return f"v1|shell|||make|{m.group(1)}||"
    return "opaque|" + command
