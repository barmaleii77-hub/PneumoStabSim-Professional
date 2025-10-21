import pytest
from src.ui.geometry_schema import validate_geometry_settings, GeometryValidationError

def test_validate_geometry_settings():
 valid_payload = {
 "wheelbase":2.0,
 "track":0.391,
 "frame_to_pivot":0.351,
 "lever_length":0.609,
 "rod_position":0.754,
 "cylinder_length":0.491,
 "cyl_diam_m":0.251,
 "stroke_m":0.3,
 "dead_gap_m":0.005,
 "rod_diameter_m":0.118,
 "piston_rod_length_m":0.5,
 "piston_thickness_m":0.1,
 "frame_height_mm":650.0,
 "frame_beam_size_mm":120.0,
 "tail_rod_length_mm":100.0,
 "tail_mount_offset_mm":100.0,
 "joint_tail_scale":1.0,
 "joint_arm_scale":1.0,
 "joint_rod_scale":1.0,
 "interference_check": True,
 "link_rod_diameters": False
 }

 # Should not raise any exceptions
 validated = validate_geometry_settings(valid_payload)
 assert validated.to_config_dict() == valid_payload

 invalid_payload = valid_payload.copy()
 invalid_payload["wheelbase"] = -1.0

 # Fixed indentation issue in the test case for invalid payload.
 with pytest.raises(GeometryValidationError):
  validate_geometry_settings(invalid_payload)
