# 3D Scene Render/Performance Checks

## Summary
- Validated the new `qml/ThreeDScene.qml` contract for primitives, lighting, batching, and input telemetry.
- Benchmarked Python-side 3D payload assembly to ensure the bridge can feed the scene without regressions.
- Captured known gating issue from the global `make check` preflight (materials schema gaps in existing settings).

## Commands
- `uv run --locked -- pytest tests/unit/ui/test_three_d_bridge.py tests/ui/test_three_d_scene_contract.py` (pass)
- `uv run --locked -- python - <<'PY' ... qml_bridge.initial_three_d_payload()` (payload micro-benchmark)
- `make check` (failed on existing settings schema validation; see logs)

## Metrics
- Average payload generation time: ~2.76e-05 s per call (5k iterations).

## Notes
- The settings schema validation failures stem from missing `specular`, `specular_tint`, `transmission`, and `ior` fields in existing materials entries; they predate the current change and will need a dedicated fix before the full gate is green.
