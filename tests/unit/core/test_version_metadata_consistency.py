from __future__ import annotations

from pathlib import Path
import re
import json

PYPROJECT = Path("pyproject.toml")
SETTINGS = Path("config/app_settings.json")


def _extract_version_pyproject(text: str) -> str | None:
    m = re.search(r"^version\s*=\s*\"([^\"]+)\"", text, re.MULTILINE)
    return m.group(1) if m else None


def test_metadata_version_matches_pyproject() -> None:
    assert PYPROJECT.exists(), "pyproject.toml отсутствует"
    assert SETTINGS.exists(), "config/app_settings.json отсутствует"

    py_text = PYPROJECT.read_text(encoding="utf-8")
    version_py = _extract_version_pyproject(py_text)
    assert version_py is not None, "Не найдена версия в pyproject.toml"

    settings_payload = json.loads(SETTINGS.read_text(encoding="utf-8"))
    meta = settings_payload.get("metadata", {})
    version_meta = meta.get("version")
    assert version_meta == version_py, (
        f"metadata.version {version_meta} != pyproject {version_py}"
    )
