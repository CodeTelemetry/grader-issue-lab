# Stable, uniquely named commands. Code Telemetry Grader checks match these
# exact invocations (for example `make org-lint`), so do not rename them or wrap
# them in other scripts when you validate a change.
PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install org-lint org-unit repo-integration acceptance \
        task-rounding task-idempotency task-csv-atomic task-authorization task-pagination task-redaction \
        labgrader-test offline-repro ci

install:
	$(PY) -m venv $(VENV)
	$(BIN)/python -m pip install -q -e '.[dev]'

# --- organization baseline (shared by every repository in the org) ---
org-lint:
	$(BIN)/ruff check src tests

org-unit:
	$(BIN)/pytest tests/unit

# --- repository checks (ParcelDesk only) ---
repo-integration:
	$(BIN)/pytest tests/integration

# --- task / issue acceptance checks (one per lab issue) ---
task-rounding:
	$(BIN)/pytest tests/acceptance/test_rounding.py
task-idempotency:
	$(BIN)/pytest tests/acceptance/test_idempotency.py
task-csv-atomic:
	$(BIN)/pytest tests/acceptance/test_csv_atomic.py
task-authorization:
	$(BIN)/pytest tests/acceptance/test_authorization.py
task-pagination:
	$(BIN)/pytest tests/acceptance/test_pagination.py
task-redaction:
	$(BIN)/pytest tests/acceptance/test_redaction.py

# Every acceptance test that exists on this branch (CI convenience, not a Grader check).
acceptance:
	@if ls tests/acceptance/test_*.py >/dev/null 2>&1; then $(BIN)/pytest tests/acceptance; else echo "no acceptance tests on this branch"; fi

# --- offline policy simulator (synthetic fixtures; not a live Code Telemetry receipt) ---
labgrader-test:
	$(BIN)/pytest tests/labgrader

offline-repro:
	$(BIN)/python -m labgrader.repro

ci: org-lint org-unit repo-integration acceptance labgrader-test offline-repro
