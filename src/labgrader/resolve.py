"""Effective policy = organization ∪ repository ∪ (union of task checks for every linked issue).

Rules the simulator enforces:

* Organization checks apply to every repository.
* Repository checks apply only when their ``repositoryId`` equals the recorded one.
* Task checks come only from the approved, versioned mapping, keyed by issues that a
  *trusted* linkage source reports (GitHub's closing-issue references for the PR, as
  fetched by the service). The PR body, issue text and agent output are never read.
* A task can only add checks. A check required at several levels keeps every origin.
* If the repository requires issue linkage and the linkage is missing, untrusted, or
  names an issue with no approved mapping, the task level is UNKNOWN (fail closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import Check, TaskPolicy

TRUSTED_LINKAGE_SOURCES = frozenset({"github-closing-issues-references"})


@dataclass
class EffectiveCheck:
    check: Check
    origins: list[str] = field(default_factory=list)  # e.g. ["organization"], ["task:repo#1", "task:repo#4"]


@dataclass
class EffectivePolicy:
    repository_id: str
    checks: dict[str, EffectiveCheck]
    task_policy_version: int | None
    linked_issues: tuple[str, ...]
    unknown_reasons: list[str]


def resolve(
    *,
    repository_id: str,
    repository: str,
    org_checks: list[Check],
    repo_checks: list[Check],
    task_policies: list[TaskPolicy],
    linkage: dict | None,
) -> EffectivePolicy:
    checks: dict[str, EffectiveCheck] = {}

    def add(check: Check, origin: str) -> None:
        existing = checks.get(check.id)
        if existing is None:
            checks[check.id] = EffectiveCheck(check, [origin])
            return
        if existing.check.fingerprints != check.fingerprints:
            # Same id, different definition: never silently pick one.
            raise ValueError(f"check {check.id} is defined differently at two levels")
        existing.origins.append(origin)

    for c in org_checks:
        add(c, "organization")
    for c in repo_checks:
        if c.repository_id == repository_id:
            add(c, "repository")

    unknown: list[str] = []
    policy = next((p for p in task_policies if p.repository == repository), None)
    linked: tuple[str, ...] = ()
    if policy is not None:
        source = (linkage or {}).get("source")
        issues = tuple((linkage or {}).get("issues") or ())
        if source not in TRUSTED_LINKAGE_SOURCES:
            if policy.require_issue_linkage:
                unknown.append(
                    "issue linkage unavailable or from an untrusted source "
                    f"({source or 'none'}); task checks cannot be resolved"
                )
        else:
            linked = issues
            if not issues and policy.require_issue_linkage:
                unknown.append("pull request closes no issue; task checks cannot be resolved")
            for issue in issues:
                ids = policy.issues.get(issue)
                if ids is None:
                    unknown.append(f"{issue} has no approved task policy (mapping v{policy.version})")
                    continue
                for check_id in ids:
                    add(policy.checks[check_id], f"task:{issue}")

    return EffectivePolicy(repository_id, checks, policy.version if policy else None, linked, unknown)
