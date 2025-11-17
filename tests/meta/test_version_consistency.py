from __future__ import annotations

import ast
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def _read_version_from_pyproject() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def _read_version_assignment(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        return node.value.value
    raise AssertionError(f"__version__ not found in {path}")


def _assert_version_in_file(expected: str, path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    assert expected in content, f"{path} is missing version {expected}"


def test_version_is_consistent_across_metadata_and_docs() -> None:
    version = _read_version_from_pyproject()

    python_modules = [
        ROOT / "src/ui/main_window_pkg/__init__.py",
        ROOT / "src/road/__init__.py",
    ]
    for module in python_modules:
        assert _read_version_assignment(module) == version

    doc_paths = [
        ROOT / "README.md",
        ROOT / "docs/README.md",
        ROOT / "docs/SETTINGS_ARCHITECTURE.md",
        ROOT / "docs/LOG_ANALYSIS_GUIDE.md",
        ROOT / "docs/LOG_ANALYSIS_CHEATSHEET.md",
    ]
    for doc in doc_paths:
        _assert_version_in_file(version, doc)
