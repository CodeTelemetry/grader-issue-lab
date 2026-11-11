# Code Telemetry policy for this repository

| File | Level | Format | Live status |
| -- | -- | -- | -- |
| `org/grader.json` | organization baseline | real Grader checks, no `repositoryId` | to publish at organization scope (docs/REPRODUCE.md (b)) |
| `grader.json` | repository (`repositoryId: grader-issue-lab`) | real Grader checks | to publish at repository scope |
| `gate.json` | PR gate scoring | real gate policy | applies once the dedicated gate exists |
| `demo/task-policy.json` | task / issue | **demo schema** | offline simulator only (ELL-607) |

Check matchers use exact fingerprints such as `v1|shell|||make|org-lint||`, the
fingerprint the Code Telemetry backend records for `make org-lint`.
