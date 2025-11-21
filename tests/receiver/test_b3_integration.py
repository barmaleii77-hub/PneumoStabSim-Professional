"""B3 Receiver Integration Test

Generates detailed log b3_integration_test.log and summary markdown under reports/receiver.

Test logic:
 1. Load Receiver.qml standalone via QQmlEngine.
 2. Inject synthetic flowData + receiverState payload with pressure range and line pressures.
 3. Validate reactive properties.
 4. Record per-line pressure ratios.

Can be invoked via: pytest -q tests/receiver/test_b3_integration.py
Or programmatically: python tests/receiver/test_b3_integration.py --standalone
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

LOG_PATH = Path("b3_integration_test.log")
REPORT_DIR = Path("reports/receiver")
SUMMARY_MD = REPORT_DIR / "B3_test_results.md"

PAYLOAD = {
    "flowData": {
        "lines": {
            "a1": {"pressure": 110_000.0},
            "b1": {"pressure": 95_000.0},
            "a2": {"pressure": 123_000.0},
            "b2": {"pressure": 88_000.0},
        }
    },
    "receiverState": {
        "pressures": {
            "a1": 110_000.0,
            "b1": 95_000.0,
            "a2": 123_000.0,
            "b2": 88_000.0,
        }
    },
}

DEFAULT_KEYS = ["a1", "b1", "a2", "b2"]


class _TestLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lines: list[str] = []

    def write(self, line: str) -> None:
        self._lines.append(line.rstrip())

    def flush(self) -> None:
        self.path.write_text("\n".join(self._lines) + "\n", encoding="utf-8")


def _load_receiver(engine: QQmlEngine) -> tuple[QQmlComponent, QObject]:
    """Load Receiver.qml returning (component, root_obj) to keep component alive.

    Если держать только созданный QObject, сборщик мусора может удалить компонент
    и объект потеряет backend, вызывая RuntimeError.
    """
    qml_path = Path("assets/qml/PneumoStabSim/scene/Receiver.qml").resolve()
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(qml_path)))
    if component.isError():  # pragma: no cover - диагностический вывод
        errors = "; ".join(e.toString() for e in component.errors())
        raise RuntimeError(f"QML load errors: {errors}")
    obj = component.create()
    if not isinstance(obj, QObject):
        raise TypeError("Receiver root is not a QObject")
    return component, obj


def _apply_payload(receiver: QObject) -> None:
    receiver.setProperty("flowData", PAYLOAD["flowData"])
    receiver.setProperty("receiverState", PAYLOAD["receiverState"])


def _extract_keys(receiver: QObject) -> list[str]:
    raw = receiver.property("lineKeys")
    if hasattr(raw, "toVariant"):
        try:
            raw = raw.toVariant()
        except Exception:
            raw = []
    if isinstance(raw, (list, tuple)):
        return list(raw) or DEFAULT_KEYS
    return DEFAULT_KEYS


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_b3_receiver_integration(qapp) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    logger = _TestLogger(LOG_PATH)
    logger.write(f"START B3 INTEGRATION TEST {datetime.utcnow().isoformat()}Z")

    engine = QQmlEngine()
    component, receiver = _load_receiver(engine)
    logger.write("Loaded Receiver.qml successfully (component retained)")

    _apply_payload(receiver)
    qapp.processEvents()

    has_range = bool(receiver.property("hasPressureRange"))
    has_flow = bool(receiver.property("hasFlowData"))
    pressure_min = float(receiver.property("pressureMin"))
    pressure_max = float(receiver.property("pressureMax"))

    logger.write(
        f"hasPressureRange={has_range} pressureMin={pressure_min} pressureMax={pressure_max}"
    )

    line_keys = _extract_keys(receiver)
    ratio_map: dict[str, float] = {}
    pressures = PAYLOAD["receiverState"]["pressures"]
    span = pressure_max - pressure_min if pressure_max > pressure_min else pressure_max
    for key in line_keys:
        val = pressures.get(key, 0.0)
        ratio = (val - pressure_min) / span if span > 0 else 0.0
        ratio = max(0.0, min(1.0, ratio))
        ratio_map[key] = ratio
        logger.write(f"ratio[{key}]={ratio:.4f}")

    assert has_range, "Pressure range not detected"
    assert has_flow, "Flow data not detected"
    assert pressure_max > pressure_min >= 0, "Invalid pressure bounds"
    assert any(r > 0.5 for r in ratio_map.values()), "No high pressure sample present"

    base = float(receiver.property("sphereBaseRadiusM"))
    max_r = float(receiver.property("sphereMaxRadiusM"))
    assert max_r > base > 0

    emissive_span = float(receiver.property("sphereEmissiveSpan"))
    assert emissive_span > 0
    logger.write(f"emissiveSpan={emissive_span}")

    logger.write("STATUS=PASSED")
    logger.flush()

    summary = [
        "# B-3 Test Results",
        "",
        f"**Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "**Result**: ✅ PASSED",
        "",
        "Key Metrics:",
        f"- Pressure Range: {pressure_min:.1f} → {pressure_max:.1f}",
        f"- High Pressure Samples: {sum(r > 0.5 for r in ratio_map.values())}",
        f"- Emissive Span: {emissive_span}",
        f"- Line Ratios: {', '.join(f'{k}:{v:.2f}' for k, v in ratio_map.items())}",
        "",
        f"See `{LOG_PATH.name}` for detailed logs.",
    ]
    SUMMARY_MD.write_text("\n".join(summary) + "\n", encoding="utf-8")


def generate_b3_artifacts() -> int:
    """Standalone artifact generator used when pytest cannot launch."""
    from PySide6 import QtWidgets

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    engine = QQmlEngine()
    try:
        component, receiver = _load_receiver(engine)
        _apply_payload(receiver)
        app.processEvents()
        has_range = bool(receiver.property("hasPressureRange"))
        pressure_min = float(receiver.property("pressureMin"))
        pressure_max = float(receiver.property("pressureMax"))
        line_keys = _extract_keys(receiver)
        pressures = PAYLOAD["receiverState"]["pressures"]
        span = (
            pressure_max - pressure_min if pressure_max > pressure_min else pressure_max
        )
        ratio_map: dict[str, float] = {}
        for key in line_keys:
            val = pressures.get(key, 0.0)
            ratio = (val - pressure_min) / span if span > 0 else 0.0
            ratio = max(0.0, min(1.0, ratio))
            ratio_map[key] = ratio
        status = (
            "✅ PASSED"
            if (
                has_range
                and pressure_max > pressure_min
                and any(r > 0.5 for r in ratio_map.values())
            )
            else "❌ FAILED"
        )
        lines = [
            f"STANDALONE B3 {datetime.utcnow().isoformat()}Z",
            f"hasRange={has_range} min={pressure_min} max={pressure_max}",
            *(f"ratio[{k}]={v:.4f}" for k, v in ratio_map.items()),
            f"STATUS={status}",
        ]
        LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        summary = [
            "# B-3 Test Results",
            "",
            f"**Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Result**: {status}",
            "",
            "Key Metrics:",
            f"- Pressure Range: {pressure_min:.1f} → {pressure_max:.1f}",
            f"- High Pressure Samples: {sum(r > 0.5 for r in ratio_map.values())}",
            f"- Line Ratios: {', '.join(f'{k}:{v:.2f}' for k, v in ratio_map.items())}",
            "",
            f"See `{LOG_PATH.name}` for detailed logs.",
        ]
        SUMMARY_MD.write_text("\n".join(summary) + "\n", encoding="utf-8")
        return 0 if status.startswith("✅") else 2
    finally:
        app.quit()


if __name__ == "__main__":
    raise SystemExit(generate_b3_artifacts())
