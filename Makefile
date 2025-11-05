SHELL := /bin/bash
PYTHON ?= python3
UV ?= uv
UV_PROJECT_DIR ?= .
UV_LOCKFILE ?= uv.lock
UV_SYNC_ARGS ?= --frozen
UV_RUN_ARGS ?= --locked
QML_LINT_PATHS ?= src assets
QML_LINT_TARGETS_FILE ?= qmllint_targets.txt
PYTHON_LINT_PATHS ?= src tests tools
MYPY_TARGETS ?= $(shell cat mypy_targets.txt 2>/dev/null)
PYTEST_TARGETS_FILE ?= pytest_targets.txt
LOG_DIR ?= logs
PYTEST_FLAGS ?= -vv --color=yes --maxfail=1
SMOKE_TARGET ?= tests/smoke
INTEGRATION_TARGET ?= tests/integration/test_main_window_qml.py

.PHONY: format lint typecheck qml-lint test-local validate-shaders check-shaders check verify smoke integration \
localization-check \
autonomous-check autonomous-check-trace trace-launch sanitize cipilot-env \
install-qt-runtime qt-env-check telemetry-etl profile-phase3 profile-render profile-validate package-all


.PHONY: qml-lint qmllint
qml-lint qmllint:
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

.PHONY: uv-sync uv-sync-locked uv-run

uv-sync:
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
		exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && $(UV) sync $(UV_SYNC_ARGS)

uv-sync-locked:
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
		exit 1; \
	fi
	@if [ ! -f "$(UV_PROJECT_DIR)/$(UV_LOCKFILE)" ]; then \
		echo "Error: Lockfile '$(UV_LOCKFILE)' was not found in $(UV_PROJECT_DIR). Run 'uv lock' first." >&2; \
		exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && $(UV) sync --locked --frozen

uv-run:
	@if [ -z "$(CMD)" ]; then \
		echo "Error: CMD parameter is required. Example: make uv-run CMD=\"pytest\"" >&2; \
		exit 2; \
	fi
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "Error: '$(UV)' is not installed. Run 'python scripts/bootstrap_uv.py' first." >&2; \
		exit 1; \
	fi
	cd $(UV_PROJECT_DIR) && PYTEST_DISABLE_PLUGIN_AUTOLOAD=$${PYTEST_DISABLE_PLUGIN_AUTOLOAD-1} $(UV) run $(UV_RUN_ARGS) -- $(CMD)

package-all:
	$(MAKE) uv-run CMD="python -m tools.packaging.build_packages"

install-qt-runtime:
	@echo "Installing Qt runtime system libraries (libgl1, libxkbcommon0, libegl1)"
	@bash tools/install_qt_runtime.sh

format:
	$(PYTHON) -m ruff format $(PYTHON_LINT_PATHS)

lint:
	$(PYTHON) -m tools.ci_tasks lint

typecheck:
	$(PYTHON) -m tools.ci_tasks typecheck


.PHONY: test-local
test-local::
	$(PYTHON) -m tools.ci_tasks test

validate-shaders:
	$(PYTHON) tools/validate_shaders.py

check-shaders: validate-shaders

shader-artifacts:
	$(PYTHON) tools/validate_shaders.py --emit-qsb

validate-hdr-orientation:
	$(PYTHON) tools/graphics/validate_hdr_orientation.py

check: lint typecheck qml-lint test-local check-shaders validate-hdr-orientation localization-check qt-env-check

verify: lint typecheck qml-lint test-local smoke integration

localization-check:
	$(PYTHON) tools/update_translations.py --check

qt-env-check:
	@$(SHELL) -lc '\
		if [ -f "$(UV_PROJECT_DIR)/activate_environment.sh" ]; then \
			source "$(UV_PROJECT_DIR)/activate_environment.sh" >/dev/null 2>&1; \
		fi; \
		if command -v "$(UV)" >/dev/null 2>&1; then \
			cd "$(UV_PROJECT_DIR)" && "$(UV)" run $(UV_RUN_ARGS) -- python tools/environment/verify_qt_setup.py --report-dir reports/environment; \
		else \
			$(PYTHON) tools/environment/verify_qt_setup.py --report-dir reports/environment; \
		fi \
	'

.PHONY: telemetry-etl
telemetry-etl:
	$(PYTHON) tools/telemetry_exporter.py export --format json --output reports/analytics/telemetry_events.json
	$(PYTHON) tools/telemetry_exporter.py aggregate --output reports/analytics/telemetry_aggregates.json

.PHONY: profile-phase3
profile-phase3:
	$(PYTHON) tools/performance_monitor.py --scenario phase3 --output reports/performance/ui_phase3_profile.json --html-output reports/performance/ui_phase3_profile.html

.PHONY: profile-render
profile-render: profile-phase3

.PHONY: profile-validate
profile-validate:
	$(PYTHON) tools/performance_gate.py reports/performance/ui_phase3_profile.json reports/performance/baselines/ui_phase3_baseline.json --summary-output reports/performance/ui_phase3_summary.json

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

# -----------------------------------------------------------------------------
# Containerised workflow helpers
# -----------------------------------------------------------------------------

CONTAINER_IMAGE ?= pneumo-dev:qt610
CONTAINER_WORKDIR ?= /workdir

.PHONY: container-build container-shell container-test container-test-opengl \
        container-test-vulkan container-verify-all container-analyze-logs

container-build:
	docker build -t $(CONTAINER_IMAGE) .

container-shell:
	docker run --rm -it -v $(CURDIR):$(CONTAINER_WORKDIR) -w $(CONTAINER_WORKDIR) $(CONTAINER_IMAGE) bash

container-test: container-build
	docker run --rm -t -v $(CURDIR):$(CONTAINER_WORKDIR) -w $(CONTAINER_WORKDIR) $(CONTAINER_IMAGE) /usr/local/bin/run_all.sh

container-test-opengl: container-build
	docker run --rm -t -v $(CURDIR):$(CONTAINER_WORKDIR) -w $(CONTAINER_WORKDIR) $(CONTAINER_IMAGE) /usr/local/bin/xvfb_wrapper.sh env QSG_RHI_BACKEND=opengl python app.py --test-mode

container-test-vulkan: container-build
	docker run --rm -t -v $(CURDIR):$(CONTAINER_WORKDIR) -w $(CONTAINER_WORKDIR) $(CONTAINER_IMAGE) /usr/local/bin/xvfb_wrapper.sh env QSG_RHI_BACKEND=vulkan python app.py --test-mode || true

container-verify-all: container-build container-test

container-analyze-logs: container-build
	docker run --rm -t -v $(CURDIR):$(CONTAINER_WORKDIR) -w $(CONTAINER_WORKDIR) $(CONTAINER_IMAGE) python /usr/local/bin/collect_logs.py

.PHONY: build shell test test-opengl test-vulkan verify-all analyze-logs
build: container-build

shell: container-shell

test: container-test

test-opengl: container-test-opengl

test-vulkan: container-test-vulkan

verify-all: container-verify-all

analyze-logs: container-analyze-logs

