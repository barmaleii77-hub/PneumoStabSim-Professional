from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from tools import validate_shaders


def _make_qsb_stub(
    base: Path,
    *,
    exit_code: int = 0,
    stdout: str = "compiled",
    stderr: str = "compilation failed",
) -> list[str]:
    script = base / "qsb_stub.py"
    script.write_text(
        f"""
import sys
from pathlib import Path

args = sys.argv[1:]

output = None
for index, value in enumerate(list(args)):
    if value == "-o" and index + 1 < len(args):
        output = Path(args[index + 1])
        break

if output is not None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"\\0")

shader_path = Path(args[-1])
if not shader_path.exists():
    shader_path.touch()

if {exit_code} != 0:
    if "{stderr}" != "":
        print("{stderr}", file=sys.stderr)
else:
    if "{stdout}" != "":
        print("{stdout}")

sys.exit({exit_code})
"""
    )
    return [sys.executable, str(script)]


def _write_shader(base: Path, relative: str, content: str) -> None:
    target = base / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_validate_shaders_success(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path)

    _write_shader(
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback.frag",
        "#version 450 core\nvoid main() {}\n",
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback_es.frag",
        "#version 300 es\nvoid main() {}\n",
    )
    _write_shader(
        shader_root, "post_effects/bloom_es.frag", "#version 300 es\nvoid main() {}\n"
    )

    _write_shader(
        shader_root, "effects/fog.vert", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_es.vert", "#version 300 es\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_fallback.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_es.frag", "#version 300 es\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_fallback_es.frag", "#version 300 es\nvoid main() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert errors == []


def test_validate_shaders_reports_missing_gles_variant(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path)

    _write_shader(
        shader_root, "effects/ssao.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/ssao_fallback.frag", "#version 450 core\nvoid main() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("missing GLES variant" in message for message in errors)


def test_validate_shaders_reports_missing_fallback_es_variant(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path)

    _write_shader(
        shader_root, "effects/dof.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_fallback.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_es.frag", "#version 300 es\nvoid main() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("missing fallback ES variant" in message for message in errors)


def test_validate_shaders_reports_version_mismatch(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path)

    _write_shader(
        shader_root, "effects/dof.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_fallback.frag", "#version 450 core\nvoid main() {}\n"
    )
    _write_shader(
        shader_root, "post_effects/dof_es.frag", "#version 100 es\nvoid main() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("expected '#version 300 es'" in message for message in errors)


def test_validate_shaders_propagates_qsb_failure(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path, exit_code=2, stderr="fatal: syntax error")

    _write_shader(
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid main() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("qsb failed" in message for message in errors)
    assert any("fatal: syntax error" in message for message in errors)
