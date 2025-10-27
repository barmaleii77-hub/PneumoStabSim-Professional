"""Regression tests for the Visual Studio Insiders automation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MSBUILD_NS = {"msb": "http://schemas.microsoft.com/developer/msbuild/2003"}


def _load_pyproj() -> ET.ElementTree:
    path = PROJECT_ROOT / "PneumoStabSim-Professional.pyproj"
    return ET.parse(path)


def test_insiders_target_invokes_bootstrap_script() -> None:
    tree = _load_pyproj()
    target = tree.find(
        "msb:Target[@Name='PrepareVisualStudioInsidersEnvironment']",
        namespaces=_MSBUILD_NS,
    )
    assert target is not None, "PrepareVisualStudioInsidersEnvironment target missing"

    before_targets = target.attrib.get("BeforeTargets", "")
    parts = {part.strip() for part in before_targets.split(";") if part.strip()}
    assert {"PrepareForBuild", "PrepareForRun"}.issubset(parts)

    condition = target.attrib.get("Condition", "")
    assert "Windows_NT" in condition
    assert "Exists('$(VisualStudioInsidersBootstrapScript)')" in condition

    exec_element = target.find("msb:Exec", namespaces=_MSBUILD_NS)
    assert exec_element is not None
    command = exec_element.attrib.get("Command", "")
    assert "powershell" in command.lower()
    script_token = "initialize_insiders_environment.ps1"
    assert script_token in command or "$(VisualStudioInsidersBootstrapScript)" in command


def test_vsconfig_post_install_runs_bootstrap() -> None:
    config_path = PROJECT_ROOT / "PneumoStabSim-Professional.insiders.vsconfig"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    post_install = data.get("customizations", {}).get("postInstall", [])
    assert post_install, "postInstall block missing from VS config"

    matches = [
        step
        for step in post_install
        if step.get("command") == "powershell"
        and "initialize_insiders_environment.ps1" in step.get("arguments", "")
    ]
    assert matches, "Visual Studio postInstall does not invoke the bootstrap script"


def test_bootstrap_script_runs_quality_gate() -> None:
    script_path = PROJECT_ROOT / "tools" / "visualstudio" / "initialize_insiders_environment.ps1"
    content = script_path.read_text(encoding="utf-8")

    assert "Running PneumoStabSim quality gate (ci_tasks verify)" in content
    assert "tools.ci_tasks" in content
    assert "'verify'" in content


def test_launch_profile_exposes_bootstrap_hint() -> None:
    launch_settings_path = PROJECT_ROOT / "Properties" / "launchSettings.json"
    launch_data = json.loads(launch_settings_path.read_text(encoding="utf-8"))
    profiles = launch_data.get("profiles", {})
    insiders_profile = profiles.get("Visual Studio Insiders (App)")
    assert insiders_profile is not None, "Missing Visual Studio Insiders launch profile"

    env_vars = insiders_profile.get("environmentVariables", {})
    assert (
        env_vars.get("INSIDERS_BOOTSTRAP_SCRIPT")
        == "tools/visualstudio/initialize_insiders_environment.ps1"
    )
