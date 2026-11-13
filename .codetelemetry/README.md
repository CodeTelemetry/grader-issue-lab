# Code Telemetry policy for this repository

| File | Level | Format | Live status |
| -- | -- | -- | -- |
| `org/grader.json` | organization baseline | real Grader checks, no `repositoryId` | live: published in workspace policy v3 |
| `grader.json` | repository (`repositoryId: grader-issue-lab`) | real Grader checks | live: published in workspace policy v3 |
| `tasks.json` | task / issue (`issues: [...]`) | real Grader checks | live: published in workspace policy v3 |
| `gate.json` | PR gate scoring | real gate policy | live: this repository's dedicated gate |
| `demo/task-policy.json` | task / issue | demo schema | offline simulator only |

Check matchers use exact fingerprints such as `v1|shell|||make|org-lint||`, the
fingerprint the Code Telemetry backend records for `make org-lint`.
