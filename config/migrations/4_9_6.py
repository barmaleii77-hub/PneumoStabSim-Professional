"""Migration helpers for settings version4.9.6."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

TARGET_VERSION = "4.9.6"
PREVIOUS_VERSION = "4.9.5"

_NEW_EFFECTS_DEFAULTS = {
 "bloom_glow_strength":1.0,
 "bloom_hdr_max":8.0,
 "bloom_hdr_scale":2.0,
 "bloom_quality_high": True,
 "bloom_bicubic_upscale": True,
 "lens_flare_ghost_count":4,
 "lens_flare_ghost_dispersal":0.06,
 "lens_flare_halo_width":0.05,
 "lens_flare_bloom_bias":1.0,
}

_MESH_DEFAULTS = {
 "cylinder_segments":128,
 "cylinder_rings":32,
}


def _ensure_nested(root: Dict[str, Any], path: list[str]) -> Dict[str, Any]:
 node: Dict[str, Any] = root
 for key in path:
 child = node.get(key)
 if not isinstance(child, dict):
 child = {}
 node[key] = child
 node = child
 return node


def _upgrade_effects(root: Dict[str, Any]) -> bool:
 changed = False
 for section in ("current", "defaults_snapshot"):
 effects = _ensure_nested(root, [section, "graphics", "effects"])
 if "bloom_glow_level" in effects:
 effects.pop("bloom_glow_level", None)
 changed = True
 for key, value in _NEW_EFFECTS_DEFAULTS.items():
 if key not in effects:
 effects[key] = deepcopy(value)
 changed = True
 return changed


def _upgrade_mesh(root: Dict[str, Any]) -> bool:
 changed = False
 for section in ("current", "defaults_snapshot"):
 mesh = _ensure_nested(root, [section, "graphics", "quality", "mesh"])
 for key, value in _MESH_DEFAULTS.items():
 if key not in mesh:
 mesh[key] = deepcopy(value)
 changed = True
 return changed


def upgrade(data: Dict[str, Any]) -> Dict[str, Any]:
 """Upgrade payload to version4.9.6."""
 changed = False
 if _upgrade_effects(data):
 changed = True
 if _upgrade_mesh(data):
 changed = True

 metadata = data.setdefault("metadata", {})
 previous = metadata.get("version")
 if previous != TARGET_VERSION:
 metadata["previous_version"] = previous or PREVIOUS_VERSION
 metadata["version"] = TARGET_VERSION
 changed = True

 return data if changed else data


def downgrade(data: Dict[str, Any]) -> Dict[str, Any]:
 """Downgrade payload back to version4.9.5."""
 for section in ("current", "defaults_snapshot"):
 effects = _ensure_nested(data, [section, "graphics", "effects"])
 for key in _NEW_EFFECTS_DEFAULTS:
 effects.pop(key, None)
 effects.setdefault("bloom_glow_level",0.0)

 quality = _ensure_nested(data, [section, "graphics", "quality"])
 quality.pop("mesh", None)

 metadata = data.setdefault("metadata", {})
 metadata["version"] = PREVIOUS_VERSION
 metadata.pop("previous_version", None)
 return data
