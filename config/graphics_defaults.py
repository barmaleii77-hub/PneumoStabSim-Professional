"""
Graphics and Visualization Default Configuration
All default values for lighting, materials, effects, and camera
Shared between Python (GraphicsPanel) and QML (main.qml)

ВАЖНО: Эти значения - единственный источник истины для графики!
Python и QML должны использовать ТОЛЬКО эти значения при инициализации.
"""

# ===============================================================
# 💡 LIGHTING DEFAULTS (Освещение)
# ===============================================================

LIGHTING_DEFAULTS = {
    # Key Light (основной свет)
    'keyLightBrightness': 2.8,
    'keyLightColor': '#ffffff',
    'keyLightAngleX': -30.0,
    'keyLightAngleY': -45.0,
    
    # Fill Light (заполняющий свет)
    'fillLightBrightness': 1.2,
    'fillLightColor': '#f0f0ff',
    
    # Rim Light (контровой свет)
    'rimBrightness': 1.5,
    'rimColor': '#ffffcc',
    
    # Point Light (точечный свет)
    'pointLightBrightness': 20000.0,
    'pointLightColor': '#ffffff',
    'pointLightY': 1800.0,
    'pointFade': 0.00008,
}

# ===============================================================
# 🌍 ENVIRONMENT DEFAULTS (Окружение)
# ===============================================================

ENVIRONMENT_DEFAULTS = {
    # Background
    'background_color': '#2a2a2a',
    
    # Skybox
    'skybox_enabled': True,
    'skybox_blur': 0.0,
    
    # IBL (Image Based Lighting)
    'ibl_enabled': True,
    'ibl_intensity': 1.0,
    'ibl_source': '../hdr/studio.hdr',
    'ibl_fallback': 'assets/studio_small_09_2k.hdr',
    
    # Fog
    'fog_enabled': False,
    'fog_color': '#808080',
    'fog_density': 0.1,
}

# ===============================================================
# ⚙️ QUALITY DEFAULTS (Качество рендеринга)
# ===============================================================

QUALITY_DEFAULTS = {
    # Antialiasing
    'antialiasing': 2,           # 0=None, 1=SSAA, 2=MSAA, 3=ProgressiveAA
    'aa_quality': 2,             # 0=Low, 1=Medium, 2=High
    
    # Shadows
    'shadows_enabled': True,
    'shadow_quality': 2,         # 0=Low, 1=Medium, 2=High
    'shadow_softness': 0.5,      # 0.0-2.0
}

# ===============================================================
# 🎨 MATERIAL DEFAULTS (Материалы)
# ===============================================================

MATERIAL_DEFAULTS = {
    # Metal (общие металлические части)
    'metal_roughness': 0.28,
    'metal_metalness': 1.0,
    'metal_clearcoat': 0.25,
    
    # Glass (стеклянные части)
    'glass_opacity': 0.35,
    'glass_roughness': 0.05,
    'glass_ior': 1.52,           # Коэффициент преломления
    
    # Frame (рама)
    'frame_color': '#cc0000',
    'frame_metalness': 0.8,
    'frame_roughness': 0.4,
    'frame_clearcoat': 0.1,
    'frame_clearcoat_roughness': 0.2,
    
    # Lever (рычаги)
    'lever_color': '#888888',
    'lever_metalness': 1.0,
    'lever_roughness': 0.28,
    'lever_clearcoat': 0.25,
    'lever_clearcoat_roughness': 0.1,
    
    # Tail (хвостовой шток)
    'tail_color': '#cccccc',
    'tail_metalness': 1.0,
    'tail_roughness': 0.3,
    
    # Cylinder (корпус цилиндра)
    'cylinder_color': '#ffffff',
    'cylinder_metalness': 0.0,
    'cylinder_roughness': 0.05,
    
    # Piston body (корпус поршня)
    'piston_body_color': '#ff0066',
    'piston_body_warning_color': '#ff4444',
    'piston_body_metalness': 1.0,
    'piston_body_roughness': 0.28,
    
    # Piston rod (шток поршня)
    'piston_rod_color': '#cccccc',
    'piston_rod_warning_color': '#ff0000',
    'piston_rod_metalness': 1.0,
    'piston_rod_roughness': 0.28,
    
    # Joints (шарниры)
    'joint_tail_color': '#0088ff',
    'joint_arm_color': '#ff8800',
    'joint_rod_ok_color': '#00ff44',
    'joint_rod_error_color': '#ff0000',
    'joint_metalness': 0.9,
    'joint_roughness': 0.35,
}

# ===============================================================
# 📷 CAMERA DEFAULTS (Камера)
# ===============================================================

CAMERA_DEFAULTS = {
    'camera_fov': 45.0,
    'camera_near': 10.0,
    'camera_far': 50000.0,
    'camera_speed': 1.0,
    'auto_rotate': False,
    'auto_rotate_speed': 0.5,
}

# ===============================================================
# ✨ EFFECTS DEFAULTS (Визуальные эффекты)
# ===============================================================

EFFECTS_DEFAULTS = {
    # Bloom
    'bloom_enabled': False,
    'bloom_intensity': 0.3,
    'bloom_threshold': 1.0,
    
    # SSAO (Screen Space Ambient Occlusion)
    'ssao_enabled': False,
    'ssao_intensity': 0.5,
    'ssao_radius': 8.0,
    
    # Motion Blur
    'motion_blur': False,
    
    # Depth of Field
    'depth_of_field': False,
    'dof_focus_distance': 2000.0,
    'dof_focus_range': 900.0,
    
    # Tonemap
    'tonemap_enabled': True,
    'tonemap_mode': 3,           # 0=None, 1=Linear, 2=Reinhard, 3=Filmic
    
    # Vignette
    'vignette_enabled': True,
    'vignette_strength': 0.45,
    
    # Lens Flare
    'lens_flare_enabled': True,
}

# ===============================================================
# 🔧 COMBINED DEFAULTS (Все вместе)
# ===============================================================

ALL_GRAPHICS_DEFAULTS = {
    **LIGHTING_DEFAULTS,
    **ENVIRONMENT_DEFAULTS,
    **QUALITY_DEFAULTS,
    **MATERIAL_DEFAULTS,
    **CAMERA_DEFAULTS,
    **EFFECTS_DEFAULTS,
}


def get_lighting_defaults():
    """Получить дефолты освещения"""
    return LIGHTING_DEFAULTS.copy()


def get_environment_defaults():
    """Получить дефолты окружения"""
    return ENVIRONMENT_DEFAULTS.copy()


def get_quality_defaults():
    """Получить дефолты качества"""
    return QUALITY_DEFAULTS.copy()


def get_material_defaults():
    """Получить дефолты материалов"""
    return MATERIAL_DEFAULTS.copy()


def get_camera_defaults():
    """Получить дефолты камеры"""
    return CAMERA_DEFAULTS.copy()


def get_effects_defaults():
    """Получить дефолты эффектов"""
    return EFFECTS_DEFAULTS.copy()


def get_all_graphics_defaults():
    """Получить ВСЕ дефолты графики"""
    return ALL_GRAPHICS_DEFAULTS.copy()


# Export
__all__ = [
    'LIGHTING_DEFAULTS',
    'ENVIRONMENT_DEFAULTS',
    'QUALITY_DEFAULTS',
    'MATERIAL_DEFAULTS',
    'CAMERA_DEFAULTS',
    'EFFECTS_DEFAULTS',
    'ALL_GRAPHICS_DEFAULTS',
    'get_lighting_defaults',
    'get_environment_defaults',
    'get_quality_defaults',
    'get_material_defaults',
    'get_camera_defaults',
    'get_effects_defaults',
    'get_all_graphics_defaults',
]
