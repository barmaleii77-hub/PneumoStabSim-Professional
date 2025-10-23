SHELL := /bin/bash
PYTHON ?= python3
QML_LINT_PATHS ?= src assets
QML_LINT_TARGETS_FILE ?= qmllint_targets.txt
PYTHON_LINT_PATHS ?= src tests tools
MYPY_TARGETS ?= $(shell cat mypy_targets.txt 2>/dev/null)
PYTEST_TARGETS_FILE ?= pytest_targets.txt
LOG_DIR ?= logs
PYTEST_FLAGS ?= -vv --color=yes --maxfail=1
SMOKE_TARGET ?= tests/smoke
INTEGRATION_TARGET ?= tests/integration/test_main_window_qml.py

.PHONY: format lint typecheck qml-lint test verify smoke integration

format:
	$(PYTHON) -m ruff format $(PYTHON_LINT_PATHS)

lint:
	$(PYTHON) -m ruff check $(PYTHON_LINT_PATHS)

typecheck:
	@targets="$(MYPY_TARGETS)"; \
	if [ -z "$$targets" ]; then \
	  echo "No mypy targets specified; skipping type checking."; \
	else \
	  $(PYTHON) -m mypy --config-file mypy.ini $$targets; \
	fi

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
	@if [ -f "$(PYTEST_TARGETS_FILE)" ]; then \
	  mapfile -t pytest_targets < "$(PYTEST_TARGETS_FILE)"; \
	else \
	  pytest_targets=(tests); \
	fi; \
	if [ $${#pytest_targets[@]} -eq 0 ]; then \
	  echo "No pytest targets specified; skipping."; \
	else \
	  $(PYTHON) -m pytest "$${pytest_targets[@]}"; \
	fi

verify: lint typecheck qml-lint test smoke integration
