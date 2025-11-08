"""Typed Pydantic models that describe the structure of ``app_settings.json``.

The models intentionally mirror the JSON schema so that service layers can
operate on rich objects instead of manipulating untyped ``dict`` values.  Only
the sections that are consumed across the application are modelled explicitly –
any leaf nodes that are not yet required can easily be extended thanks to
Pydantic's forward compatibility.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, RootModel, model_validator


class _StrictModel(BaseModel):
    """Base class that forbids unknown fields by default."""

    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }


class Metadata(_StrictModel):
    version: str
    schema_version: str
    last_modified: str
    units_version: str
    migrations: list[str]
    last_migration: str
    migrated_from: str
    migration_date: str
    total_parameters: int
    description: str
    operational_imperatives: list[str]
    environment_slider_ranges: dict[str, "SliderRange"]
    legacy: dict[str, dict[str, Any]] = Field(default_factory=dict)


class SimulationSettings(_StrictModel):
    physics_dt: float
    render_vsync_hz: float
    max_steps_per_frame: int
    max_frame_time: float


class ReceiverVolumeLimits(_StrictModel):
    min_m3: float
    max_m3: float


class PneumaticSettings(_StrictModel):
    volume_mode: str
    receiver_volume: float
    receiver_diameter: float
    receiver_length: float
    cv_atmo_dp: float
    cv_tank_dp: float
    cv_atmo_dia: float
    cv_tank_dia: float
    relief_min_pressure: float
    relief_stiff_pressure: float
    relief_safety_pressure: float
    throttle_min_dia: float
    throttle_stiff_dia: float
    diagonal_coupling_dia: float
    atmo_temp: float
    thermo_mode: str
    polytropic_heat_transfer_coeff: float
    polytropic_exchange_area: float
    leak_coefficient: float
    leak_reference_area: float
    master_isolation_open: bool
    pressure_units: str
    receiver_volume_limits: ReceiverVolumeLimits


class GeometrySettings(_StrictModel):
    wheelbase: float
    track: float
    frame_to_pivot: float
    lever_length: float
    rod_position: float
    cylinder_length: float
    cyl_diam_m: float
    stroke_m: float
    dead_gap_m: float
    rod_diameter_m: float
    rod_diameter_rear_m: float
    piston_rod_length_m: float
    piston_thickness_m: float
    frame_mass: float
    wheel_mass: float
    tail_rod_length_m: float
    interference_check: bool
    link_rod_diameters: bool
    frame_height_m: float
    frame_beam_size_m: float
    frame_length_m: float
    lever_length_m: float
    cylinder_body_length_m: float
    active_preset: str


class ModesPhysicsSettings(_StrictModel):
    include_springs: bool
    include_dampers: bool
    include_pneumatics: bool
    spring_constant: float
    damper_coefficient: float
    lever_inertia_multiplier: float
    damper_force_threshold_n: float
    spring_rest_position_m: float
    integrator_method: str


class ModesSettings(_StrictModel):
    sim_type: str
    mode_preset: str
    amplitude: float
    frequency: float
    phase: float
    lf_phase: float
    rf_phase: float
    lr_phase: float
    rr_phase: float
    physics: ModesPhysicsSettings


class _LightBase(_StrictModel):
    brightness: float
    color: str
    angle_x: float
    angle_y: float
    angle_z: float
    position_x: float
    position_y: float
    position_z: float
    cast_shadow: bool
    bind_to_camera: bool


class PointLightSettings(_StrictModel):
    brightness: float
    color: str
    position_x: float
    position_y: float
    position_z: float
    range: float
    constant_fade: float
    linear_fade: float
    quadratic_fade: float
    cast_shadow: bool
    bind_to_camera: bool


class SpotLightSettings(_StrictModel):
    brightness: float
    color: str
    position_x: float
    position_y: float
    position_z: float
    range: float
    cone_angle: float
    inner_cone_angle: float
    angle_x: float
    angle_y: float
    angle_z: float
    cast_shadow: bool
    bind_to_camera: bool


class LightingSettings(_StrictModel):
    key: _LightBase
    fill: _LightBase
    rim: _LightBase
    point: PointLightSettings
    spot: SpotLightSettings


class EnvironmentSettings(_StrictModel):
    background_mode: str
    background_color: str
    skybox_enabled: bool
    ibl_enabled: bool
    ibl_intensity: float
    skybox_brightness: float
    probe_horizon: float
    ibl_rotation: float
    ibl_source: str
    skybox_blur: float
    ibl_offset_x: float
    ibl_offset_y: float
    ibl_bind_to_camera: bool
    reflection_enabled: bool
    reflection_padding_m: float
    reflection_quality: str
    reflection_refresh_mode: str
    reflection_time_slicing: str
    fog_enabled: bool
    fog_color: str
    fog_density: float
    fog_near: float
    fog_far: float
    fog_height_enabled: bool
    fog_least_intense_y: float
    fog_most_intense_y: float
    fog_height_curve: float
    fog_transmit_enabled: bool
    fog_transmit_curve: float
    ao_enabled: bool
    ao_strength: float
    ao_radius: float
    ao_softness: float
    ao_dither: bool
    ao_sample_rate: int


class ShadowsSettings(_StrictModel):
    enabled: bool
    resolution: int
    filter: float
    bias: float
    darkness: float


class AntialiasingSettings(_StrictModel):
    primary: str
    quality: str
    post: str


class MeshSettings(_StrictModel):
    cylinder_segments: int
    cylinder_rings: int


class QualitySettings(_StrictModel):
    preset: str | None = None
    shadows: ShadowsSettings
    antialiasing: AntialiasingSettings
    taa_enabled: bool
    taa_strength: float
    taa_motion_adaptive: bool
    fxaa_enabled: bool
    specular_aa: bool
    dithering: bool
    render_scale: float
    render_policy: str
    frame_rate_limit: float
    oit: str
    mesh: MeshSettings


class CameraSettings(_StrictModel):
    fov: float
    near: float
    far: float
    speed: float
    auto_rotate: bool
    auto_rotate_speed: float
    auto_fit: bool
    manual_camera: bool
    camera_pos_x: float
    camera_pos_y: float
    camera_pos_z: float
    camera_rot_x: float
    camera_rot_y: float
    camera_rot_z: float
    orbit_target_x: float
    orbit_target_y: float
    orbit_target_z: float
    orbit_yaw: float
    orbit_pitch: float
    orbit_distance: float
    orbit_inertia_enabled: bool
    orbit_inertia: float
    orbit_rotate_smoothing: float
    orbit_pan_smoothing: float
    orbit_zoom_smoothing: float
    orbit_friction: float
    world_pos_x: float
    world_pos_y: float
    world_pos_z: float
    world_rot_x: float
    world_rot_y: float
    world_rot_z: float
    world_scale: float


class MaterialSettings(_StrictModel):
    base_color: str
    metalness: float
    roughness: float
    specular: float
    specular_tint: str
    opacity: float
    clearcoat: float
    clearcoat_roughness: float
    transmission: float
    ior: float
    thickness: float
    attenuation_distance: float
    attenuation_color: str
    emissive_color: str
    emissive_intensity: float
    normal_strength: float
    texture_path: str | None = None
    occlusion_amount: float
    alpha_mode: str
    alpha_cutoff: float
    warning_color: str | None = None
    ok_color: str | None = None
    error_color: str | None = None
    id: str


class MaterialsSettings(_StrictModel):
    frame: MaterialSettings
    lever: MaterialSettings
    tail_rod: MaterialSettings
    cylinder: MaterialSettings
    piston_body: MaterialSettings
    piston_rod: MaterialSettings
    joint_tail: MaterialSettings
    joint_arm: MaterialSettings
    joint_rod: MaterialSettings


class EffectsSettings(_StrictModel):
    bloom_enabled: bool
    bloom_intensity: float
    bloom_threshold: float
    bloom_spread: float
    bloom_glow_strength: float
    bloom_hdr_max: float
    bloom_hdr_scale: float
    bloom_quality_high: bool
    bloom_bicubic_upscale: bool
    tonemap_enabled: bool
    tonemap_mode: str
    tonemap_exposure: float
    tonemap_white_point: float
    depth_of_field: bool
    dof_auto_focus: bool
    dof_focus_distance: float
    dof_blur: float
    motion_blur: bool
    motion_blur_amount: float
    lens_flare: bool
    lens_flare_ghost_count: int
    lens_flare_ghost_dispersal: float
    lens_flare_halo_width: float
    lens_flare_bloom_bias: float
    lens_flare_stretch_to_aspect: bool
    vignette: bool
    vignette_strength: float
    vignette_radius: float
    color_adjustments_enabled: bool
    color_adjustments_active: bool
    adjustment_brightness: float
    adjustment_contrast: float
    adjustment_saturation: float


class SceneSettings(_StrictModel):
    scale_factor: float
    exposure: float
    default_clear_color: str
    model_base_color: str
    model_roughness: float
    model_metalness: float


class GraphicsSettings(_StrictModel):
    lighting: LightingSettings
    environment: EnvironmentSettings
    quality: QualitySettings
    camera: CameraSettings
    materials: MaterialsSettings
    effects: EffectsSettings
    scene: SceneSettings
    environment_ranges: dict[str, SliderRange]


class AnimationSettings(_StrictModel):
    is_running: bool
    animation_time: float
    amplitude: float
    frequency: float
    phase_global: float
    phase_fl: float
    phase_fr: float
    phase_rl: float
    phase_rr: float
    smoothing_enabled: bool
    smoothing_duration_ms: float
    smoothing_angle_snap_deg: float
    smoothing_piston_snap_m: float
    smoothing_easing: str


class PhysicsSuspensionSettings(_StrictModel):
    spring_constant: float
    damper_coefficient: float
    damper_force_threshold_n: float
    spring_rest_position_m: float
    cylinder_head_area_m2: float
    cylinder_rod_area_m2: float
    axis_unit_world: list[float]


class PhysicsReferenceAxes(_StrictModel):
    vertical_world: list[float]


class PhysicsValidationSettings(_StrictModel):
    max_force_n: float
    max_moment_n_m: float


class PhysicsIntegratorLoopSettings(_StrictModel):
    max_steps_per_render: int
    max_linear_velocity_m_s: float
    max_angular_velocity_rad_s: float
    lever_ratio_clip_min: float
    lever_ratio_clip_max: float
    nan_replacement_value: float
    posinf_replacement_value: float
    neginf_replacement_value: float
    statistics_min_total_steps: int


class PhysicsIntegratorSolverSettings(_StrictModel):
    primary_method: str
    fallback_methods: list[str]
    relative_tolerance: float
    absolute_tolerance: float
    max_step_divisor: float


class PhysicsIntegratorSettings(_StrictModel):
    loop: PhysicsIntegratorLoopSettings
    solver: PhysicsIntegratorSolverSettings


class AttachmentPoint(_StrictModel):
    x_m: float
    z_m: float


class PhysicsRigidBodySettings(_StrictModel):
    default_mass_kg: float
    default_inertia_roll_kg_m2: float
    default_inertia_pitch_kg_m2: float
    gravity_m_s2: float
    track_width_m: float
    wheelbase_m: float
    static_load_tolerance: float
    load_sum_tolerance_scale: float
    load_sum_min_reference: float
    damping_coefficient: float
    angle_limit_rad: float
    attachment_points_m: dict[str, AttachmentPoint]


class PhysicsConstants(_StrictModel):
    suspension: PhysicsSuspensionSettings
    reference_axes: PhysicsReferenceAxes
    validation: PhysicsValidationSettings
    integrator: PhysicsIntegratorSettings
    rigid_body: PhysicsRigidBodySettings


class PhysicsSettings(_StrictModel):
    suspension: PhysicsSuspensionSettings
    reference_axes: PhysicsReferenceAxes
    validation: PhysicsValidationSettings


class GeometryKinematicsConstants(_StrictModel):
    track_width_m: float
    lever_length_m: float
    pivot_offset_from_frame_m: float
    rod_attach_fraction: float


class GeometryCylinderConstants(_StrictModel):
    inner_diameter_m: float
    piston_thickness_m: float
    rod_diameter_m: float
    body_length_m: float
    dead_zone_head_m3: float
    dead_zone_rod_m3: float


class GeometryVisualizationConstants(_StrictModel):
    cylinder_radius_m: float
    arm_radius_m: float
    pivot_offset_x_m: float
    tail_offset_x_m: float
    piston_clip_min_fraction: float
    piston_clip_max_fraction: float
    max_stroke_fraction: float


class GeometryInitialStateConstants(_StrictModel):
    frame_length_m: float
    frame_height_m: float
    frame_beam_size_m: float
    lever_length_m: float
    cylinder_body_length_m: float
    tail_rod_length_m: float
    j_arm_left: list[float]
    j_arm_right: list[float]
    j_tail_left: list[float]
    j_tail_right: list[float]


class SliderRange(_StrictModel):
    min: float
    max: float
    step: float = Field(gt=0)
    decimals: int | None = None
    units: str | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "SliderRange":
        if self.max <= self.min:
            raise ValueError("Slider range 'max' must be greater than 'min'")
        return self


class GeometryPreset(_StrictModel):
    key: str
    label: str
    values: dict[str, float | bool | str]


class GeometryConstants(_StrictModel):
    kinematics: GeometryKinematicsConstants
    cylinder: GeometryCylinderConstants
    visualization: GeometryVisualizationConstants
    initial_state: GeometryInitialStateConstants
    ui_ranges: dict[str, SliderRange]
    presets: list[GeometryPreset]


class PneumoValveConstants(_StrictModel):
    delta_open_pa: float
    equivalent_diameter_m: float
    relief_min_orifice_diameter_m: float
    relief_stiff_orifice_diameter_m: float


class PneumoReceiverConstants(_StrictModel):
    volume_min_m3: float
    volume_max_m3: float
    initial_volume_m3: float
    initial_pressure_pa: float
    initial_temperature_k: float
    volume_mode: str


class PneumoGasConstants(_StrictModel):
    tank_volume_initial_m3: float
    tank_pressure_initial_pa: float
    tank_temperature_initial_k: float
    tank_volume_mode: str
    thermo_mode: str
    time_step_s: float
    total_time_s: float
    relief_min_threshold_pa: float
    relief_stiff_threshold_pa: float
    relief_safety_threshold_pa: float


class PneumoConstants(_StrictModel):
    valves: PneumoValveConstants
    receiver: PneumoReceiverConstants
    gas: PneumoGasConstants


class Constants(_StrictModel):
    geometry: GeometryConstants
    pneumo: PneumoConstants
    physics: PhysicsConstants


class SignalTraceSettings(_StrictModel):
    enabled: bool
    history_limit: int
    include: list[str]
    exclude: list[str]
    overlay_enabled: bool


class CameraHUDSettings(_StrictModel):
    enabled: bool
    precision: int
    showAngles: bool
    showDamping: bool
    showInertia: bool
    showMotion: bool
    showPan: bool
    showPivot: bool
    showPreset: bool
    showSmoothing: bool
    showTimestamp: bool


class DiagnosticsSettings(_StrictModel):
    signal_trace: SignalTraceSettings
    camera_hud: CameraHUDSettings


class SystemDependencyVariant(_StrictModel):
    id: str
    human_name: str
    platform_prefixes: list[str]
    error_markers: list[str]
    install_hint: str
    library_name: str | None = None
    packages: list[str] | None = None
    install_command: str | None = None


class SystemDependency(_StrictModel):
    description: str
    missing_message: str
    variants: list[SystemDependencyVariant]


class SystemDependencies(_StrictModel):
    egl_runtime: SystemDependency
    opengl_runtime: SystemDependency
    xkb_runtime: SystemDependency


class SystemSettings(_StrictModel):
    dependencies: SystemDependencies


class QualityPreset(RootModel[QualitySettings]):
    """Wrapper for quality presets so they share the quality schema."""


class QualityPresets(_StrictModel):
    ultra: QualitySettings
    high: QualitySettings
    medium: QualitySettings
    low: QualitySettings


class CurrentSettings(_StrictModel):
    simulation: SimulationSettings
    pneumatic: PneumaticSettings
    geometry: GeometrySettings
    modes: ModesSettings
    graphics: GraphicsSettings
    animation: AnimationSettings
    physics: PhysicsSettings
    quality_presets: QualityPresets
    diagnostics: DiagnosticsSettings
    system: SystemSettings
    constants: Constants


class AppSettings(_StrictModel):
    metadata: Metadata
    current: CurrentSettings
    defaults_snapshot: CurrentSettings


def dump_settings(settings: AppSettings) -> dict[str, Any]:
    """Return a serialisable dictionary representation of the settings."""

    # NOTE:
    # ``AppSettings`` contains several optional fields (for example the
    # ``decimals``/``units`` metadata in slider ranges) that default to
    # ``None`` when not specified in ``config/app_settings.json``.  When the
    # settings service mutates the model and writes it back to disk we want to
    # preserve the original structure of the JSON file.  Serialising with the
    # default `model_dump` arguments includes these ``None`` values, which would
    # emit explicit ``null`` entries for every optional slider range field.  The
    # JSON Schema enforces concrete types (``integer``/``string``) when the keys
    # are present, so introducing ``null`` values caused schema validation to
    # fail during ``SettingsService.save`` and broke a swath of tests.
    #
    # By excluding ``None`` we serialise only the values that were explicitly
    # defined in the source JSON, keeping the payload compliant with the schema
    # while preserving the existing file layout.
    return settings.model_dump(
        mode="python",
        round_trip=True,
        exclude_none=True,
    )
