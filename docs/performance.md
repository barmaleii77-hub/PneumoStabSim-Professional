# Performance Profiling Playbook

This guide documents the standard pipeline for recording, interpreting, and
regressing Qt Quick performance metrics in PneumoStabSim Professional. All
artifacts live under `reports/performance/` and are produced with the helper
scripts introduced in Phase 3.

## 1. Toolchain Overview

The profiling workflow relies on the following components:

- `tools/performance_monitor.py` – samples process CPU, memory, frame timing,
  and optional GPU metrics while exporting both JSON and HTML reports.
- `tools/performance_gate.py` – compares freshly captured metrics with the
  Phase 3 baseline envelope and exits with a non-zero status if limits are
  exceeded.
- Qt Quick profiler overlay configuration from `src/diagnostics/profiler.py`,
  which is embedded in the exported artifacts.

All scripts are pure Python and run inside the standard project environment. If
NVIDIA GPUs are detected with NVML support (`pynvml`), additional GPU
utilisation and memory metrics are included automatically.

## 2. Capturing a Profiling Run

1. Ensure dependencies are installed (`pip install -e .[dev]` or
   `make uv-sync`).
2. Run the canned Phase 3 scenario:

   ```bash
   make profile-render
   ```

   This command launches `tools/performance_monitor.py --scenario phase3` and
   writes two primary artifacts:

   - `reports/performance/ui_phase3_profile.json`
   - `reports/performance/ui_phase3_profile.html`

   The HTML version provides a quick visual summary while embedding the raw
   JSON payload for auditability.

3. (Optional) Generate additional scenarios by invoking
   `python tools/performance_monitor.py` directly and adjusting `--duration`,
   `--interval`, or output paths. The helper will mirror the JSON file with an
   HTML companion automatically.

## 3. Metric Reference

The exported averages include the following keys:

- `avg_cpu_percent`, `avg_memory_percent`, `avg_memory_mb` – sampled via
  `psutil` for the monitored process.
- `avg_cpu_time_user`, `avg_cpu_time_system`, `avg_cpu_time_total` – cumulative
  CPU seconds spent in user and kernel mode during the sampling window.
- `avg_fps`, `avg_frame_time_ms` – rolling FPS and frame latency derived from
  the internal frame recorder.
- `avg_gpu_utilization_percent`, `avg_gpu_memory_used_mb` – optional metrics
  collected through NVML when GPUs are available; marked as optional in the
  gate to avoid false positives on CPU-only hosts.

If a metric is unavailable (for example GPU utilisation on CI without discrete
hardware), it is recorded as `null` in JSON and the gate treats it as optional.

## 4. Regression Gates and Baselines

Baseline limits for the Phase 3 UI render path live in
`reports/performance/baselines/ui_phase3_baseline.json`. Each entry defines
per-metric constraints:

- `reference` and `tolerance_percent` establish an acceptable band around the
  golden measurement.
- `max` / `min` enforce hard ceilings or floors.
- `optional: true` marks metrics that are informative but should not break the
  build when missing.

After generating a report, run:

```bash
make profile-validate
```

This executes `tools/performance_gate.py`, compares the captured averages with
baseline thresholds, and writes a machine-readable summary to
`reports/performance/ui_phase3_summary.json`. The CI workflow (`.github/workflows/ci.yml`)
invokes the same target so pull requests automatically fail when a metric
breaches the envelope.

## 5. Interpreting the HTML Summary

The HTML report organises the data into three panels:

1. **Scenario metadata** – captured timestamps, overlay state, and capability
   flags (`psutil`/GPU availability).
2. **Aggregated metrics** – formatted averages for quick scanning; anomalous
   values should be cross-checked against the JSON for precise numbers.
3. **Raw payload** – the exact JSON emitted by the profiler for archival or
   scripting.

Use the HTML report for at-a-glance validation during manual testing, and defer
to the JSON payload when plotting trends or feeding dashboards.

## 6. Troubleshooting

- **Missing GPU metrics:** Install `pynvml` (or ensure the NVIDIA drivers expose
  NVML). Metrics remain optional, so CI will not fail solely because they are
  absent.
- **psutil warnings:** Install `psutil` to unlock CPU/memory sampling. Without
  it, only the profiler overlay metadata is exported.
- **CI failures:** Inspect `reports/performance/ui_phase3_summary.json` in the
  uploaded artifact for detailed failure reasons, then compare the recorded
  averages against the baseline thresholds.

Document any new scenarios or threshold updates in this file alongside the
baseline JSON change so the history remains traceable.
