# Test and Lint Run – $(date -Iseconds)

## Commands Executed
- `make uv-run CMD="ruff check"`
- `make uv-run CMD="mypy --config-file mypy.ini @mypy_targets.txt"`
- `make uv-run CMD="coverage run -m pytest"`
- `uv run --locked -- coverage xml -o reports/coverage.xml`
- `uv run --locked -- coverage html -d reports/htmlcov`
- `uv run --locked -- coverage report -m > reports/coverage_summary.txt`
- `bash -lc 'LINTER=.venv/bin/pyside6-qmllint; mapfile -t qml_files < qmllint_targets.txt; for f in "${qml_files[@]}"; do "$LINTER" "$f"; done' > reports/qmllint.log`
- `python - <<'PY' ...` to extract HDR/reflection/physics coverage into `reports/coverage_key_modules.txt`.

## Summary of Outcomes
- **Ruff**: Completed with existing `# noqa` rule warning only; no errors.
- **Mypy**: Passed for configured targets.
- **Pytest with coverage**: Ran full suite; 18 failures and 6 errors remain (see `reports/coverage_summary.txt` for coverage totals). Key blockers include missing fixtures for physics cases, training bridge fixtures, CLI report generation, multiple configuration KeyErrors in simulation scenarios, and several QML/UI expectations.
- **Coverage reports**: Generated Cobertura XML (`reports/coverage.xml`) and HTML (`reports/htmlcov/index.html`). Overall coverage is 61% per `reports/coverage_summary.txt`.
- **Key module coverage**: HDR, reflection, and physics-related modules captured in `reports/coverage_key_modules.txt`.
- **QML lint**: Completed for all targets with numerous warnings about imports, missing properties, and unqualified accesses; details recorded in `reports/qmllint.log`.

## Notable Failures / Follow-ups
- Simulation scenario tests fail due to missing `defaults_snapshot.geometry.wheelbase` and related geometry keys.
- Physics suspension case tests lack the `physics_case_loader` fixture.
- Training preset bridge tests report missing `settings_service` fixture and signal timing timeouts.
- Several UI/QML tests (panel history, canvas preview, graphics panel hydration, shared materials fallback, main QML load, post-effects bypass, QML signals) are failing and require attention.
