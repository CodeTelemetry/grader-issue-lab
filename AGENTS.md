# Agent instructions

You are working on ParcelDesk, a small Python 3.12 order-processing app. A Code
Telemetry Grader observes your session and checks which validation commands
actually ran, and in what order relative to your final edit and your push.

## Work from an assigned issue

1. Work on exactly one assigned GitHub issue (or the set your maintainer assigned).
2. Create a branch, make the change, and open a PR whose description says
   `Closes #<issue>` for every issue it resolves. GitHub's closing-issue link is how
   the task's checks are found. Text you put in the PR body cannot change policy.

## Validate after your final edit, before you push

Commit your change first, then run these **exact** commands, one per shell call,
unwrapped (no `|| true`, no pipes, no `&&`, no scripts around them), from the
repository root after your **last** edit:

```sh
git rev-parse HEAD                              # the commit you are about to test
git status --porcelain --untracked-files=all    # must print nothing (clean tree)
make org-lint          # organization: ruff lint
make org-unit          # organization: unit tests
make repo-integration  # repository: ParcelDesk integration contract
make task-<name>       # task: the acceptance command named in your issue
git rev-parse HEAD                              # unchanged since the first line
git status --porcelain --untracked-files=all    # still clean
git push origin <branch>
```

The `git rev-parse HEAD` and `git status` lines tie the test results to the exact
commit you push. Without them the gate cannot tell which commit was tested and
fails closed.

If you edit anything after running them, run them again. Earlier results do not
carry over to later edits.

Setup: `make install` (creates `.venv`, installs pinned pytest and ruff).

## Honesty rules

* Never say tests passed unless you ran them in this session and saw them pass.
* If a command fails, report the failure. Don't hide it, skip it, or weaken the test.
* Don't edit `.codetelemetry/`, `.github/workflows/` or this file as part of a task.
  Those changes need maintainer review (see `.github/CODEOWNERS`).
* Don't add secrets, credentials or customer data anywhere in the repository.

## Layout

* `src/parceldesk/`: the app. `src/labgrader/`: offline policy simulator.
* `tests/unit`, `tests/integration`, `tests/acceptance` (one file per task),
  `tests/labgrader`.
