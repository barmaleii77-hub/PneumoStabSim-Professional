"""Utilities for enforcing the repository-wide pytest skip policy.

This module scans Python sources for direct uses of ``pytest.skip``/``xfail``
markers and helpers.  The renovation programme forbids ad-hoc skips so we fail
fast during CI before pytest is even invoked.  When a skip is truly
unavoidable, add ``# pytest-skip-ok`` to the offending line and document the
justification nearby so reviewers can trace the rationale easily.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

_FORBIDDEN_MARKERS: tuple[tuple[str, ...], ...] = (
    ("pytest", "skip"),
    ("pytest", "xfail"),
    ("pytest", "mark", "skip"),
    ("pytest", "mark", "skipif"),
    ("pytest", "mark", "xfail"),
)
_FORBIDDEN_NAMES: frozenset[str] = frozenset({"skip", "xfail"})
_OVERRIDE_TOKEN = "pytest-skip-ok"


@dataclass(slots=True)
class SkipViolation:
    """Description of a forbidden skip marker reference."""

    path: Path
    line: int
    column: int
    marker: str
    source: str


def _iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for root in paths:
        if root.is_dir():
            yield from (p for p in root.rglob("*.py") if p.is_file())
            continue
        if root.suffix == ".py" and root.is_file():
            yield root


def _attribute_chain(node: ast.AST) -> tuple[str, ...] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return tuple(reversed(parts))
    return None


class _SkipDetector(ast.NodeVisitor):
    def __init__(self, *, module: Path, lines: Sequence[str]) -> None:
        self.module = module
        self.lines = lines
        self.pytest_aliases: set[str] = {"pytest"}
        self.forbidden_names: set[str] = set()
        self.violations: list[SkipViolation] = []

    # --- Import tracking -------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:  # noqa: D401 - standard ast hook
        for alias in node.names:
            if alias.name == "pytest":
                self.pytest_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: D401
        if node.module == "pytest":
            for alias in node.names:
                if alias.name in _FORBIDDEN_NAMES:
                    self.forbidden_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    # --- Decorator hooks -------------------------------------------------
    def _record_if_forbidden(self, node: ast.AST, marker: tuple[str, ...]) -> None:
        if marker not in _FORBIDDEN_MARKERS:
            return
        lineno = getattr(node, "lineno", 0) or 0
        col = getattr(node, "col_offset", 0) or 0
        if 1 <= lineno <= len(self.lines):
            line_text = self.lines[lineno - 1]
            if _OVERRIDE_TOKEN in line_text:
                return
        joined = ".".join(marker)
        snippet = self.lines[lineno - 1].strip() if 1 <= lineno <= len(self.lines) else ""
        self.violations.append(
            SkipViolation(
                path=self.module,
                line=lineno,
                column=col,
                marker=joined,
                source=snippet,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:  # noqa: D401
        marker = None
        if isinstance(node.func, ast.Name) and node.func.id in self.forbidden_names:
            marker = (node.func.id,)
        else:
            chain = _attribute_chain(node.func)
            if chain and chain[0] in self.pytest_aliases:
                marker = chain
        if marker is not None:
            self._record_if_forbidden(node, marker)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: D401
        chain = _attribute_chain(node)
        if chain and chain[0] in self.pytest_aliases:
            self._record_if_forbidden(node, chain)
        self.generic_visit(node)


def scan_paths(paths: Iterable[str | Path]) -> list[SkipViolation]:
    """Return all skip violations discovered under ``paths``."""

    collected: list[SkipViolation] = []
    resolved = [Path(p).resolve() for p in paths]
    for file_path in _iter_python_files(resolved):
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(text, filename=str(file_path))
        except SyntaxError:
            continue
        detector = _SkipDetector(module=file_path, lines=text.splitlines())
        detector.visit(tree)
        collected.extend(detector.violations)
    return sorted(collected, key=lambda item: (str(item.path), item.line, item.column))


def _default_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    return [repo_root / "tests"]


def _format_violation(entry: SkipViolation, *, root: Path) -> str:
    try:
        relative = entry.path.relative_to(root)
    except ValueError:
        relative = entry.path
    return (
        f"{relative}:{entry.line}:{entry.column}: forbidden pytest skip marker '{entry.marker}'\n"
        f"    {entry.source}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ensure no forbidden pytest skip/xfail markers are present. "
            "Add '# pytest-skip-ok' on the same line to acknowledge intentional skips."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=_default_paths(),
        help="Paths to scan (files or directories).",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    violations = scan_paths(args.paths)
    if not violations:
        return 0

    for violation in violations:
        print(_format_violation(violation, root=repo_root))
    print(
        "Found forbidden pytest skip markers. Remove them or mark intentional "
        "uses with '# pytest-skip-ok' and document the rationale.",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
