"""Grade synthetic session evidence against an effective policy.

Evidence is an ordered list of events: ``edit``, ``command`` (with ``exitCode`` and an
optional ``truncated`` flag), ``gap`` (telemetry is missing for an unknown stretch: an
edit may have happened there), and ``push``.

Per check, as of the final push:

* PASS    – the latest matching run after the final edit (and after any gap) succeeded.
* FAIL    – that run failed.
* STALE   – the check only ran before the final edit. Earlier success is not inherited.
* MISSING – the check never ran, and the evidence is complete enough to say so.
* UNKNOWN – the deciding run's output was truncated, or a gap means we can neither
            prove a post-edit run happened nor that it did not. Never reported as a
            pass or as a proven absence.

Overall: FAIL if any check is FAIL/STALE/MISSING; otherwise UNKNOWN if any check or the
policy resolution is unknown; otherwise PASS.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fingerprint import fingerprint
from .resolve import EffectivePolicy

PASS, FAIL, STALE, MISSING, UNKNOWN = "pass", "fail", "stale", "missing", "unknown"
_FAILING = {FAIL, STALE, MISSING}


@dataclass
class CheckVerdict:
    check_id: str
    origins: list[str]
    verdict: str
    reason: str
    observed_seq: int | None = None


@dataclass
class Evaluation:
    overall: str
    checks: list[CheckVerdict]
    unknown_reasons: list[str]
    final_edit_seq: int
    push_seq: int | None


def evaluate(policy: EffectivePolicy, events: list[dict]) -> Evaluation:
    events = sorted(events, key=lambda e: e["seq"])
    pushes = [e["seq"] for e in events if e["type"] == "push"]
    push_seq = pushes[-1] if pushes else None
    before = [e for e in events if push_seq is None or e["seq"] < push_seq]
    final_edit = max((e["seq"] for e in before if e["type"] == "edit"), default=0)
    last_gap = max((e["seq"] for e in before if e["type"] == "gap"), default=0)

    verdicts: list[CheckVerdict] = []
    for check_id, eff in policy.checks.items():
        runs = [
            e for e in before
            if e["type"] == "command" and fingerprint(e["command"]) in eff.check.fingerprints
        ]
        verdicts.append(_grade(check_id, eff.origins, runs, final_edit, last_gap, push_seq))

    unknown = list(policy.unknown_reasons)
    if push_seq is None:
        unknown.append("no push observed; nothing to grade against")
    states = {v.verdict for v in verdicts}
    if states & _FAILING:
        overall = FAIL
    elif UNKNOWN in states or unknown:
        overall = UNKNOWN
    else:
        overall = PASS
    return Evaluation(overall, verdicts, unknown, final_edit, push_seq)


def _grade(check_id, origins, runs, final_edit, last_gap, push_seq) -> CheckVerdict:
    boundary = max(final_edit, last_gap)
    after = [r for r in runs if r["seq"] > boundary]
    if after:
        latest = after[-1]
        if latest.get("truncated"):
            return CheckVerdict(check_id, origins, UNKNOWN, "deciding run's output was truncated", latest["seq"])
        if latest.get("exitCode") == 0:
            return CheckVerdict(check_id, origins, PASS, "succeeded after the final edit", latest["seq"])
        return CheckVerdict(check_id, origins, FAIL, f"exited {latest.get('exitCode')} after the final edit", latest["seq"])
    if last_gap > final_edit:
        # Runs (or edits) may sit inside the gap. Neither success nor absence is provable.
        return CheckVerdict(check_id, origins, UNKNOWN, "telemetry gap after the final observed edit")
    if runs:
        return CheckVerdict(check_id, origins, STALE, "only ran before the final edit", runs[-1]["seq"])
    return CheckVerdict(check_id, origins, MISSING, "never ran before push")
