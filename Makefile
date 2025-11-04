SHELL := /bin/bash
PYTHON ?= python3
UV ?= uv
UV_PROJECT_DIR ?= .
QML_LINT_PATHS ?= src assets
QML_LINT_TARGETS_FILE ?= qmllint_targets.txt
PYTHON_LINT_PATHS ?= src tests tools
MYPY_TARGETS ?= $(shell cat mypy_targets.txt 2>/dev/null)
PYTEST_TARGETS_FILE ?= pytest_targets.txt
LOG_DIR ?= logs
PYTEST_FLAGS ?= -vv --color=yes --maxfail=1
SMOKE_TARGET ?= tests/smoke
INTEGRATION_TARGET ?= tests/integration/test_main_window_qml.py

.PHONY: format lint typecheck qml-lint test validate-shaders check verify smoke integration \
autonomous-check autonomous-check-trace trace-launch sanitize cipilot-env \
install-qt-runtime

.PHONY: qmllint
qmllint:
	$(MAKE) qml-lint

.PHONY: uv-sync uv-run

uv-sync:
	@if ! command -v $(UV) >/dev/null 2>&1; then \
	echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
	exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && $(UV) sync

uv-run:
	@if [ -z "$(CMD)" ]; then \
	echo "Error: CMD parameter is required. Example: make uv-run CMD=\"pytest\"" >&2; \
	exit 2; \
	fi
	@if ! command -v $(UV) >/dev/null 2>&1; then \
	echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
	exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && PYTEST_DISABLE_PLUGIN_AUTOLOAD=$${PYTEST_DISABLE_PLUGIN_AUTOLOAD-1} $(UV) run -- $(CMD)

install-qt-runtime:
	@echo "Installing Qt runtime system libraries (libgl1, libxkbcommon0, libegl1)"
	@bash tools/install_qt_runtime.sh

format:
	$(PYTHON) -m ruff format $(PYTHON_LINT_PATHS)

lint:
	$(PYTHON) -m tools.ci_tasks lint

typecheck:
	$(PYTHON) -m tools.ci_tasks typecheck

qml-lint:
	@echo "Running QML lint (qmllint)"
	@LINTER="$(QML_LINTER)"; \
	if [ -z "$$LINTER" ]; then \
	 if command -v qmllint >/dev/null 2>&1; then \
	 LINTER=qmllint; \
	 elif command -v pyside6-qmllint >/dev/null 2>&1; then \
	 LINTER=pyside6-qmllint; \
	 else \
	 echo "Error: qmllint or pyside6-qmllint is not installed. Set QML_LINTER to override." >&2; \
	 exit 1; \
	 fi; \
	fi; \
	if [ -f "$(QML_LINT_TARGETS_FILE)" ]; then \
	 mapfile -t qml_files < "$(QML_LINT_TARGETS_FILE)"; \
	else \
	 qml_files=(); \
	fi; \
	if [ $${#qml_files[@]} -eq 0 ]; then \
	 echo "No QML lint targets specified; skipping."; \
	 exit 0; \
	fi; \
	for file in "$${qml_files[@]}"; do \
	 if [ -n "$$file" ]; then \
	 if [ -d "$$file" ]; then \
	 find "$$file" -type f -name '*.qml' -print0 | while IFS= read -r -d '' nested; do "$$LINTER" "$$nested"; done; \
	 else \
	 "$$LINTER" "$$file"; \
	 fi; \
	 fi; \
	done

test:
	$(PYTHON) -m tools.ci_tasks test

validate-shaders:
	$(PYTHON) tools/validate_shaders.py

validate-hdr-orientation:
	$(PYTHON) tools/graphics/validate_hdr_orientation.py

check: lint typecheck qml-lint test validate-shaders validate-hdr-orientation

verify: lint typecheck qml-lint test smoke integration

autonomous-check:
	$(PYTHON) -m tools.autonomous_check

autonomous-check-trace:
	$(PYTHON) -m tools.autonomous_check --launch-trace

trace-launch:
	$(PYTHON) -m tools.trace_launch

sanitize:
	$(PYTHON) -m tools.project_sanitize

cipilot-env:
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
		exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && $(UV) sync
	cd $(UV_PROJECT_DIR) && $(UV) run -- python -m tools.cipilot_environment --skip-uv-sync --probe-mode=python

