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
    'keyLightBrightness': 1.0,      # Changed to realistic default (0-10)
    'keyLightColor': '#ffffff',
    'keyLightAngleX': -30.0,
    'keyLightAngleY': -45.0,
    
    # Fill Light (заполняющий свет)
    'fillLightBrightness': 0.5,     # Changed to realistic default (0-5)
    'fillLightColor': '#f0f0ff',
    
    # Rim Light (контровой свет)
    'rimBrightness': 0.8,           # Changed to realistic default
    'rimColor': '#ffffcc',
    
    # Point Light (точечный свет)
    'pointLightBrightness': 1000.0, # Changed to realistic default (0-100000)
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
    
    # Ambient Occlusion (SSAO)
    'ambient_occlusion': True,
    'ao_intensity': 1.0,
}

# ===============================================================
# ⚙️ QUALITY DEFAULTS (Качество рендеринга)
# ===============================================================

QUALITY_DEFAULTS = {
    # Antialiasing
    'antialiasing': 2,           # 0=None, 1=SSAA, 2=MSAA, 3=ProgressiveAA, 4=FXAA, 5=TAA
    'aa_quality': 2,             # 0=Low (2x), 1=Medium (4x), 2=High (8x)
    'specular_aa': True,         # Specular antialiasing (reduces shimmer)
    'taa_enabled': False,        # Temporal antialiasing
    'taa_strength': 0.3,         # TAA strength (0.0-1.0)
    
    # Shadows
    'shadows_enabled': True,
    'shadow_quality': 2,         # 0=Low (256), 1=Medium (512), 2=High (1024), 3=VeryHigh (2048), 4=Ultra (4096)
    'shadow_softness': 10.0,     # Shadow bias (default ~10)
    'shadow_darkness': 75.0,     # Shadow darkness (0-100%)
    'shadow_filter': 3,          # 0=Hard, 1=PCF4, 2=PCF8, 3=PCF16, 4=PCF32
}

# ===============================================================
# 🎨 MATERIAL DEFAULTS (Материалы)
# ===============================================================

MATERIAL_DEFAULTS = {
    # Metal (общие металлические части)
    'metal_roughness': 0.5,          # Changed to default 0.5
    'metal_metalness': 1.0,
    'metal_clearcoat': 0.0,          # Changed to default 0.0
    'metal_specular_amount': 1.0,
    'metal_specular_tint': 0.0,
    'metal_clearcoat_roughness': 0.0,
    
    # Glass (стеклянные части)
    'glass_opacity': 1.0,            # Changed: use transmission instead
    'glass_roughness': 0.0,          # Changed to 0.0 for clear glass
    'glass_ior': 1.5,                # Коэффициент преломления
    'glass_transmission': 1.0,       # Transmission factor (0-1)
    'glass_thickness': 1.0,          # Thickness factor
    'glass_attenuation_distance': 10000.0,  # Attenuation distance (inf default)
    'glass_attenuation_color': '#ffffff',   # Attenuation color
    
    # Frame (рама)
    'frame_color': '#cc0000',
    'frame_metalness': 0.0,          # Changed: frame is not metal by default
    'frame_roughness': 0.5,
    'frame_clearcoat': 0.0,
    'frame_clearcoat_roughness': 0.0,
    
    # Lever (рычаги)
    'lever_color': '#888888',
    'lever_metalness': 1.0,
    'lever_roughness': 0.5,
    'lever_clearcoat': 0.0,
    'lever_clearcoat_roughness': 0.0,
    
    # Tail (хвостовой шток)
    'tail_color': '#cccccc',
    'tail_metalness': 1.0,
    'tail_roughness': 0.5,
    
    # Cylinder (корпус цилиндра)
    'cylinder_color': '#ffffff',
    'cylinder_metalness': 0.0,
    'cylinder_roughness': 0.05,
    
    # Piston body (корпус поршня)
    'piston_body_color': '#ff0066',
    'piston_body_warning_color': '#ff4444',
    'piston_body_metalness': 1.0,
    'piston_body_roughness': 0.5,
    'piston_body_emissive_color': '#000000',
    'piston_body_emissive_intensity': 0.0,
    
    # Piston rod (шток поршня)
    'piston_rod_color': '#cccccc',
    'piston_rod_warning_color': '#ff0000',
    'piston_rod_metalness': 1.0,
    'piston_rod_roughness': 0.5,
    
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
    'camera_fov': 60.0,              # Changed to default 60°
    'camera_near': 10.0,             # Changed to 10mm
    'camera_far': 50000.0,
    'camera_speed': 1.0,
    'auto_rotate': False,
    'auto_rotate_speed': 1.0,        # Changed to 1.0
}

# ===============================================================
# ✨ EFFECTS DEFAULTS (Визуальные эффекты)
# ===============================================================

EFFECTS_DEFAULTS = {
    # Bloom
    'bloom_enabled': False,
    'bloom_intensity': 0.5,          # Changed to 0.5
    'bloom_threshold': 1.0,
    
    # SSAO (Screen Space Ambient Occlusion)
    'ssao_enabled': False,
    'ssao_intensity': 1.0,           # Changed to 1.0
    'ssao_radius': 50.0,             # Changed to scene units
    
    # Motion Blur
    'motion_blur': False,
    
    # Depth of Field
    'depth_of_field': False,
    'dof_focus_distance': 1000.0,    # Changed to 1000
    'dof_focus_range': 500.0,        # Changed to reasonable range
    'dof_blur_amount': 4.0,
    
    # Tonemap
    'tonemap_enabled': True,
    'tonemap_mode': 3,           # 0=None, 1=Linear, 2=Reinhard, 3=Filmic
    
    # Vignette
    'vignette_enabled': False,       # Changed to False by default
    'vignette_strength': 0.5,
    
    # Lens Flare
    'lens_flare_enabled': False,     # Changed to False by default
    
    # Order-Independent Transparency
    'oit_method': 'WeightedBlended', # For correct transparent material blending
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
