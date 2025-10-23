PYTHON ?= python
PYTEST ?= $(PYTHON) -m pytest
LOG_DIR ?= logs
PYTEST_FLAGS ?= -vv --color=yes --maxfail=1
SMOKE_TARGET ?= tests/smoke
INTEGRATION_TARGET ?= tests/integration/test_main_window_qml.py

.PHONY: verify smoke integration

verify: smoke integration

smoke:
	$(PYTHON) -c "from pathlib import Path; Path('$(LOG_DIR)').mkdir(parents=True, exist_ok=True)"
	$(PYTEST) -m smoke $(SMOKE_TARGET) $(PYTEST_FLAGS) --log-file=$(LOG_DIR)/pytest-smoke.log --log-file-level=INFO

integration:
	$(PYTEST) -m integration $(INTEGRATION_TARGET) $(PYTEST_FLAGS) --log-file=$(LOG_DIR)/pytest-integration.log --log-file-level=INFO
