# Reproduce

Two separate paths. Keep their results apart: (a) is a simulation, (b) is the product.

## (a) Offline: synthetic fixtures, no account, no network after install

```sh
git clone https://github.com/CodeTelemetry/grader-issue-lab.git
cd grader-issue-lab
make install            # python3 -m venv .venv + pinned pytest/ruff
make org-lint org-unit repo-integration
make labgrader-test     # semantics of the org → repo → task simulator
make offline-repro      # 18 synthetic scenarios vs examples/scenarios/expected.json
```

Expected last line of `make offline-repro`: `18 fixtures, 0 mismatches`.

To see per-check origins, verdicts and reasons for one scenario:

```sh
.venv/bin/python -m labgrader.repro --explain examples/evidence/05-pagination-stale.json
```

Every fixture is marked `"synthetic": true` and uses `headSha: "synthetic-…"`.
The simulator refuses fixtures without that flag. Its output is **not** a Code
Telemetry receipt.

### Reproduce a scenario's code state

Each lab issue has a PR. The commit at the scenario tag reproduces the CI outcome:

```sh
git fetch origin --tags
git checkout scenario/idempotency-org-lint-fail
make org-lint                # fails (deliberate lint error)
git checkout scenario/idempotency-remediated
make org-lint                # passes
```

The tags are listed in the README traceability table.

## (b) Live: instrumented Code Telemetry end-to-end (optional)

Needs a Code Telemetry workspace (organization key for the org baseline), the
`@codetelemetry/mcp` server, and a coding agent exporting telemetry.

1. Publish `.codetelemetry/org/grader.json` at **organization** scope and
   `.codetelemetry/grader.json` at repository scope through the MCP Grader
   draft → publish flow. Record the policy versions it returns.
2. Create this repository's dedicated GitHub gate through the MCP
   (`configure_github_pr_gate`), commit the workflow it returns **unchanged** (it
   embeds the gate ID, which is an identifier, not a secret; only OIDC tokens from
   trusted repositories are accepted), and require the `codetelemetry/validation` check.
   This repository's gate lives in the **CodeTelemetry Public** organization; see
   `.codetelemetry/workspace.json`.
3. Public repositories only: GitHub begins enforcing its default
   `pull_request_target` block on 2026-12-02 (brownout 2026-11-16). Add an
   *active event policy* that allows `pull_request_target` **only** for
   `.github/workflows/codetelemetry-pr-gate.yml`. Never use a blanket allow.
   If no gate job starts, check Actions → Policy insights. A blocked run is
   unavailable, not green.
4. Have an agent work an issue following `AGENTS.md` and open a PR with `Closes #N`.
   The session's telemetry must reach the workspace that owns the gate, with
   tool output included:
   * Use a current Claude Code CLI. Versions before 2.1.289 can lose tool output,
     so the gate never sees the `git rev-parse HEAD` SHA or the empty
     `git status`, and fails closed.
   * Claude Code 2.1.282 and later ignore OpenTelemetry exporter settings in a
     project's `.claude/settings.json` and `.claude/settings.local.json`. A
     session started inside this repository therefore exports with your
     user-level key, and the team-scoped gate never locates it. Pass the
     workspace settings explicitly:
     `claude --settings .claude/settings.local.json`, or export the same
     `OTEL_*` variables in the shell that launches the agent.
5. Read the verdict on the PR's `codetelemetry/validation` check and open its
   details link to the recorded session.

Task-level checks are enforced live: the gate workflow reads the PR's
GitHub closing-issue links, and the gate adds each linked issue's checks from the
published policy. Linkage that can't be read, or a linked issue with no mapped
checks, fails closed (`task_linkage_unknown`, `task_policy_unmapped`).
