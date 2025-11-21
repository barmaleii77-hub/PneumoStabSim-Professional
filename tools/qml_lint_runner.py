#!/usr/bin/env python3
"""Cross-platform QML lint runner (enhanced summary)."""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path
DEFAULT_TARGETS_FILE = "qmllint_targets.txt"

def _candidate_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    c: list[Path] = []
    if os.name == "nt":
        c += [root/".venv"/"Scripts"/"pyside6-qmllint.exe", root/".venv"/"Scripts"/"qmllint.exe"]
    else:
        c += [root/".venv"/"bin"/"pyside6-qmllint", root/".venv"/"bin"/"qmllint"]
    return c

def _which(name: str) -> str | None:
    from shutil import which
    return which(name)

def _resolve_linter() -> str | None:
    override = os.environ.get("QML_LINTER")
    if override:
        return override
    for n in ("pyside6-qmllint", "qmllint"):
        if _which(n):
            return n
    for p in _candidate_paths():
        if p.exists():
            return str(p)
    return None

def _collect_targets(path: Path) -> list[Path]:
    if not path.exists():
        return []
    out: list[Path] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = line.strip()
        if not raw or raw.startswith('#'): continue
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.qml")))
        else:
            out.append(p)
    seen: set[Path] = set(); uniq: list[Path] = []
    for e in out:
        rp = e.resolve() if e.exists() else e
        if rp not in seen:
            seen.add(rp); uniq.append(e)
    return uniq

def run_lint(linter: str, targets: list[Path]) -> int:
    if not targets:
        print("[qml-lint] No targets; skipping."); return 0
    failures: list[str] = []; errors: list[str] = []
    for t in targets:
        if not t.exists():
            print(f"[qml-lint] MISSING {t}"); continue
        cmd = [linter, str(t)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            print(f"[qml-lint] OK   {t}")
        else:
            failures.append(str(t))
            print(f"[qml-lint] FAIL {t} (rc={proc.returncode})")
            if proc.stdout: print(proc.stdout.rstrip())
            if proc.stderr: print(proc.stderr.rstrip())
    if failures:
        print(f"[qml-lint] Summary: {len(failures)} file(s) failed lint")
        for f in failures[:20]:
            print(f"  - {f}")
        return 2
    return 0

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Cross-platform qmllint runner")
    ap.add_argument("--targets-file", default=DEFAULT_TARGETS_FILE)
    return ap.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    linter = _resolve_linter()
    if not linter:
        print("[qml-lint] ERROR: qmllint not found. Set QML_LINTER or install PySide6 tools.")
        return 1
    targets = _collect_targets(Path(a.targets_file))
    return run_lint(linter, targets)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
