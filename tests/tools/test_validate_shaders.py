from __future__ import annotations

import json
import shlex
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
    capture_args: Path | None = None,
    version_exit_code: int | None = None,
    version_stdout: str = "Qt Shader Baker 6.10",
    version_stderr: str = "",
) -> list[str]:
    script = base / "qsb_stub.py"
    capture_literal = repr(str(capture_args)) if capture_args is not None else "None"
    if version_exit_code is None:
        version_exit_literal = exit_code
        if exit_code != 0 and version_stderr == "":
            version_stderr = stderr
    else:
        version_exit_literal = version_exit_code
    script.write_text(
        f"""
import json
import sys
from pathlib import Path

args = sys.argv[1:]

capture_path = {capture_literal}
if capture_path is not None:
    capture = Path(capture_path)
    capture.parent.mkdir(parents=True, exist_ok=True)
    with capture.open("a", encoding="utf-8") as handle:
        json.dump(args, handle)
        handle.write("\\n")

if args == ["--version"]:
    if {version_exit_literal} != 0:
        if "{version_stderr}" != "":
            print("{version_stderr}", file=sys.stderr)
    else:
        if "{version_stdout}" != "":
            print("{version_stdout}")
    sys.exit({version_exit_literal})

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
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback.frag",
        "#version 450 core\nvoid qt_customMain() {}\n",
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback_es.frag",
        "#version 300 es\nvoid qt_customMain() {}\n",
    )
    _write_shader(
        shader_root, "effects/bloom_es.frag", "#version 300 es\nvoid qt_customMain() {}\n"
    )

    _write_shader(
        shader_root, "effects/fog.vert", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_es.vert", "#version 300 es\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_fallback.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_es.frag", "#version 300 es\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/fog_fallback_es.frag", "#version 300 es\nvoid qt_customMain() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert errors == []


def test_validate_shaders_invokes_qsb_profiles_and_logs(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    capture = tmp_path / "qsb_invocations.jsonl"
    qsb_cmd = _make_qsb_stub(tmp_path, capture_args=capture)

    _write_shader(
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback.frag",
        "#version 450 core\nvoid qt_customMain() {}\n",
    )
    _write_shader(
        shader_root,
        "effects/bloom_fallback_es.frag",
        "#version 300 es\nvoid qt_customMain() {}\n",
    )
    _write_shader(
        shader_root, "effects/bloom_es.frag", "#version 300 es\nvoid qt_customMain() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert errors == []
    assert capture.exists()

    invocations = [json.loads(line) for line in capture.read_text().splitlines() if line]
    assert invocations, "expected at least one qsb invocation"

    actual_runs = [call for call in invocations if call != ["--version"]]
    assert actual_runs, "expected at least one shader compilation invocation"

    for invocation in actual_runs:
        assert any(
            invocation[index : index + 2] == ["--glsl", "450"]
            for index in range(len(invocation) - 1)
        )
        assert any(
            invocation[index : index + 2] == ["--glsl", "300es"]
            for index in range(len(invocation) - 1)
        )
        assert any(
            invocation[index : index + 2] == ["--hlsl", "50"]
            for index in range(len(invocation) - 1)
        )
        assert any(
            invocation[index : index + 2] == ["--msl", "12"]
            for index in range(len(invocation) - 1)
        )

    log_path = reports_dir / "effects" / "bloom.log"
    qsb_output_path = reports_dir / "effects" / "bloom.qsb"
    assert log_path.exists()
    assert qsb_output_path.exists()
    log_contents = log_path.read_text(encoding="utf-8")
    assert "--hlsl 50" in log_contents
    assert "--msl 12" in log_contents


def test_validate_shaders_reports_missing_gles_variant(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(tmp_path)

    _write_shader(
        shader_root, "effects/ssao.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/ssao_fallback.frag", "#version 450 core\nvoid qt_customMain() {}\n"
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
        shader_root, "effects/dof.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_fallback.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_es.frag", "#version 300 es\nvoid qt_customMain() {}\n"
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
        shader_root, "effects/dof.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_fallback.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )
    _write_shader(
        shader_root, "effects/dof_es.frag", "#version 100 es\nvoid qt_customMain() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("expected '#version 300 es'" in message for message in errors)


def test_validate_shaders_propagates_qsb_failure(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    qsb_cmd = _make_qsb_stub(
        tmp_path,
        exit_code=2,
        stderr="fatal: syntax error",
        version_exit_code=0,
    )

    _write_shader(
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )

    errors = validate_shaders.validate_shaders(
        shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
    )

    assert any("qsb failed" in message for message in errors)
    assert any("fatal: syntax error" in message for message in errors)


def test_validate_shaders_raises_when_shared_library_missing(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"
    reports_dir = tmp_path / "reports"
    stderr = (
        "/opt/qt/bin/qsb: error while loading shared libraries: libxkbcommon.so.0: "
        "cannot open shared object file: No such file or directory"
    )
    qsb_cmd = _make_qsb_stub(tmp_path, exit_code=127, stderr=stderr)

    _write_shader(
        shader_root, "effects/bloom.frag", "#version 450 core\nvoid qt_customMain() {}\n"
    )

    with pytest.raises(validate_shaders.ShaderValidationUnavailableError) as excinfo:
        validate_shaders.validate_shaders(
            shader_root, qsb_command=qsb_cmd, reports_dir=reports_dir
        )

    message = str(excinfo.value)
    assert "libxkbcommon.so.0" in message
    assert "Qt Shader Baker could not start" in message
