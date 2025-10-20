# -*- coding: utf-8 -*-
"""
Graphics panel defaults and presets
Значения по умолчанию и пресеты для панели графики

ОБНОВЛЕНО v2.0:
- Добавлены Qt 6.10 параметры для Effects Tab
- Все новые параметры из рефакторенных табов
"""
from typing import Any, Dict


def build_defaults() -> Dict[str, Any]:
    """Построить дефолтные настройки графики
    
    Returns:
        Словарь с настройками по умолчанию
    """
    return {
        "lighting": {
            "key": {
                "brightness": 1.2,
                "color": "#ffffff",
                "angle_x": -35.0,
                "angle_y": -40.0,
                "cast_shadow": True,
                "bind_to_camera": False,
                "position_x": 0.0,
                "position_y": 0.0,
            },
            "fill": {
                "brightness": 0.7,
                "color": "#dfe7ff",
                "cast_shadow": False,
                "bind_to_camera": False,
                "position_x": 0.0,
                "position_y": 0.0,
            },
            "rim": {
                "brightness": 1.0,
                "color": "#ffe2b0",
                "cast_shadow": False,
                "bind_to_camera": False,
                "position_x": 0.0,
                "position_y": 0.0,
            },
            "point": {
                "brightness": 1000.0,
                "color": "#ffffff",
                "position_x": 0.0,
                "position_y": 2200.0,
                "range": 3200.0,
                "cast_shadow": False,
                "bind_to_camera": False,
            },
        },
        "environment": {
            "background_mode": "skybox",
            "background_color": "#1f242c",
            "ibl_enabled": True,
            "skybox_enabled": True,
            "ibl_intensity": 1.3,
            "ibl_rotation": 0.0,
            "ibl_source": "",
            "ibl_fallback": "",
            "skybox_blur": 0.08,
            # Новые параметры IBL
            "probe_brightness": 1.0,
            "probe_horizon": 0.0,
            # Fog (расширенный)
            "fog_enabled": True,
            "fog_color": "#b0c4d8",
            "fog_density": 0.12,
            "fog_near": 1200.0,
            "fog_far": 12000.0,
            "fog_height_enabled": False,
            "fog_least_intense_y": 0.0,
            "fog_most_intense_y": 3000.0,
            "fog_height_curve": 1.0,
            "fog_transmit_enabled": True,
            "fog_transmit_curve": 1.0,
            # SSAO
            "ao_enabled": True,
            "ao_strength": 1.0,
            "ao_radius": 8.0,
            # Расширенные параметры SSAO (Qt 6.10)
            "ao_softness": 20.0,
            "ao_dither": True,
            "ao_sample_rate": 4,
            # IBL orientation offsets/bind
            "ibl_offset_x": 0.0,
            "ibl_offset_y": 0.0,
            "ibl_bind_to_camera": False,
        },
        "quality": {
            "preset": "ultra",
            "shadows": {
                "enabled": True,
                "resolution": "4096",
                "filter": 32,
                "bias": 8.0,
                "darkness": 80.0,
            },
            "antialiasing": {"primary": "ssaa", "quality": "high", "post": "taa"},
            "taa_enabled": True,
            "taa_strength": 0.4,
            "taa_motion_adaptive": True,
            "fxaa_enabled": False,
            "specular_aa": True,
            "dithering": True,
            "render_scale": 1.05,
            "render_policy": "always",
            "frame_rate_limit": 144.0,
            "oit": "weighted",
        },
        "camera": {
            "fov": 60.0,
            "near": 10.0,
            "far": 50000.0,
            "speed": 1.0,
            "auto_rotate": False,
            "auto_rotate_speed": 1.0,
        },
        "effects": {
            # Bloom (4 базовых + 5 Qt 6.10)
            "bloom_enabled": True,
            "bloom_intensity": 0.5,
            "bloom_threshold": 1.0,
            "bloom_spread": 0.65,
            "bloom_kernel_size": "large",  # Qt 6.10
            "bloom_kernel_quality": "high",  # Qt 6.10
            "bloom_up_scale_blur": True,  # Qt 6.10
            "bloom_down_scale_blur": True,  # Qt 6.10
            "bloom_glow_level": 0,  # Qt 6.10
            
            # Tonemap (2 базовых + 2 Qt 6.10)
            "tonemap_enabled": True,
            "tonemap_mode": "filmic",
            "tonemap_exposure": 1.0,  # Qt 6.10
            "tonemap_white_point": 1.0,  # Qt 6.10
            
            # Depth of Field (3 базовых)
            "depth_of_field": False,
            "dof_focus_distance": 2200.0,
            "dof_blur": 4.0,
            
            # Motion Blur (2)
            "motion_blur": False,
            "motion_blur_amount": 0.2,
            
            # Lens Flare (1 базовый + 5 Qt 6.10)
            "lens_flare": False,
            "lens_flare_intensity": 1.0,  # Qt 6.10
            "lens_flare_scale": 1.0,  # Qt 6.10
            "lens_flare_spread": 0.5,  # Qt 6.10
            "lens_flare_streak_intensity": 0.5,  # Qt 6.10
            "lens_flare_bloom_scale": 1.0,  # Qt 6.10
            
            # Vignette (2 базовых + 1 Qt 6.10)
            "vignette": False,
            "vignette_strength": 0.35,
            "vignette_radius": 0.5,  # Qt 6.10
            
            # Color Adjustments (3 Qt 6.10)
            "saturation": 1.0,  # Qt 6.10
            "contrast": 1.0,  # Qt 6.10
            "brightness": 0.0,  # Qt 6.10
            
            # SSAO (deprecated, оставлено для совместимости)
            "ssao_enabled": True,
            "ssao_strength": 1.0,
            "ssao_radius": 8.0,
        },
        "materials": _build_materials_defaults(),
    }


def _build_materials_defaults() -> Dict[str, Dict[str, Any]]:
    """Построить дефолты для материалов всех компонентов"""
    return {
        "frame": {
            "base_color": "#c53030",
            "metalness": 0.85,
            "roughness": 0.35,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.22,
            "clearcoat_roughness": 0.1,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ff5454",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "lever": {
            "base_color": "#9ea4ab",
            "metalness": 1.0,
            "roughness": 0.28,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.3,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ff5454",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "tail": {
            "base_color": "#d5d9df",
            "metalness": 1.0,
            "roughness": 0.3,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ffd24d",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "cylinder": {
            "base_color": "#e1f5ff",
            "metalness": 0.0,
            "roughness": 0.05,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "transmission": 1.0,
            "opacity": 1.0,
            "ior": 1.52,
            "attenuation_distance": 1800.0,
            "attenuation_color": "#b7e7ff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ff7070",
            "ok_color": "#7dffd6",
            "error_color": "#ff2a2a",
        },
        "piston_body": {
            "base_color": "#ff3c6e",
            "metalness": 1.0,
            "roughness": 0.26,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.18,
            "clearcoat_roughness": 0.06,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ff5454",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "piston_rod": {
            "base_color": "#ececec",
            "metalness": 1.0,
            "roughness": 0.18,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.12,
            "clearcoat_roughness": 0.05,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ff5454",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "joint_tail": {
            "base_color": "#2a82ff",
            "metalness": 0.9,
            "roughness": 0.35,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.1,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ffd24d",
            "ok_color": "#00ff55",
            "error_color": "#ff0000",
        },
        "joint_arm": {
            "base_color": "#ff9c3a",
            "metalness": 0.9,
            "roughness": 0.32,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.12,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ffd24d",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
        "joint_rod": {
            "base_color": "#00ff55",
            "metalness": 0.9,
            "roughness": 0.3,
            "specular": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.1,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "warning_color": "#ffd24d",
            "ok_color": "#00ff55",
            "error_color": "#ff2a2a",
        },
    }


def build_quality_presets() -> Dict[str, Dict[str, Any]]:
    """Построить пресеты качества графики
    
    Returns:
        Словарь с пресетами качества (ultra, high, medium, low)
    """
    return {
        "ultra": {
            "shadows": {"enabled": True, "resolution": "4096", "filter": 32, "bias": 8.0, "darkness": 80.0},
            "antialiasing": {"primary": "ssaa", "quality": "high", "post": "taa"},
            "taa_enabled": True,
            "taa_strength": 0.4,
            "taa_motion_adaptive": True,
            "fxaa_enabled": False,
            "specular_aa": True,
            "dithering": True,
            "render_scale": 1.05,
            "render_policy": "always",
            "frame_rate_limit": 144.0,
            "oit": "weighted",
        },
        "high": {
            "shadows": {"enabled": True, "resolution": "2048", "filter": 16, "bias": 9.5, "darkness": 78.0},
            "antialiasing": {"primary": "msaa", "quality": "high", "post": "off"},
            "taa_enabled": False,
            "taa_strength": 0.3,
            "taa_motion_adaptive": True,
            "fxaa_enabled": False,
            "specular_aa": True,
            "dithering": True,
            "render_scale": 1.0,
            "render_policy": "always",
            "frame_rate_limit": 120.0,
            "oit": "weighted",
        },
        "medium": {
            "shadows": {"enabled": True, "resolution": "1024", "filter": 8, "bias": 10.0, "darkness": 75.0},
            "antialiasing": {"primary": "msaa", "quality": "medium", "post": "fxaa"},
            "taa_enabled": False,
            "taa_strength": 0.25,
            "taa_motion_adaptive": True,
            "fxaa_enabled": True,
            "specular_aa": True,
            "dithering": True,
            "render_scale": 0.9,
            "render_policy": "always",
            "frame_rate_limit": 90.0,
            "oit": "weighted",
        },
        "low": {
            "shadows": {"enabled": True, "resolution": "512", "filter": 4, "bias": 12.0, "darkness": 70.0},
            "antialiasing": {"primary": "off", "quality": "low", "post": "fxaa"},
            "taa_enabled": False,
            "taa_strength": 0.2,
            "taa_motion_adaptive": True,
            "fxaa_enabled": True,
            "specular_aa": False,
            "dithering": True,
            "render_scale": 0.8,
            "render_policy": "ondemand",
            "frame_rate_limit": 60.0,
            "oit": "none",
        },
    }


# Экспорт главного объекта
GRAPHICS_DEFAULTS = build_defaults()
