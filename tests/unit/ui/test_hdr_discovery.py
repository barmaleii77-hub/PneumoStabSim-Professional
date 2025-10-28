from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = PROJECT_ROOT / "src" / "ui" / "panels" / "graphics" / "hdr_discovery.py"

_SPEC = importlib.util.spec_from_file_location("hdr_discovery_test", MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError("Unable to load hdr_discovery module for tests")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

discover_hdr_files = _MODULE.discover_hdr_files


def test_discover_hdr_files_recurses_and_normalises(tmp_path: Path) -> None:
    assets_root = tmp_path / "assets"
    hdr_dir = assets_root / "hdr"
    hdri_dir = assets_root / "hdri"
    qml_root = assets_root / "qml"
    qml_assets = qml_root / "assets"

    (hdr_dir / "nested").mkdir(parents=True)
    hdri_dir.mkdir(parents=True)
    (qml_assets / "indoor").mkdir(parents=True)

    (hdr_dir / "sunrise.hdr").write_bytes(b"")
    (hdr_dir / "nested" / "sunset.exr").write_bytes(b"")
    (hdri_dir / "forest.hdr").write_bytes(b"")
    (qml_assets / "indoor" / "studio.hdr").write_bytes(b"")

    search_dirs = [hdr_dir, hdri_dir, qml_assets]
    results = discover_hdr_files(search_dirs, qml_root=qml_root)

    assert results == [
        ("sunrise.hdr", "../hdr/sunrise.hdr"),
        ("sunset.exr", "../hdr/nested/sunset.exr"),
        ("forest.hdr", "../hdri/forest.hdr"),
        ("studio.hdr", "assets/indoor/studio.hdr"),
    ]
