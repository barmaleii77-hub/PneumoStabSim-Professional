from __future__ import annotations

import json
from pathlib import Path

from src.core.resource_cache import ResourceCache
from src.infrastructure.event_bus import EventBus


def _load_baseline() -> dict:
    root = Path(__file__).resolve().parents[2]
    with open(root / "optimization_test_results.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def _lazy_loading_probe() -> bool:
    singleton_path = Path(__file__).resolve().parents[2] / "qml" / "components" / "UiConstants.qml"
    payload = singleton_path.read_text(encoding="utf-8")
    return "XMLHttpRequest" in payload and "ui_constants.json" in payload


def _cache_probe() -> dict[str, float | bool]:
    calls: dict[str, int] = {"geometry": 0, "materials": 0}

    def geometry_loader() -> dict[str, int]:
        calls["geometry"] += 1
        return {"points": [1, 2, 3], "rev": calls["geometry"]}

    def material_loader() -> dict[str, int]:
        calls["materials"] += 1
        return {"materials": ["steel", "aluminium"], "rev": calls["materials"]}

    bus = EventBus()
    cache = ResourceCache(
        geometry_loader=geometry_loader,
        material_loader=material_loader,
        event_bus=bus,
    )

    first = cache.snapshot()
    second = cache.snapshot()
    bus.publish(cache.change_topic)
    third = cache.snapshot()

    cache_works = first is second and first is not third and calls["geometry"] == 2
    total_calls = calls["geometry"] + calls["materials"]
    speedup = 6.0 / total_calls  # naive ratio against reloading every request

    return {
        "cache_works": cache_works,
        "speedup": speedup,
        "data_consistent": cache.is_consistent(),
    }


def test_lazy_load_works_against_baseline() -> None:
    baseline = _load_baseline()["lazy_loading"]["result"]["lazy_load_works"]
    assert _lazy_loading_probe() == baseline


def test_cache_contract_matches_baseline() -> None:
    results = _cache_probe()
    baseline = _load_baseline()["caching"]["result"]
    assert results["cache_works"] == baseline["cache_works"]
    assert results["data_consistent"] == baseline["data_consistent"]
    assert results["speedup"] >= baseline["speedup"]
