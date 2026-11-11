"""Properties of the offline org -> repo -> task simulator."""

import json
from pathlib import Path

import pytest

from labgrader.evaluate import evaluate
from labgrader.policy import PolicyError, load_task_policy, parse_check
from labgrader.repro import ROOT, load_policies, main, run_fixture
from labgrader.resolve import resolve

R = "CodeTelemetry/grader-issue-lab"
TRUSTED = "github-closing-issues-references"


def _resolve(issues, source=TRUSTED, repository_id="grader-issue-lab", repository=R):
    org, repo, tasks = load_policies()
    return resolve(repository_id=repository_id, repository=repository, org_checks=org, repo_checks=repo,
                   task_policies=tasks, linkage={"source": source, "issues": [f"{R}#{n}" for n in issues]})


def test_effective_policy_is_cumulative_with_origins():
    policy = _resolve([1])
    assert {k: v.origins for k, v in policy.checks.items()} == {
        "org.lint": ["organization"],
        "org.unit": ["organization"],
        "parceldesk.integration": ["repository"],
        "task.rounding": [f"task:{R}#1"],
    }
    assert policy.task_policy_version == 1
    assert policy.unknown_reasons == []


def test_multiple_issues_union_task_checks():
    assert {"task.rounding", "task.authorization"} <= set(_resolve([1, 4]).checks)


def test_repository_checks_are_isolated_to_their_repository_id():
    policy = _resolve([], repository_id="ledger-lite", repository="CodeTelemetry/ledger-lite")
    assert set(policy.checks) == {"org.lint", "org.unit"}
    assert policy.unknown_reasons == []  # ledger-lite has no task policy, so no linkage requirement


@pytest.mark.parametrize("source", [None, "pr-body", "issue-text", "agent"])
def test_untrusted_or_missing_linkage_is_unknown_and_adds_nothing(source):
    policy = _resolve([1], source=source)
    assert "task.rounding" not in policy.checks
    assert policy.unknown_reasons
    assert {"org.lint", "org.unit", "parceldesk.integration"} <= set(policy.checks)


def test_unmapped_issue_fails_closed():
    assert any("no approved task policy" in r for r in _resolve([99]).unknown_reasons)


@pytest.mark.parametrize("key", ["disable", "override", "exempt", "skip"])
def test_policies_cannot_disable_broader_checks(key):
    raw = json.loads((ROOT / ".codetelemetry/org/grader.json").read_text())["checks"][0]
    with pytest.raises(PolicyError):
        parse_check({**raw, key: ["org.lint"]})
    with pytest.raises(PolicyError):
        parse_check({**raw, "enabled": False})


def test_task_mapping_entries_may_only_add(tmp_path: Path):
    data = json.loads((ROOT / ".codetelemetry/demo/task-policy.json").read_text())
    data["issues"][f"{R}#1"]["disableChecks"] = ["org.lint"]
    path = tmp_path / "p.json"
    path.write_text(json.dumps(data))
    with pytest.raises(PolicyError):
        load_task_policy(path)


def test_task_mapping_requires_version_and_approval(tmp_path: Path):
    data = json.loads((ROOT / ".codetelemetry/demo/task-policy.json").read_text())
    for broken in ({**data, "version": 0}, {k: v for k, v in data.items() if k != "approvedBy"}):
        path = tmp_path / "p.json"
        path.write_text(json.dumps(broken))
        with pytest.raises(PolicyError):
            load_task_policy(path)


def test_pr_body_cannot_change_policy():
    fixture, ev, policy = run_fixture(ROOT / "examples/evidence/09-pr-body-injection.json")
    assert "skip org.lint" in fixture["pullRequest"]["body"]
    assert {v.check_id: v.verdict for v in ev.checks}["org.lint"] == "missing"
    assert ev.overall == "fail"


def _events(*items):
    return [{**e, "seq": i} for i, e in enumerate(items, 1)]


def test_success_before_final_edit_is_never_inherited():
    policy = _resolve([1])
    run = [{"type": "command", "command": f"make {t}", "exitCode": 0}
           for t in ("org-lint", "org-unit", "repo-integration", "task-rounding")]
    ev = evaluate(policy, _events({"type": "edit"}, *run, {"type": "edit"}, {"type": "push"}))
    assert {v.verdict for v in ev.checks} == {"stale"}
    assert ev.overall == "fail"


def test_truncated_or_gapped_evidence_is_unknown_not_pass_or_absent():
    policy = _resolve([1])
    ev = evaluate(policy, _events({"type": "edit"}, {"type": "gap"}, {"type": "push"}))
    assert {v.verdict for v in ev.checks} == {"unknown"}
    assert ev.overall == "unknown"


def test_events_after_push_do_not_count():
    policy = _resolve([1])
    run = [{"type": "command", "command": f"make {t}", "exitCode": 0}
           for t in ("org-lint", "org-unit", "repo-integration", "task-rounding")]
    ev = evaluate(policy, _events({"type": "edit"}, {"type": "push"}, *run))
    assert ev.overall == "fail"


def test_wrapped_commands_are_not_credited():
    policy = _resolve([1])
    ev = evaluate(policy, _events({"type": "edit"}, {"type": "command", "command": "make org-lint || true", "exitCode": 0},
                                  {"type": "push"}))
    assert {v.check_id: v.verdict for v in ev.checks}["org.lint"] == "missing"


def test_all_fixtures_match_expected_matrix():
    assert main([]) == 0
