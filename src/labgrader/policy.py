"""Load and validate the lab's policy files.

* ``.codetelemetry/org/grader.json``  – organization baseline, real Grader check format,
  no ``repositoryId`` (published with an organization key; see docs/POLICY-HIERARCHY.md).
* ``.codetelemetry/grader.json``      – repository checks, real Grader check format, every
  check carries ``repositoryId``.
* ``.codetelemetry/demo/task-policy.json`` – DEMO SCHEMA. Approved, versioned issue → check
  mapping. Code Telemetry has no task-scope API yet (ELL-607); this file exists so the
  offline simulator can show the intended semantics. It is not read by the product.

The simulator only understands the subset of the Grader matcher it needs:
``matcherRule.include`` with ``exactFingerprint`` ``equals``/``in``. Anything else is
rejected rather than guessed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ORIGINS = ("organization", "repository", "task")

# Keys a task mapping entry may contain. There is intentionally no way to disable,
# exempt or override a broader check: a task can only add requirements.
_TASK_ENTRY_KEYS = {"title", "checks"}
_MAPPING_KEYS = {"schema", "version", "approvedBy", "approvedAt", "repository", "requireIssueLinkage", "issues", "checks"}
_FORBIDDEN_CHECK_KEYS = {"disable", "disables", "exempt", "override", "overrides", "skip"}


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class Check:
    id: str
    name: str
    fingerprints: tuple[str, ...]
    before_push: bool
    repository_id: str | None = None


def _fingerprints(raw: dict) -> tuple[str, ...]:
    rule = raw.get("matcherRule") or {}
    include = rule.get("include") or {}
    if set(rule) - {"include", "argumentNormalization"} or include.get("field") != "exactFingerprint":
        raise PolicyError(f"check {raw.get('id')}: simulator supports exactFingerprint include rules only")
    value = include.get("value")
    if include.get("operator") == "equals" and isinstance(value, str):
        return (value,)
    if include.get("operator") == "in" and isinstance(value, list) and all(isinstance(v, str) for v in value):
        return tuple(value)
    raise PolicyError(f"check {raw.get('id')}: unsupported exactFingerprint operator")


def parse_check(raw: dict) -> Check:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise PolicyError("every check needs an id")
    bad = _FORBIDDEN_CHECK_KEYS & set(raw)
    if bad:
        raise PolicyError(f"check {raw['id']}: {sorted(bad)} is not allowed; policies only add requirements")
    if raw.get("enabled") is False:
        raise PolicyError(f"check {raw['id']}: disabled checks are not allowed in the lab policy")
    return Check(
        id=raw["id"],
        name=raw.get("name", raw["id"]),
        fingerprints=_fingerprints(raw),
        before_push=bool(raw.get("beforePush", False)),
        repository_id=raw.get("repositoryId"),
    )


def load_grader(path: Path, *, scope: str) -> list[Check]:
    data = json.loads(path.read_text())
    checks = [parse_check(c) for c in data.get("checks", [])]
    for c in checks:
        if scope == "organization" and c.repository_id is not None:
            raise PolicyError(f"organization check {c.id} must not set repositoryId")
        if scope == "repository" and not c.repository_id:
            raise PolicyError(f"repository check {c.id} must set repositoryId")
    return checks


@dataclass(frozen=True)
class TaskPolicy:
    version: int
    repository: str
    require_issue_linkage: bool
    issues: dict[str, tuple[str, ...]]  # issue key -> check ids
    checks: dict[str, Check]


def load_task_policy(path: Path) -> TaskPolicy:
    data = json.loads(path.read_text())
    unknown = set(data) - _MAPPING_KEYS
    if unknown:
        raise PolicyError(f"task policy: unknown keys {sorted(unknown)}")
    if data.get("schema") != "codetelemetry-lab/task-policy@demo":
        raise PolicyError("task policy must declare the demo schema")
    if not isinstance(data.get("version"), int) or data["version"] < 1:
        raise PolicyError("task policy needs an integer version >= 1")
    if not data.get("approvedBy"):
        raise PolicyError("task policy must record who approved it")
    checks = {c.id: c for c in (parse_check(raw) for raw in data.get("checks", []))}
    issues: dict[str, tuple[str, ...]] = {}
    for key, entry in data.get("issues", {}).items():
        extra = set(entry) - _TASK_ENTRY_KEYS
        if extra:
            raise PolicyError(f"issue {key}: only {sorted(_TASK_ENTRY_KEYS)} are allowed, got {sorted(extra)}")
        ids = tuple(entry.get("checks", []))
        if not ids:
            raise PolicyError(f"issue {key}: must add at least one check")
        missing = [i for i in ids if i not in checks]
        if missing:
            raise PolicyError(f"issue {key}: unknown checks {missing}")
        issues[key] = ids
    return TaskPolicy(data["version"], data["repository"], bool(data.get("requireIssueLinkage", True)), issues, checks)
