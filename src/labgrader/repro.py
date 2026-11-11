"""Re-run every synthetic scenario and compare with the expected-results matrix.

    python -m labgrader.repro                 # all scenarios, exit 1 on any mismatch
    python -m labgrader.repro --explain FILE  # one fixture, full per-check detail
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluate import Evaluation, evaluate
from .policy import load_grader, load_task_policy
from .resolve import resolve

ROOT = Path(__file__).resolve().parents[2]
BANNER = "SYNTHETIC OFFLINE SIMULATION - not a Code Telemetry receipt"


def load_policies(root: Path = ROOT):
    ct = root / ".codetelemetry"
    org = load_grader(ct / "org" / "grader.json", scope="organization")
    repo = load_grader(ct / "grader.json", scope="repository")
    tasks = [load_task_policy(ct / "demo" / "task-policy.json")]
    return org, repo, tasks


def run_fixture(path: Path, root: Path = ROOT) -> tuple[dict, Evaluation, object]:
    fixture = json.loads(path.read_text())
    if fixture.get("synthetic") is not True:
        raise SystemExit(f"{path}: refusing to grade a fixture not marked synthetic")
    org, repo, tasks = load_policies(root)
    pr = fixture["pullRequest"]
    policy = resolve(
        repository_id=fixture["repositoryId"],
        repository=pr["repository"],
        org_checks=org,
        repo_checks=repo,
        task_policies=tasks,
        linkage=pr.get("linkage"),
    )
    # pr["body"] is deliberately never passed anywhere: it is untrusted input.
    return fixture, evaluate(policy, fixture["session"]["events"]), policy


def summarize(evaluation: Evaluation) -> dict:
    return {"overall": evaluation.overall, "checks": {v.check_id: v.verdict for v in evaluation.checks}}


def explain(path: Path) -> None:
    fixture, ev, policy = run_fixture(path)
    print(BANNER)
    print(f"scenario: {fixture['scenario']}  repo: {fixture['repositoryId']}  PR head: {fixture['pullRequest']['headSha']}")
    print(f"task policy version: {policy.task_policy_version}  linked issues: {', '.join(policy.linked_issues) or '-'}")
    print(f"final edit seq: {ev.final_edit_seq}  push seq: {ev.push_seq}")
    for v in ev.checks:
        print(f"  {v.verdict:8} {v.check_id:28} [{', '.join(v.origins)}] {v.reason}")
    for reason in ev.unknown_reasons:
        print(f"  unknown  (policy) {reason}")
    print(f"OVERALL: {ev.overall.upper()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--explain", type=Path)
    args = parser.parse_args(argv)
    if args.explain:
        explain(args.explain)
        return 0

    expected = json.loads((ROOT / "examples" / "scenarios" / "expected.json").read_text())["scenarios"]
    fixtures = sorted((ROOT / "examples" / "evidence").glob("*.json"))
    print(BANNER)
    failures = 0
    seen = set()
    for path in fixtures:
        fixture, ev, _ = run_fixture(path)
        name = fixture["scenario"]
        seen.add(name)
        got = summarize(ev)
        want = expected.get(name)
        ok = want == got
        failures += not ok
        print(f"{'ok  ' if ok else 'DIFF'} {name:34} {got['overall']}")
        if not ok:
            print(f"     expected {json.dumps(want, sort_keys=True)}\n     got      {json.dumps(got, sort_keys=True)}")
    for name in sorted(set(expected) - seen):
        failures += 1
        print(f"DIFF {name:34} expected scenario has no fixture")
    print(f"{len(fixtures)} fixtures, {failures} mismatches")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
