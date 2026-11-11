# DEMO SCHEMA, not read by Code Telemetry

`task-policy.json` uses `codetelemetry-lab/task-policy@demo`, a format proposed for
this lab. Code Telemetry has no task-scope API yet (tracked as ELL-607). Only the
offline simulator in `src/labgrader/` reads this file. Don't publish it as Grader
configuration, and don't copy its task checks into the organization or repository
policy to imitate task scope.
