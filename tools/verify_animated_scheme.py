"""Verification script for animated scheme configuration and materials."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "app_settings.json"
SHARED_MATERIALS_PATH = REPO_ROOT / "assets" / "qml" / "scene" / "SharedMaterials.qml"
SIM_ROOT_PATH = REPO_ROOT / "assets" / "qml" / "PneumoStabSim" / "SimulationRoot.qml"

REQUIRED_WARNING_FIELDS = {
    "piston_body": ["warning_color"],
    "piston_rod": ["warning_color"],
    "joint_rod": ["ok_color", "error_color"],
}

TEXTURE_EXPECTED_IDS = [
    "frameBaseColorTexture",
    "leverBaseColorTexture",
    "tailRodBaseColorTexture",
    "cylinderBaseColorTexture",
    "pistonBodyBaseColorTexture",
    "pistonRodBaseColorTexture",
    "jointTailBaseColorTexture",
    "jointArmBaseColorTexture",
]

BASECOLORMAP_EXPECTATIONS = {
    "frameMaterial": "frameBaseColorTexture",
    "leverMaterial": "leverBaseColorTexture",
    "tailRodMaterial": "tailRodBaseColorTexture",
    "cylinderMaterial": "cylinderBaseColorTexture",
    "pistonBodyMaterial": "pistonBodyBaseColorTexture",
    "pistonRodMaterial": "pistonRodBaseColorTexture",
    "jointTailMaterial": "jointTailBaseColorTexture",
    "jointArmMaterial": "jointArmBaseColorTexture",
}

PROPERTY_SUFFIX_REQUIRED = {
    "texture_path",
    "normal_strength",
    "occlusion_amount",
    "thickness",
    "alpha_mode",
    "alpha_cutoff",
}


def load_config() -> None:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for section_key in ("current", "defaults_snapshot"):
        try:
            materials = data[section_key]["graphics"]["materials"]
        except KeyError as exc:  # pragma: no cover - misconfiguration guard
            raise SystemExit(f"Missing graphics.materials in {section_key}: {exc}")
        for material_key, payload in materials.items():
            if "texture_path" not in payload:
                raise SystemExit(
                    f"Material '{material_key}' in {section_key} lacks 'texture_path'"
                )
            if not isinstance(payload.get("texture_path", ""), str):
                raise SystemExit(
                    f"Material '{material_key}' in {section_key} has non-string texture_path"
                )
            for field in REQUIRED_WARNING_FIELDS.get(material_key, []):
                if field not in payload:
                    raise SystemExit(
                        f"Material '{material_key}' in {section_key} lacks '{field}'"
                    )
        if materials.get("cylinder", {}).get("alpha_mode") != "blend":
            raise SystemExit(
                f"Expected cylinder alpha_mode='blend' in {section_key} configuration"
            )


def ensure_shared_materials_textures() -> None:
    text = SHARED_MATERIALS_PATH.read_text(encoding="utf-8")
    for tex_id in TEXTURE_EXPECTED_IDS:
        if tex_id not in text:
            raise SystemExit(f"SharedMaterials.qml missing texture resource '{tex_id}'")
    for material_id, texture_id in BASECOLORMAP_EXPECTATIONS.items():
        pattern = (
            rf"{material_id}\s*:\s*PrincipledMaterial\s*{{"
            rf"[^}}]*baseColorMap:\s*(?:root\.)?textureEnabled\([^\n{{}}]*\)\s*\?\s*(?:root\.)?{texture_id}"
        )
        if not re.search(pattern, text, re.DOTALL):
            raise SystemExit(
                f"SharedMaterials.qml missing baseColorMap binding for {material_id}"
            )
    required_props = [
        "frameTexturePath",
        "leverTexturePath",
        "tailRodTexturePath",
        "cylinderTexturePath",
        "pistonBodyTexturePath",
        "pistonRodTexturePath",
        "jointTailTexturePath",
        "jointArmTexturePath",
    ]
    for prop in required_props:
        if prop not in text:
            raise SystemExit(f"SharedMaterials.qml missing property '{prop}'")
    helper_checks = [
        "normalizedTexturePath",
        "resolveTextureSource",
        "textureEnabled",
        "alphaModeValue",
    ]
    for helper in helper_checks:
        if helper not in text:
            raise SystemExit(f"SharedMaterials.qml missing helper '{helper}'")


def ensure_property_suffix_map() -> None:
    text = SIM_ROOT_PATH.read_text(encoding="utf-8")
    for prop in PROPERTY_SUFFIX_REQUIRED:
        camel = "".join(part.capitalize() for part in prop.split("_"))
        token = f'{prop}: "{camel}"'
        if token not in text:
            raise SystemExit(
                f"SimulationRoot.qml missing propertySuffixMap entry for '{prop}'"
            )


def main() -> None:
    load_config()
    ensure_shared_materials_textures()
    ensure_property_suffix_map()
    print("verify_animated_scheme: OK")


if __name__ == "__main__":
    main()
