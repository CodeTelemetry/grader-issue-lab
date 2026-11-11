# Policy hierarchy: organization → repository → task

## The rule

```
effective checks = organization ∪ repository(repositoryId) ∪ ⋃ task(issue) for each linked issue
```

* **Organization** checks (`.codetelemetry/org/grader.json`) apply to every repository.
  They carry no `repositoryId`.
* **Repository** checks (`.codetelemetry/grader.json`) carry the recorded
  `repositoryId` (`grader-issue-lab`) and apply only to that repository.
* **Task** checks come only from the approved, versioned mapping
  (`.codetelemetry/demo/task-policy.json`). They're selected by the issues that GitHub
  reports the PR closes.

Levels only add. No level can disable, exempt or weaken a check from a broader
level. The loader rejects `disable`, `override`, `exempt`, `skip`, `enabled: false`
and any unknown key on a mapping entry. If a check id appears at two levels it
keeps both origins. If the two definitions differ, the policy is rejected rather
than one of them winning.

## Trust boundaries

| Input | Trusted for policy? | Why |
| -- | -- | -- |
| `.codetelemetry/**` on the default branch | yes | reviewed (CODEOWNERS), versioned |
| GitHub closing-issue references for the PR | yes, for *which* issues | read by the service from GitHub, not by the agent |
| PR body, issue body, comments | **no** | anyone who can open a PR can write them |
| Agent output / session text | **no** | the agent is the thing being graded |

The issue only names which mapping entry applies. The mapping decides the checks.
An issue that can't be mapped makes the task level **unknown** while linkage is
required (`requireIssueLinkage: true`). So do missing linkage and linkage from an
untrusted source. Unknown blocks a merge; it is never treated as a pass, and it is
never quietly reduced to just the org and repo checks.

## Verdicts per check (as of the final push)

| Verdict | Meaning |
| -- | -- |
| pass | latest matching run after the final edit succeeded |
| fail | that run failed |
| stale | it only ran before the final edit |
| missing | it never ran, and the evidence is complete enough to say so |
| unknown | deciding output truncated, or a telemetry gap means neither a run nor its absence is provable |

## What exists in Code Telemetry today (2026-11-11)

| Level | Product status | In this lab |
| -- | -- | -- |
| Organization | Org-scope Grader configuration (ELL-556, ELL-559; Ready for Acceptance) | real `grader.json` format, **not yet published live from this lab** |
| Repository | Check-level `repositoryId` is supported | real `grader.json`, **not yet published live from this lab** |
| Task / issue | **Not implemented.** No check field selects by issue (backend `agent/grader.ts` allowed fields). `applicabilityRule` matches observed activity, which is agent-controlled, so it must not stand in for it. `seed_grader_config` discovers build tasks, not issues. | **demo schema**, offline simulator only. Product work tracked in ELL-607. |

This lab does **not** fake the task level by publishing every task check globally,
or by editing the published policy for each PR. Until ELL-607 ships, the task-level
outcomes here come from the offline simulator and are labelled that way.

### Where task selection should fit (proposal in ELL-607)

The gate evaluator already pins the evaluation to `headSha` and `policyVersion`
(`integrations/github/gateEvaluator.ts`). The smallest safe extension:

1. Store the task mapping as versioned Grader config at org or repo scope, managed
   through the MCP like `grader.json`.
2. When the gate evaluates a PR head, fetch `closingIssuesReferences` from GitHub for
   that PR and record the result in the snapshot.
3. Union the mapped checks into the effective policy, recording origin per check. If
   linkage is required and missing, fail closed.
