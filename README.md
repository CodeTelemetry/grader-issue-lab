# Grader issue lab

A small, reproducible example of the Code Telemetry PR Grader applying
**organization → repository → task (GitHub issue)** validation policy to six real
GitHub issues and pull requests.

> **Status, 2026-11-11.** Organization and repository checks are written in the
> real Grader format but **have not been published live from this lab yet**. The
> task level **does not exist in the product yet** (ELL-607). Every task-level
> result here comes from the offline simulator and runs on synthetic fixtures.
> CI results on the PRs are real GitHub Actions runs. Nothing in this repository
> is a live Code Telemetry receipt unless the traceability table links one.

## The three-step trick

1. **Define the required checks** as exact commands at each level: the org
   baseline (`make org-lint`, `make org-unit`), the repository contract
   (`make repo-integration`), and each issue's acceptance command (`make task-…`).
2. **Capture what actually ran.** The agent's session is recorded, so you can see
   which commands ran, their outcome, and whether they ran *after the final edit*.
3. **Verify on the PR.** The `codetelemetry/validation` check passes only if every
   effective check passed after the final edit for that exact head SHA. Stale,
   failed, missing and unknown evidence are reported as such, never as green.

## Run it (offline, about a minute)

```sh
git clone https://github.com/CodeTelemetry/grader-issue-lab.git && cd grader-issue-lab
make install
make org-lint org-unit repo-integration
make labgrader-test offline-repro     # expect: 18 fixtures, 0 mismatches
```

Python 3.12+. Only pytest and ruff, both pinned. No cloud service. See
[docs/REPRODUCE.md](docs/REPRODUCE.md) for the optional live path.

## How policy combines

`effective = org ∪ repo ∪ task(issue₁) ∪ task(issue₂) …`. Levels only add. Task
checks come from a reviewed, versioned mapping, selected by the issues GitHub says
the PR closes. PR and issue text is never policy. Missing or untrusted linkage
makes the task level **unknown** (fail closed). Details and current product gaps
are in [docs/POLICY-HIERARCHY.md](docs/POLICY-HIERARCHY.md).

## The six assignments

| # | Assignment | Task check | Demonstrated outcome | Simulator fixtures |
| -- | -- | -- | -- | -- |
| 1 | Fix currency rounding | `make task-rounding` | all org/repo/task checks pass | `01-rounding-pass` |
| 2 | Make refunds idempotent | `make task-idempotency` | org lint fails; repo and task pass | `02-…fail`, `02r-…remediated` |
| 3 | Make CSV import atomic | `make task-csv-atomic` | repo integration fails; org and task pass | `03-…fail`, `03r-…remediated` |
| 4 | Restrict customer order access | `make task-authorization` | task acceptance fails; org and repo pass | `04-…fail`, `04r-…remediated` |
| 5 | Implement cursor pagination | `make task-pagination` | tests ran, then source edited and pushed: stale | `05-…stale`, `05r-…remediated` |
| 6 | Redact secrets in audit logs | `make task-redaction` | truncated output or telemetry gap: unknown | `06-…truncated`, `06-…gap`, `06r-…remediated` |

More fixtures: multiple issues in one PR (union), an unlinked PR, a PR-body
injection attempt, an unmapped issue, and a second repository (`ledger-lite`) that
reuses the organization baseline without ParcelDesk's repository checks.

## Traceability

<!-- traceability:start -->
| Issue | PR | Scenario | Scenario commit | CI at scenario commit | Remediation | Remediation result |
| -- | -- | -- | -- | -- | -- | -- |
| [#1](https://github.com/CodeTelemetry/grader-issue-lab/issues/1) | [#7](https://github.com/CodeTelemetry/grader-issue-lab/pull/7) | all pass | `scenario/rounding-pass` `7b2cfdcd644e` | [CI](https://github.com/CodeTelemetry/grader-issue-lab/actions/runs/43039788761/job/130588190361) ✅ | — | — |
| [#2](https://github.com/CodeTelemetry/grader-issue-lab/issues/2) | [#8](https://github.com/CodeTelemetry/grader-issue-lab/pull/8) | org lint fails | `scenario/idempotency-org-lint-fail` `57cc0372c706` | [CI](https://github.com/CodeTelemetry/grader-issue-lab/actions/runs/43039859322/job/130588439180) ❌ (F401) | `scenario/idempotency-remediated` `7bc998cdec4c` | CI ✅ |
| [#3](https://github.com/CodeTelemetry/grader-issue-lab/issues/3) | [#9](https://github.com/CodeTelemetry/grader-issue-lab/pull/9) | repo integration fails | `scenario/csv-atomic-repo-integration-fail` `820df4019490` | [CI](https://github.com/CodeTelemetry/grader-issue-lab/actions/runs/43039936599/job/130588699017) ❌ | `scenario/csv-atomic-remediated` `04b64a84164f` | CI ✅ |
| [#4](https://github.com/CodeTelemetry/grader-issue-lab/issues/4) | [#10](https://github.com/CodeTelemetry/grader-issue-lab/pull/10) | task acceptance fails | `scenario/authorization-task-fail` `7465dc3207db` | [CI](https://github.com/CodeTelemetry/grader-issue-lab/actions/runs/43039984783/job/130588867967) ❌ | `scenario/authorization-remediated` `dd7adf97fe79` | CI ✅ |
| [#5](https://github.com/CodeTelemetry/grader-issue-lab/issues/5) | [#11](https://github.com/CodeTelemetry/grader-issue-lab/pull/11) | stale after edit | `scenario/pagination-stale` `d807c8ba9ede` | [CI](https://github.com/CodeTelemetry/grader-issue-lab/actions/runs/43040060418/job/130589132457) ✅ (green CI, stale session) | re-run, no code change | [comment](https://github.com/CodeTelemetry/grader-issue-lab/pull/11#issuecomment-6798713245) |
| [#6](https://github.com/CodeTelemetry/grader-issue-lab/issues/6) | [#12](https://github.com/CodeTelemetry/grader-issue-lab/pull/12) | unknown evidence | `scenario/redaction-code` `c2e4da175da9` | CI ✅ | **live: not implemented** | offline fixtures only |

What each column is:

* **CI** is a real GitHub Actions run of the org/repo/task commands. It shows the
  code's state at that SHA. It doesn't show what the agent ran before pushing.
* **`codetelemetry/validation`** currently **fails on every PR** with *"Configure this
  repository's dedicated CodeTelemetry gate before enabling merges."* No gate is
  provisioned for this repository yet, so there is **no live Code Telemetry verdict
  or session receipt** in this table. That failure is correct: an unconfigured gate
  must not be green.
* **Agent sessions:** the PRs were written by a coding agent (Claude Code) working
  from these issues. The commands it ran are listed in each PR description. Those
  sessions have not been confirmed as ingested by Code Telemetry, so no session URLs
  are listed.
* **Task level:** simulated offline (ELL-607). Scenario 5's stale verdict and
  scenario 6's unknown verdict are about session evidence, so CI can't show them.

### Not yet live (blocking a "fully three-level" claim)

| Gap | Tracking |
| -- | -- |
| Task/issue-scoped checks in the product | ELL-607 |
| Org baseline published at organization scope, plus a second live repository | live step (b)1 in docs/REPRODUCE.md |
| Dedicated gate + `CODETELEMETRY_GATE_ID`; public-repo `pull_request_target` event policy | live steps (b)2–3 |
| Recorded sessions linked from each PR; live stale and unknown receipts | after the gate exists |
<!-- traceability:end -->

## Layout

```text
src/parceldesk/            app: money, refunds, csv_import, access, pagination, audit
src/labgrader/             offline org → repo → task simulator (synthetic only)
tests/unit|integration     org baseline and repository contract
tests/acceptance/          one file per task, added by that task's PR
tests/labgrader/           simulator semantics
.codetelemetry/            org + repo Grader checks (real format), gate, demo task mapping
examples/evidence/         synthetic session fixtures
examples/scenarios/        expected-results matrix
```

MIT licensed.
