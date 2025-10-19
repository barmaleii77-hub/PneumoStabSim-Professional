import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Controls
import "components"
import "core"
import "camera"
import "lighting"
import "scene"
import "geometry"

/*
 * PneumoStabSim - ENHANCED WORKING VERSION
 * ✅ Геометрия, материалы, окружение (IBL), анимация, автообновление
 */
Item {
    id: root
    anchors.fill: parent

    // ===============================================================
    // МОСТ PYTHON → QML (батч-обновления)
    // ===============================================================
    property var pendingPythonUpdates: null
    signal batchUpdatesApplied(var summary)

    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates)
            return;
        try {
            applyBatchedUpdates(pendingPythonUpdates);
        } finally {
            pendingPythonUpdates = null; // очищаем после применения
        }
    }

    function setIfExists(obj, prop, value) {
        try {
            if (obj && (prop in obj || typeof obj[prop] !== 'undefined')) {
                obj[prop] = value;
            }
        } catch (e) { /* ignore */ }
    }

    function applyBatchedUpdates(updates) {
        if (!updates) return;
        var applied = {};
        if (updates.geometry) { applyGeometryUpdates(updates.geometry); applied.geometry = true; }
        if (updates.camera) { applyCameraUpdates(updates.camera); applied.camera = true; }
        if (updates.lighting) { applyLightingUpdates(updates.lighting); applied.lighting = true; }
        if (updates.environment) { applyEnvironmentUpdates(updates.environment); applied.environment = true; }
        if (updates.quality) { applyQualityUpdates(updates.quality); applied.quality = true; }
        if (updates.materials) { applyMaterialUpdates(updates.materials); applied.materials = true; }
        if (updates.effects) { applyEffectsUpdates(updates.effects); applied.effects = true; }
        if (updates.animation) { applyAnimationUpdates(updates.animation); applied.animation = true; }
        batchUpdatesApplied(applied);
        if (updates.geometry && root.autoFitCameraOnGeometryChange)
            fitCameraToModel(true);
    }

    function applyGeometryUpdates(p) {
        if (!p) return;
        setIfExists(root, 'userFrameLength', p.frameLength);
        setIfExists(root, 'userFrameHeight', p.frameHeight);
        setIfExists(root, 'userBeamSize', p.frameBeamSize);
        setIfExists(root, 'userLeverLength', p.leverLength);
        setIfExists(root, 'userCylinderLength', p.cylinderBodyLength);
        setIfExists(root, 'userTrackWidth', p.trackWidth);
        setIfExists(root, 'userFrameToPivot', p.frameToPivot);
        setIfExists(root, 'userRodPosition', p.rodPosition);
        setIfExists(root, 'userBoreHead', p.boreHead);
        setIfExists(root, 'userRodDiameter', p.rodDiameter);
        setIfExists(root, 'userPistonThickness', p.pistonThickness);
        setIfExists(root, 'userPistonRodLength', p.pistonRodLength);
        if (p.cylinderSegments) setIfExists(root, 'cylinderSegments', p.cylinderSegments);
        if (p.cylinderRings) setIfExists(root, 'cylinderRings', p.cylinderRings);
        // Доп. визуальная геометрия
        if (typeof p.tail_rod_length === 'number') root.tailRodLength = p.tail_rod_length;
        if (typeof p.joint_tail_scale === 'number') root.jointTailScale = p.joint_tail_scale;
        if (typeof p.joint_arm_scale === 'number') root.jointArmScale = p.joint_arm_scale;
        if (typeof p.joint_rod_scale === 'number') root.jointRodScale = p.joint_rod_scale;
        // Мировые трансформации модели (опционально)
        if (typeof p.world_pos_x === 'number') root.worldPosX = p.world_pos_x;
        if (typeof p.world_pos_y === 'number') root.worldPosY = p.world_pos_y;
        if (typeof p.world_pos_z === 'number') root.worldPosZ = p.world_pos_z;
        if (typeof p.world_rot_x === 'number') root.worldRotX = p.world_rot_x;
        if (typeof p.world_rot_y === 'number') root.worldRotY = p.world_rot_y;
        if (typeof p.world_rot_z === 'number') root.worldRotZ = p.world_rot_z;
        if (typeof p.world_scale === 'number') root.worldScale = Math.max(0.001, p.world_scale);
    }

    function applyCameraUpdates(p) {
        if (!p) return;
        if (typeof p.fov === 'number') root.cameraFov = p.fov;
        if (typeof p.near === 'number') root.cameraNear = p.near;
        if (typeof p.far === 'number') root.cameraFar = p.far;
        // Синонимы для автоповорота
        if (typeof p.auto_rotate_enabled === 'boolean') root.autoRotateEnabled = p.auto_rotate_enabled;
        if (typeof p.auto_rotate === 'boolean') root.autoRotateEnabled = p.auto_rotate;
        if (typeof p.auto_rotate_speed === 'number') root.autoRotateSpeed = p.auto_rotate_speed;
        // Автофит
        if (typeof p.auto_fit === 'boolean') root.autoFitCameraOnGeometryChange = p.auto_fit;
        if (typeof p.center_camera === 'boolean' && p.center_camera) fitCameraToModel(true);

        // Орбитальные параметры (без ограничений по углам)
        if (typeof p.orbit_target_x === 'number') mouseControls.orbitTarget.x = p.orbit_target_x;
        if (typeof p.orbit_target_y === 'number') mouseControls.orbitTarget.y = p.orbit_target_y;
        if (typeof p.orbit_target_z === 'number') mouseControls.orbitTarget.z = p.orbit_target_z;
        if (typeof p.orbit_yaw === 'number') mouseControls._yawTarget = mouseControls.orbitYaw = p.orbit_yaw;
        if (typeof p.orbit_pitch === 'number') mouseControls._pitchTarget = mouseControls.orbitPitch = p.orbit_pitch;
        if (typeof p.orbit_distance === 'number') mouseControls._distanceTarget = mouseControls.orbitDistance = Math.max(1, Math.min(100000, p.orbit_distance));

        // Плавность/инерция/трение — задаём на root, т.к. логика использует root.*
        if (typeof p.orbit_inertia_enabled === 'boolean') root.inertiaEnabled = p.orbit_inertia_enabled;
        if (typeof p.orbit_inertia === 'number') root.inertia = Math.max(0, Math.min(1, p.orbit_inertia));
        if (typeof p.orbit_rotate_smoothing === 'number') root.rotateSmoothing = Math.max(0, Math.min(1, p.orbit_rotate_smoothing));
        if (typeof p.orbit_pan_smoothing === 'number') root.panSmoothing = Math.max(0, Math.min(1, p.orbit_pan_smoothing));
        if (typeof p.orbit_zoom_smoothing === 'number') root.zoomSmoothing = Math.max(0, Math.min(1, p.orbit_zoom_smoothing));
        if (typeof p.orbit_friction === 'number') root.friction = Math.max(0, Math.min(1, p.orbit_friction));

        // Ручной режим камеры
        if (typeof p.manual_camera === 'boolean') root.manualCameraOverride = p.manual_camera;
        if (root.manualCameraOverride) {
            var camPosChanged = false;
            if (typeof p.camera_pos_x === 'number' || typeof p.camera_pos_y === 'number' || typeof p.camera_pos_z === 'number') {
                var cx = (typeof p.camera_pos_x === 'number') ? p.camera_pos_x : camera.position.x;
                var cy = (typeof p.camera_pos_y === 'number') ? p.camera_pos_y : camera.position.y;
                var cz = (typeof p.camera_pos_z === 'number') ? p.camera_pos_z : camera.position.z;
                camera.position = Qt.vector3d(cx, cy, cz);
                camPosChanged = true;
            }
            if (typeof p.camera_rot_x === 'number' || typeof p.camera_rot_y === 'number' || typeof p.camera_rot_z === 'number') {
                var rx = (typeof p.camera_rot_x === 'number') ? p.camera_rot_x : camera.eulerRotation.x;
                var ry = (typeof p.camera_rot_y === 'number') ? p.camera_rot_y : camera.eulerRotation.y;
                var rz = (typeof p.camera_rot_z === 'number') ? p.camera_rot_z : camera.eulerRotation.z;
                camera.eulerRotation = Qt.vector3d(rx, ry, rz);
            }
            if (camPosChanged) {
                cameraRig.position = mouseControls.orbitTarget;
            }
        }

        // Мировые трансформации модели (разрешаем слать из панели камеры)
        if (typeof p.world_pos_x === 'number') root.worldPosX = p.world_pos_x;
        if (typeof p.world_pos_y === 'number') root.worldPosY = p.world_pos_y;
        if (typeof p.world_pos_z === 'number') root.worldPosZ = p.world_pos_z;
        if (typeof p.world_rot_x === 'number') root.worldRotX = p.world_rot_x;
        if (typeof p.world_rot_y === 'number') root.worldRotY = p.world_rot_y;
        if (typeof p.world_rot_z === 'number') root.worldRotZ = p.world_rot_z;
        if (typeof p.world_scale === 'number') root.worldScale = Math.max(0.001, p.world_scale);
    }

    function applyLightingUpdates(p) {
        if (!p) return;
        function applyDir(lightObj, data) {
            if (!data) return;
            if (typeof data.brightness === 'number') setIfExists(lightObj, 'brightness', data.brightness);
            if (typeof data.color === 'string') setIfExists(lightObj, 'color', data.color);
            if (typeof data.angle_x === 'number') lightObj.eulerRotation.x = data.angle_x;
            if (typeof data.angle_y === 'number') lightObj.eulerRotation.y = data.angle_y;
            if (typeof data.angle_z === 'number') lightObj.eulerRotation.z = data.angle_z;
            if (typeof data.position_x === 'number') lightObj.position.x = data.position_x;
            if (typeof data.position_y === 'number') lightObj.position.y = data.position_y;
            if (typeof data.position_z === 'number') lightObj.position.z = data.position_z;
            if (typeof data.cast_shadow === 'boolean') setIfExists(lightObj, 'castsShadow', data.cast_shadow);
        }
        if (p.key) applyDir(keyLight, p.key);
        if (p.fill) applyDir(fillLight, p.fill);
        if (p.rim) applyDir(rimLight, p.rim);
        if (p.point && pointLight) {
            var d = p.point;
            if (typeof d.brightness === 'number') setIfExists(pointLight, 'brightness', d.brightness);
            if (typeof d.color === 'string') setIfExists(pointLight, 'color', d.color);
            if (typeof d.position_x === 'number') pointLight.position.x = d.position_x;
            if (typeof d.position_y === 'number') pointLight.position.y = d.position_y;
            if (typeof d.position_z === 'number') pointLight.position.z = d.position_z;
            if (typeof d.constant_fade === 'number') setIfExists(pointLight, 'constantFade', d.constant_fade);
            if (typeof d.linear_fade === 'number') setIfExists(pointLight, 'linearFade', d.linear_fade);
            if (typeof d.quadratic_fade === 'number') setIfExists(pointLight, 'quadraticFade', d.quadratic_fade);
            if (typeof d.cast_shadow === 'boolean') setIfExists(pointLight, 'castsShadow', d.cast_shadow);
        }
        if (p.spot && spotLight) {
            var s = p.spot;
            if (typeof s.brightness === 'number') setIfExists(spotLight, 'brightness', s.brightness);
            if (typeof s.color === 'string') setIfExists(spotLight, 'color', s.color);
            if (typeof s.position_x === 'number') spotLight.position.x = s.position_x;
            if (typeof s.position_y === 'number') spotLight.position.y = s.position_y;
            if (typeof s.position_z === 'number') spotLight.position.z = s.position_z;
            if (typeof s.angle_x === 'number') spotLight.eulerRotation.x = s.angle_x;
            if (typeof s.angle_y === 'number') spotLight.eulerRotation.y = s.angle_y;
            if (typeof s.angle_z === 'number') spotLight.eulerRotation.z = s.angle_z;
            if (typeof s.range === 'number') setIfExists(spotLight, 'range', s.range);
            if (typeof s.cone_angle === 'number') setIfExists(spotLight, 'coneAngle', s.cone_angle);
            if (typeof s.inner_cone_angle === 'number') setIfExists(spotLight, 'innerConeAngle', s.inner_cone_angle);
            if (typeof s.cast_shadow === 'boolean') setIfExists(spotLight, 'castsShadow', s.cast_shadow);
        }
    }

    function applyEnvironmentUpdates(p) {
        if (!p) return;
        if (p.background_color) root.backgroundColor = p.background_color;
        if (typeof p.skybox_enabled === 'boolean') {
            if (!p.background_mode) {
                root.backgroundMode = p.skybox_enabled ? SceneEnvironment.SkyBox : SceneEnvironment.Color;
            }
        }
        if (typeof p.ibl_enabled === 'boolean') root.iblLightingEnabled = p.ibl_enabled;
        if (p.background_mode) {
            switch (p.background_mode) {
            case 'color': root.backgroundMode = SceneEnvironment.Color; break;
            case 'skybox': root.backgroundMode = SceneEnvironment.SkyBox; break;
            case 'transparent': root.backgroundMode = SceneEnvironment.Transparent; break;
            }
        }
        if (p.ibl_source) { iblProbe.primarySource = Qt.resolvedUrl(p.ibl_source); }
        if (p.ibl_fallback) { iblProbe.fallbackSource = Qt.resolvedUrl(p.ibl_fallback); }
        if (typeof p.ibl_intensity === 'number') setIfExists(env, 'probeExposure', p.ibl_intensity);
        if (typeof p.ibl_rotation === 'number') setIfExists(env, 'probeOrientation', Qt.vector3d(0, p.ibl_rotation, 0));

        // Туман
        if (typeof p.fog_enabled === 'boolean') setIfExists(env, 'fogEnabled', p.fog_enabled);
        if (p.fog_color) setIfExists(env, 'fogColor', p.fog_color);
        if (typeof p.fog_density === 'number') setIfExists(env, 'fogDensity', p.fog_density);
        if (typeof p.fog_near === 'number') setIfExists(env, 'fogDepthNear', p.fog_near);
        if (typeof p.fog_far === 'number') setIfExists(env, 'fogDepthFar', p.fog_far);

        // SSAO расширенный (если доступно)
        if (typeof p.ao_enabled === 'boolean') setIfExists(env, 'aoEnabled', p.ao_enabled);
        if (typeof p.ao_strength === 'number') setIfExists(env, 'aoStrength', p.ao_strength);
        if (typeof p.ao_radius === 'number') setIfExists(env, 'aoDistance', p.ao_radius);
        if (typeof p.ao_softness === 'number') setIfExists(env, 'aoSoftness', p.ao_softness);
        if (typeof p.ao_dither === 'boolean') setIfExists(env, 'aoDither', p.ao_dither);
        if (typeof p.ao_sample_rate === 'number') setIfExists(env, 'aoSampleRate', p.ao_sample_rate);
    }

    function applyQualityUpdates(p) {
        if (!p) return;
        if (p.antialiasing && p.antialiasing.primary) {
            switch (p.antialiasing.primary) {
            case 'off': env.antialiasingMode = SceneEnvironment.NoAA; break;
            case 'msaa': env.antialiasingMode = SceneEnvironment.MSAA; break;
            case 'ssaa': env.antialiasingMode = SceneEnvironment.SSAA; break;
            }
        }
        if (p.antialiasing && p.antialiasing.quality) {
            switch (p.antialiasing.quality) {
            case 'low': env.antialiasingQuality = SceneEnvironment.Low; break;
            case 'medium': env.antialiasingQuality = SceneEnvironment.Medium; break;
            case 'high': env.antialiasingQuality = SceneEnvironment.High; break;
            }
        }
        if (typeof p.dithering === 'boolean') setIfExists(env, 'ditheringEnabled', p.dithering);
        if (p.shadows && typeof p.shadows.enabled === 'boolean') {
            setIfExists(keyLight, 'castsShadow', p.shadows.enabled);
            setIfExists(fillLight, 'castsShadow', p.shadows.enabled);
            setIfExists(rimLight, 'castsShadow', p.shadows.enabled);
            setIfExists(pointLight, 'castsShadow', p.shadows.enabled);
            setIfExists(spotLight, 'castsShadow', p.shadows.enabled);
        }
        if (p.shadows && typeof p.shadows.resolution === 'string') {
            setIfExists(env, 'shadowMapQuality', p.shadows.resolution);
        }
        if (p.mesh) {
            if (typeof p.mesh.cylinder_segments === 'number') root.cylinderSegments = p.mesh.cylinder_segments;
            if (typeof p.mesh.cylinder_rings === 'number') root.cylinderRings = p.mesh.cylinder_rings;
            if (typeof p.mesh.tail_rod_length === 'number') root.tailRodLength = p.mesh.tail_rod_length;
            if (typeof p.mesh.joint_tail_scale === 'number') root.jointTailScale = p.mesh.joint_tail_scale;
            if (typeof p.mesh.joint_arm_scale === 'number') root.jointArmScale = p.mesh.joint_arm_scale;
            if (typeof p.mesh.joint_rod_scale === 'number') root.jointRodScale = p.mesh.joint_rod_scale;
        }
    }

    function applyMaterialUpdates(p) {
        if (!p) return;
        var key = p.current_material || Object.keys(p)[0];
        var s = p[key];
        if (!s) return;
        var target = null;
        switch (key) {
        case 'frame': target = frameMat; break;
        case 'lever': target = leverMat; break;
        case 'tail': target = tailRodMat; break;
        case 'cylinder': target = cylinderMat; break;
        case 'piston_body': target = pistonBodyMat; break;
        case 'piston_rod': target = pistonRodMat; break;
        case 'joint_tail': target = jointTailMat; break;
        case 'joint_arm': target = jointArmMat; break;
        case 'joint_rod': target = jointRodMat; break;
        default: target = null;
        }
        if (!target) return;
        if (s.base_color) setIfExists(target, 'baseColor', s.base_color);
        if (typeof s.metalness === 'number') setIfExists(target, 'metalness', s.metalness);
        if (typeof s.roughness === 'number') setIfExists(target, 'roughness', s.roughness);
        if (typeof s.specular === 'number') setIfExists(target, 'specularAmount', s.specular);
        if (s.specular_tint) setIfExists(target, 'specularTint', s.specular_tint);
        if (typeof s.opacity === 'number') setIfExists(target, 'opacity', s.opacity);
        if (typeof s.clearcoat === 'number') setIfExists(target, 'clearcoatAmount', s.clearcoat);
        if (typeof s.clearcoat_roughness === 'number') setIfExists(target, 'clearcoatRoughness', s.clearcoat_roughness);
        if (typeof s.ior === 'number') setIfExists(target, 'indexOfRefraction', s.ior);
        if (s.emissive_color) setIfExists(target, 'emissiveColor', s.emissive_color);
        if (typeof s.emissive_intensity === 'number') setIfExists(target, 'emissivePower', s.emissive_intensity);
        if (typeof s.normal_strength === 'number') setIfExists(target, 'normalStrength', s.normal_strength);
        if (typeof s.occlusion_amount === 'number') setIfExists(target, 'occlusionAmount', s.occlusion_amount);
        if (typeof s.alpha_cutoff === 'number') setIfExists(target, 'alphaCutoff', s.alpha_cutoff);
        if (typeof s.transmission === 'number') setIfExists(target, 'transmissionFactor', s.transmission);
        if (typeof s.thickness === 'number') setIfExists(target, 'thicknessFactor', s.thickness);
        if (typeof s.alpha_mode === 'string') {
            switch (s.alpha_mode) {
            case 'default': target.alphaMode = PrincipledMaterial.Default; break;
            case 'mask': target.alphaMode = PrincipledMaterial.Mask; break;
            case 'blend': target.alphaMode = PrincipledMaterial.Blend; break;
            }
        }
    }

    function applyEffectsUpdates(p) {
        if (!p) return;
        if (typeof p.bloom_enabled === 'boolean') setIfExists(env, 'glowEnabled', p.bloom_enabled);
        if (typeof p.bloom_intensity === 'number') setIfExists(env, 'glowIntensity', p.bloom_intensity);
        if (typeof p.bloom_threshold === 'number') setIfExists(env, 'glowHDRMinimumValue', p.bloom_threshold);
        if (typeof p.bloom_spread === 'number') setIfExists(env, 'glowBloom', p.bloom_spread);
        if (typeof p.bloom_glow_strength === 'number') setIfExists(env, 'glowStrength', p.bloom_glow_strength);
        if (typeof p.bloom_hdr_max === 'number') setIfExists(env, 'glowHDRMaximumValue', p.bloom_hdr_max);
        if (typeof p.bloom_hdr_scale === 'number') setIfExists(env, 'glowHDRScale', p.bloom_hdr_scale);
        if (typeof p.bloom_quality_high === 'boolean') setIfExists(env, 'glowQualityHigh', p.bloom_quality_high);
        if (typeof p.bloom_bicubic_upscale === 'boolean') setIfExists(env, 'glowUseBicubicUpscale', p.bloom_bicubic_upscale);
        if (typeof p.tonemap_enabled === 'boolean') setIfExists(env, 'tonemapEnabled', p.tonemap_enabled);
        if (p.tonemap_mode) {
            switch (p.tonemap_mode) {
            case 'filmic': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapFilmic); break;
            case 'aces': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapAces); break;
            case 'reinhard': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapReinhard); break;
            case 'gamma': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapGamma); break;
            case 'linear': setIfExists(env, 'tonemapMode', SceneEnvironment.TonemapLinear); break;
            }
        }
        if (typeof p.tonemap_exposure === 'number') setIfExists(env, 'tonemapExposure', p.tonemap_exposure);
        if (typeof p.tonemap_white_point === 'number') setIfExists(env, 'tonemapWhitePoint', p.tonemap_white_point);
        if (typeof p.depth_of_field === 'boolean') setIfExists(env, 'depthOfFieldEnabled', p.depth_of_field);
        if (typeof p.dof_focus_distance === 'number') setIfExists(env, 'depthOfFieldFocusDistance', p.dof_focus_distance);
        if (typeof p.dof_blur === 'number') setIfExists(env, 'depthOfFieldBlurAmount', p.dof_blur);
        if (typeof p.motion_blur === 'boolean') setIfExists(env, 'motionBlurEnabled', p.motion_blur);
        if (typeof p.motion_blur_amount === 'number') setIfExists(env, 'motionBlurAmount', p.motion_blur_amount);
        if (typeof p.lens_flare === 'boolean') setIfExists(env, 'lensFlareEnabled', p.lens_flare);
        if (typeof p.lens_flare_ghost_count === 'number') setIfExists(env, 'lensFlareGhostCount', p.lens_flare_ghost_count);
        if (typeof p.lens_flare_ghost_dispersal === 'number') setIfExists(env, 'lensFlareGhostDispersal', p.lens_flare_ghost_dispersal);
        if (typeof p.lens_flare_halo_width === 'number') setIfExists(env, 'lensFlareHaloWidth', p.lens_flare_halo_width);
        if (typeof p.lens_flare_bloom_bias === 'number') setIfExists(env, 'lensFlareBloomBias', p.lens_flare_bloom_bias);
        if (typeof p.lens_flare_stretch_to_aspect === 'boolean') setIfExists(env, 'lensFlareStretchToAspect', p.lens_flare_stretch_to_aspect);
        if (typeof p.vignette === 'boolean') setIfExists(env, 'vignetteEnabled', p.vignette);
        if (typeof p.vignette_strength === 'number') setIfExists(env, 'vignetteStrength', p.vignette_strength);
        if (typeof p.vignette_radius === 'number') setIfExists(env, 'vignetteRadius', p.vignette_radius);
        if (typeof p.adjustment_brightness === 'number') setIfExists(env, 'colorAdjustmentBrightness', p.adjustment_brightness);
        if (typeof p.adjustment_contrast === 'number') setIfExists(env, 'colorAdjustmentContrast', p.adjustment_contrast);
        if (typeof p.adjustment_saturation === 'number') setIfExists(env, 'colorAdjustmentSaturation', p.adjustment_saturation);
    }

    // === Анимация: обновления из Python/панелей ===
    function applyAnimationUpdates(params) {
        if (!params) return;
        if (typeof params.amplitude === 'number') root.userAmplitude = params.amplitude;
        if (typeof params.frequency === 'number') root.userFrequency = params.frequency;
        if (typeof params.phase === 'number') root.userPhaseGlobal = params.phase;
        if (typeof params.lf_phase === 'number') root.userPhaseFL = params.lf_phase;
        if (typeof params.rf_phase === 'number') root.userPhaseFR = params.rf_phase;
        if (typeof params.lr_phase === 'number') root.userPhaseRL = params.lr_phase;
        if (typeof params.rr_phase === 'number') root.userPhaseRR = params.rr_phase;
        updateLeverAngles();
    }

    function updatePistonPositions(positions) {
        if (!positions) return;
        if (positions.fl !== undefined) root.userPistonPositionFL = Number(positions.fl);
        if (positions.fr !== undefined) root.userPistonPositionFR = Number(positions.fr);
        if (positions.rl !== undefined) root.userPistonPositionRL = Number(positions.rl);
        if (positions.rr !== undefined) root.userPistonPositionRR = Number(positions.rr);
    }

    // ===============================================================
    // МИНИМАЛЬНЫЕ СВОЙСТВА ДЛЯ СЦЕНЫ
    // ===============================================================

    // Geometry parameters (мм)
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 3200
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600
    property real userFrameToPivot: 600
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200
    // Доп. визуальная геометрия
    property real tailRodLength: 100
    property real jointTailScale: 1.0
    property real jointArmScale: 1.0
    property real jointRodScale: 1.0

    // Camera
    property real cameraFov: 60.0
    property real cameraNear: 10.0
    property real cameraFar: 50000.0

    // Автонастройка камеры (вкл/выкл из UI)
    property bool autoFitCameraOnGeometryChange: false
    // Ручной режим управления камерой
    property bool manualCameraOverride: false

    // Мировые трансформации модели
    property real worldPosX: 0.0
    property real worldPosY: 0.0
    property real worldPosZ: 0.0
    property real worldRotX: 0.0
    property real worldRotY: 0.0
    property real worldRotZ: 0.0
    property real worldScale: 1.0

    // Lighting
    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40

    // ====== MATERIAL PROPS (initial placeholders; overridden from Settings) ======
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    property real frameRoughness: 0.35
    property real frameSpecular: 0.8

    property color leverBaseColor: "#9ea4ab"
    property real leverMetalness: 1.0
    property real leverRoughness: 0.28
    property real leverSpecular: 0.9

    property color cylinderBaseColor: "#e1f5ff"
    property real cylinderOpacity: 0.3
    property real cylinderRoughness: 0.2
    property real cylinderSpecular: 0.6

    property color pistonBodyBaseColor: "#ff3c6e"
    property real pistonBodyMetalness: 1.0
    property real pistonBodyRoughness: 0.26
    property real pistonBodySpecular: 0.9

    property color pistonRodBaseColor: "#ececec"
    property real pistonRodMetalness: 1.0
    property real pistonRodRoughness: 0.18
    property real pistonRodSpecular: 1.0

    property color tailRodBaseColor: "#d5d9df"
    property real tailRodMetalness: 1.0
    property real tailRodRoughness: 0.3
    property real tailRodSpecular: 0.8

    property color jointTailBaseColor: "#2a82ff"
    property real jointTailMetalness: 0.9
    property real jointTailRoughness: 0.35
    property real jointTailSpecular: 0.7

    property color jointArmBaseColor: "#ff9c3a"
    property real jointArmMetalness: 0.9
    property real jointArmRoughness: 0.32
    property real jointArmSpecular: 0.7

    property color jointRodBaseColor: "#00ff55"
    property real jointRodMetalness: 0.9
    property real jointRodRoughness: 0.3
    property real jointRodSpecular: 0.7

    property bool iblLightingEnabled: true
    property bool iblBackgroundEnabled: true
    property real iblRotationDeg: 0.0
    property real iblIntensity: 1.0
    property color backgroundColor: "#1f242c"
    property int backgroundMode: SceneEnvironment.SkyBox

    // Quality
    property bool shadowsEnabled: true
    property string shadowResolution: "2048"
    property int cylinderSegments: 32
    property int cylinderRings: 4

    // Auto-rotate camera
    property bool autoRotateEnabled: false
    property real autoRotateSpeed: 8.0

    // ================================================================
    // CAMERA ORBIT SMOOTHING/INERTIA
    // ================================================================
    property bool inertiaEnabled: false           // вкл/выкл инерции
    property real inertia: 0.25                   // 0..1 — сила инерции
    property real rotateSmoothing: 0.15           // 0..1 — сглаживание поворота
    property real panSmoothing: 0.15              // 0..1 — сглаживание панорамирования
    property real zoomSmoothing: 0.15             // 0..1 — сглаживание зума
    property real friction: 0.08                  // 0..1 — трение (затухание скорости)

    // Текущие и целевые значения орбиты
    property real yawTarget: mouseControls.orbitYaw
    property real pitchTarget: mouseControls.orbitPitch
    property real distanceTarget: mouseControls.orbitDistance
    property vector3d targetTarget: mouseControls.orbitTarget

    // Скорости (для инерции)
    property real yawVelocity: 0.0
    property real pitchVelocity: 0.0
    property real panVX: 0.0
    property real panVY: 0.0
    property real zoomVelocity: 0.0

    // ================================================================
    // АНИМАЦИОННЫЕ СВОЙСТВА (ВЕРНУТЫ ДЛЯ СИГНАЛОВ on*Changed)
    // ================================================================
    property real animationTime: 0.0
    property bool isRunning: false
    property real userAmplitude: 8.0
    property real userFrequency: 1.0
    property real userPhaseGlobal: 0.0
    property real userPhaseFL: 0.0
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0

    property real fl_angle: 0.0
    property real fr_angle: 0.0
    property real rl_angle: 0.0
    property real rr_angle: 0.0

    property real userPistonPositionFL: 250.0
    property real userPistonPositionFR: 250.0
    property real userPistonPositionRL: 250.0
    property real userPistonPositionRR: 250.0

    // ================================================================
    // ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАМЕРЫ
    // ================================================================

    function getModelCenter() {
        return Qt.vector3d(0, root.userBeamSize + root.userFrameHeight / 2.0, 0)
    }

    function getModelRadius() {
        var halfX = Math.max(root.userTrackWidth/2.0, root.userFrameToPivot + root.userLeverLength)
        var halfY = (root.userBeamSize + root.userFrameHeight) * 0.6
        var halfZ = root.userFrameLength/2.0
        var r = Math.sqrt(halfX*halfX + halfY*halfY + halfZ*halfZ)
        return r * 1.05
    }

    function fitCameraToModel(adjustDistance) {
        var center = getModelCenter()
        mouseControls.orbitTarget = center
        targetTarget = center
        if (adjustDistance) {
            var r = getModelRadius()
            var fovRad = (root.cameraFov || 60) * Math.PI / 180.0
            var dist = r / Math.sin(Math.min(Math.PI/3, fovRad/2.0)) + 300
            mouseControls.orbitDistance = Math.max(500, Math.min(30000, dist))
            distanceTarget = mouseControls.orbitDistance
        }
        mouseControls.updateCameraOrbit()
    }

    // ===============================================================
    // MATERIALS - заранее
    // ===============================================================

    PrincipledMaterial { id: leverMat; baseColor: root.leverBaseColor; metalness: root.leverMetalness; roughness: root.leverRoughness; specularAmount: root.leverSpecular }
    PrincipledMaterial { id: tailRodMat; baseColor: root.tailRodBaseColor; metalness: root.tailRodMetalness; roughness: root.tailRodRoughness; specularAmount: root.tailRodSpecular }
    PrincipledMaterial { id: cylinderMat; baseColor: root.cylinderBaseColor; opacity: root.cylinderOpacity; alphaMode: PrincipledMaterial.Blend; roughness: root.cylinderRoughness; specularAmount: root.cylinderSpecular }
    PrincipledMaterial { id: pistonBodyMat; baseColor: root.pistonBodyBaseColor; metalness: root.pistonBodyMetalness; roughness: root.pistonBodyRoughness; specularAmount: root.pistonBodySpecular }
    PrincipledMaterial { id: pistonRodMat; baseColor: root.pistonRodBaseColor; metalness: root.pistonRodMetalness; roughness: root.pistonRodRoughness; specularAmount: root.pistonRodSpecular }
    PrincipledMaterial { id: jointTailMat; baseColor: root.jointTailBaseColor; metalness: root.jointTailMetalness; roughness: root.jointTailRoughness; specularAmount: root.jointTailSpecular }
    PrincipledMaterial { id: jointArmMat; baseColor: root.jointArmBaseColor; metalness: root.jointArmMetalness; roughness: root.jointArmRoughness; specularAmount: root.jointArmSpecular }
    PrincipledMaterial { id: jointRodMat; baseColor: root.jointRodBaseColor; metalness: root.jointRodMetalness; roughness: root.jointRodRoughness; specularAmount: root.jointRodSpecular }
    PrincipledMaterial { id: frameMat; baseColor: root.frameBaseColor; metalness: root.frameMetalness; roughness: root.frameRoughness; specularAmount: root.frameSpecular }

    // ===============================================================
    // VIEW3D - 3D СЦЕНА + IBL PROBE
    // ===============================================================

    IblProbeLoader { id: iblProbe; primarySource: typeof startIblSource !== 'undefined' ? Qt.resolvedUrl(startIblSource) : ""; fallbackSource: typeof startIblFallback !== 'undefined' ? Qt.resolvedUrl(startIblFallback) : "" }

    View3D {
        id: view3d
        anchors.fill: parent

        environment: ExtendedSceneEnvironment {
            id: env
            backgroundMode: root.backgroundMode
            clearColor: root.backgroundColor
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            lightProbe: iblProbe.ready ? iblProbe.probe : null
            probeExposure: root.iblLightingEnabled ? root.iblIntensity : 0.0
            probeOrientation: Qt.vector3d(0, root.iblRotationDeg, 0)
        }

        Node {
            id: worldRoot
            position: Qt.vector3d(root.worldPosX, root.worldPosY, root.worldPosZ)
            eulerRotation: Qt.vector3d(root.worldRotX, root.worldRotY, root.worldRotZ)
            scale: Qt.vector3d(root.worldScale, root.worldScale, root.worldScale)

            Node {
                id: cameraRig
                position: getModelCenter()
                Node {
                    id: yawNode
                    eulerRotation.y: mouseControls.orbitYaw
                    Node {
                        id: pitchNode
                        eulerRotation.x: mouseControls.orbitPitch
                        PerspectiveCamera {
                            id: camera
                            position: Qt.vector3d(0, 0, mouseControls.orbitDistance)
                            fieldOfView: root.cameraFov
                            clipNear: root.cameraNear
                            clipFar: root.cameraFar
                        }
                    }
                }
            }

            DirectionalLight { id: keyLight; eulerRotation.x: root.keyLightAngleX; eulerRotation.y: root.keyLightAngleY; brightness: root.keyLightBrightness; color: root.keyLightColor; castsShadow: root.shadowsEnabled }
            DirectionalLight { id: fillLight; eulerRotation.x: -60; eulerRotation.y: 135; brightness: 0.7; color: "#dfe7ff" }
            DirectionalLight { id: rimLight; eulerRotation.x: 30; eulerRotation.y: -135; brightness: 0.6; color: "#ffe2b0" }
            PointLight { id: pointLight; position: Qt.vector3d(0, 2200, 0); brightness: 0; castsShadow: false }
            SpotLight { id: spotLight; position: Qt.vector3d(0, 2500, 1000); brightness: 0; coneAngle: 45; innerConeAngle: 25; castsShadow: false }

            Frame { id: frameGeometry; worldRoot: worldRoot; beamSize: root.userBeamSize; frameHeight: root.userFrameHeight; frameLength: root.userFrameLength; frameMaterial: frameMat }

            readonly property real pivotZFront: -root.userFrameLength/2 + root.userBeamSize/2
            readonly property real pivotZRear:   root.userFrameLength/2 - root.userBeamSize/2
            function armXLeft()  { return -root.userFrameToPivot }
            function armXRight() { return  root.userFrameToPivot }
            function tailXLeft() { return -root.userTrackWidth/2 }
            function tailXRight(){ return  root.userTrackWidth/2 }

            SuspensionCorner { id: flCorner
                j_arm: Qt.vector3d(worldRoot.armXLeft(), root.userBeamSize, worldRoot.pivotZFront)
                j_tail: Qt.vector3d(worldRoot.tailXLeft(), root.userBeamSize + root.userFrameHeight, worldRoot.pivotZFront)
                leverAngle: root.fl_angle; pistonPositionFromPython: root.userPistonPositionFL
                leverLength: root.userLeverLength; rodPosition: root.userRodPosition; cylinderLength: root.userCylinderLength; boreHead: root.userBoreHead; rodDiameter: root.userRodDiameter; pistonThickness: root.userPistonThickness; pistonRodLength: root.userPistonRodLength; cylinderSegments: root.cylinderSegments; cylinderRings: root.cylinderRings
                tailRodLength: root.tailRodLength; jointTailScale: root.jointTailScale; jointArmScale: root.jointArmScale; jointRodScale: root.jointRodScale
                leverMaterial: leverMat; tailRodMaterial: tailRodMat; cylinderMaterial: cylinderMat; pistonBodyMaterial: pistonBodyMat; pistonRodMaterial: pistonRodMat; jointTailMaterial: jointTailMat; jointArmMaterial: jointArmMat; jointRodMaterial: jointRodMat }
            SuspensionCorner { id: frCorner
                j_arm: Qt.vector3d(worldRoot.armXRight(), root.userBeamSize, worldRoot.pivotZFront)
                j_tail: Qt.vector3d(worldRoot.tailXRight(), root.userBeamSize + root.userFrameHeight, worldRoot.pivotZFront)
                leverAngle: root.fr_angle; pistonPositionFromPython: root.userPistonPositionFR
                leverLength: root.userLeverLength; rodPosition: root.userRodPosition; cylinderLength: root.userCylinderLength; boreHead: root.userBoreHead; rodDiameter: root.userRodDiameter; pistonThickness: root.userPistonThickness; pistonRodLength: root.userPistonRodLength; cylinderSegments: root.cylinderSegments; cylinderRings: root.cylinderRings
                tailRodLength: root.tailRodLength; jointTailScale: root.jointTailScale; jointArmScale: root.jointArmScale; jointRodScale: root.jointRodScale
                leverMaterial: leverMat; tailRodMaterial: tailRodMat; cylinderMaterial: cylinderMat; pistonBodyMaterial: pistonBodyMat; pistonRodMaterial: pistonRodMat; jointTailMaterial: jointTailMat; jointArmMaterial: jointArmMat; jointRodMaterial: jointRodMat }
            SuspensionCorner { id: rlCorner
                j_arm: Qt.vector3d(worldRoot.armXLeft(), root.userBeamSize, worldRoot.pivotZRear)
                j_tail: Qt.vector3d(worldRoot.tailXLeft(), root.userBeamSize + root.userFrameHeight, worldRoot.pivotZRear)
                leverAngle: root.rl_angle; pistonPositionFromPython: root.userPistonPositionRL
                leverLength: root.userLeverLength; rodPosition: root.userRodPosition; cylinderLength: root.userCylinderLength; boreHead: root.userBoreHead; rodDiameter: root.userRodDiameter; pistonThickness: root.userPistonThickness; pistonRodLength: root.userPistonRodLength; cylinderSegments: root.cylinderSegments; cylinderRings: root.cylinderRings
                tailRodLength: root.tailRodLength; jointTailScale: root.jointTailScale; jointArmScale: root.jointArmScale; jointRodScale: root.jointRodScale
                leverMaterial: leverMat; tailRodMaterial: tailRodMat; cylinderMaterial: cylinderMat; pistonBodyMaterial: pistonBodyMat; pistonRodMaterial: pistonRodMat; jointTailMaterial: jointTailMat; jointArmMaterial: jointArmMat; jointRodMaterial: jointRodMat }
            SuspensionCorner { id: rrCorner
                j_arm: Qt.vector3d(worldRoot.armXRight(), root.userBeamSize, worldRoot.pivotZRear)
                j_tail: Qt.vector3d(worldRoot.tailXRight(), root.userBeamSize + root.userFrameHeight, worldRoot.pivotZRear)
                leverAngle: root.rr_angle; pistonPositionFromPython: root.userPistonPositionRR
                leverLength: root.userLeverLength; rodPosition: root.userRodPosition; cylinderLength: root.userCylinderLength; boreHead: root.userBoreHead; rodDiameter: root.userRodDiameter; pistonThickness: root.userPistonThickness; pistonRodLength: root.userPistonRodLength; cylinderSegments: root.cylinderSegments; cylinderRings: root.cylinderRings
                tailRodLength: root.tailRodLength; jointTailScale: root.jointTailScale; jointArmScale: root.jointArmScale; jointRodScale: root.jointRodScale
                leverMaterial: leverMat; tailRodMaterial: tailRodMat; cylinderMaterial: cylinderMat; pistonBodyMaterial: pistonBodyMat; pistonRodMaterial: pistonRodMat; jointTailMaterial: jointTailMat; jointArmMaterial: jointArmMat; jointRodMaterial: jointRodMat }
        }
    }

    // ===============================================================
    // INFO PANEL
    // ===============================================================

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 450
        height: 200
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8
        Column {
            anchors.centerIn: parent
            spacing: 5
            Text { text: "PneumoStabSim - FULL MODEL + ORBIT"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "✅ Frame centered (U-shape, 3 beams)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ 4 Suspension corners (FL, FR, RL, RR)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ IBL loader expects ../hdr/*.hdr relative to assets/qml"; color: "#00ff88"; font.pixelSize: 9 }
            Text { text: "🖱️ Управление: ЛКМ-орбита, ПКМ-панорама, колесо-зум, двойной клик — автофит"; color: "#aaddff"; font.pixelSize: 9 }
        }
    }

    // ===============================================================
    // MOUSE CONTROLS (ОРБИТА)
    // ===============================================================

    MouseArea {
        id: mouseControls
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property real lastX: 0
        property real lastY: 0
        property bool isDragging: false
        property int dragButton: 0
        property real orbitYaw: 30
        property real orbitPitch: -20
        property real orbitDistance: 4000
        property vector3d orbitTarget: getModelCenter()
        property real rotateSpeed: 0.35
        property real panSpeed: 2.0

        // Внутренние целевые значения (плавность/инерция)
        property real _yawTarget: orbitYaw
        property real _pitchTarget: orbitPitch
        property real _distanceTarget: orbitDistance
        property vector3d _targetTarget: orbitTarget

        onPressed: (mouse) => {
            isDragging = true
            dragButton = mouse.button
            lastX = mouse.x
            lastY = mouse.y
            if (mouse.button === Qt.LeftButton) {
                cursorShape = Qt.SizeAllCursor
            } else if (mouse.button === Qt.RightButton) {
                cursorShape = Qt.ClosedHandCursor
            }
        }
        onReleased: { isDragging = false; dragButton = 0; cursorShape = Qt.ArrowCursor }
        onPositionChanged: (mouse) => {
            if (!isDragging || root.manualCameraOverride) return
            var dx = mouse.x - lastX
            var dy = mouse.y - lastY
            if (dragButton === Qt.LeftButton) {
                // Исправлен знак горизонтального вращения (yaw)
                _yawTarget -= dx * rotateSpeed
                _pitchTarget -= dy * rotateSpeed
                if (!root.inertiaEnabled) {
                    orbitYaw = _yawTarget
                    orbitPitch = _pitchTarget
                } else {
                    // Инерция — добавляем скорости (с исправленным знаком для yaw)
                    root.yawVelocity -= dx * rotateSpeed
                    root.pitchVelocity -= dy * rotateSpeed
                }
                updateCameraOrbit()
            } else if (dragButton === Qt.RightButton) {
                var yawRad = orbitYaw * Math.PI / 180
                var right = Qt.vector3d(Math.cos(yawRad), 0, -Math.sin(yawRad))
                var up = Qt.vector3d(0, 1, 0)
                var moveX = -dx * panSpeed
                var moveY = dy * panSpeed
                _targetTarget = Qt.vector3d(
                    orbitTarget.x + right.x * moveX + up.x * moveY,
                    orbitTarget.y + right.y * moveX + up.y * moveY,
                    orbitTarget.z + right.z * moveX + up.z * moveY
                )
                if (!root.inertiaEnabled) {
                    orbitTarget = _targetTarget
                } else {
                    root.panVX += (right.x * moveX + up.x * moveY)
                    root.panVY += (right.y * moveX + up.y * moveY)
                }
                updateCameraOrbit()
            }
            lastX = mouse.x
            lastY = mouse.y
        }
        onWheel: (wheel) => {
            if (root.manualCameraOverride) return
            var delta = wheel.angleDelta.y
            var factor = delta > 0 ? 0.9 : 1.1
            _distanceTarget = Math.max(1, Math.min(100000, orbitDistance * factor))
            if (!root.inertiaEnabled) {
                orbitDistance = _distanceTarget
            } else {
                root.zoomVelocity += (orbitDistance - _distanceTarget)
            }
            updateCameraOrbit()
        }
        onDoubleClicked: fitCameraToModel(true)

        function updateCameraOrbit() {
            cameraRig.position = orbitTarget
            if (root.manualCameraOverride) return
            // Узлы yaw/pitch + позиция по Z
        }

        // Плавное приближение к целям + инерция
        Timer {
            interval: 16
            running: true
            repeat: true
            onTriggered: {
                // Сглаживание без инерции
                if (!root.inertiaEnabled) {
                    // Повороты
                    mouseControls.orbitYaw += (mouseControls._yawTarget - mouseControls.orbitYaw) * root.rotateSmoothing
                    mouseControls.orbitPitch += (mouseControls._pitchTarget - mouseControls.orbitPitch) * root.rotateSmoothing
                    // Панорама
                    mouseControls.orbitTarget = Qt.vector3d(
                        mouseControls.orbitTarget.x + (mouseControls._targetTarget.x - mouseControls.orbitTarget.x) * root.panSmoothing,
                        mouseControls.orbitTarget.y + (mouseControls._targetTarget.y - mouseControls.orbitTarget.y) * root.panSmoothing,
                        mouseControls.orbitTarget.z + (mouseControls._targetTarget.z - mouseControls.orbitTarget.z) * root.panSmoothing
                    )
                    // Зум
                    mouseControls.orbitDistance += (mouseControls._distanceTarget - mouseControls.orbitDistance) * root.zoomSmoothing
                } else {
                    // Инерция: применяем скорости и трение
                    root.yawVelocity *= (1.0 - root.friction)
                    root.pitchVelocity *= (1.0 - root.friction)
                    root.panVX *= (1.0 - root.friction)
                    root.panVY *= (1.0 - root.friction)
                    root.zoomVelocity *= (1.0 - root.friction)

                    mouseControls._yawTarget += root.yawVelocity * root.inertia
                    mouseControls._pitchTarget += root.pitchVelocity * root.inertia

                    mouseControls.orbitYaw += (mouseControls._yawTarget - mouseControls.orbitYaw) * Math.max(0.01, root.rotateSmoothing)
                    mouseControls.orbitPitch += (mouseControls._pitchTarget - mouseControls.orbitPitch) * Math.max(0.01, root.rotateSmoothing)

                    mouseControls.orbitTarget = Qt.vector3d(
                        mouseControls.orbitTarget.x + (mouseControls._targetTarget.x - mouseControls.orbitTarget.x + root.panVX * root.inertia) * Math.max(0.01, root.panSmoothing),
                        mouseControls.orbitTarget.y + (mouseControls._targetTarget.y - mouseControls.orbitTarget.y + root.panVY * root.inertia) * Math.max(0.01, root.panSmoothing),
                        mouseControls.orbitTarget.z + (mouseControls._targetTarget.z - mouseControls.orbitTarget.z) * Math.max(0.01, root.panSmoothing)
                    )
                    mouseControls.orbitDistance += ((mouseControls._distanceTarget - mouseControls.orbitDistance) - root.zoomVelocity * root.inertia) * Math.max(0.01, root.zoomSmoothing)
                }
                mouseControls.updateCameraOrbit()
            }
        }

        Component.onCompleted: { if (root.autoFitCameraOnGeometryChange) fitCameraToModel(true) }
        Timer { interval: 16; running: root.autoRotateEnabled; repeat: true; onTriggered: { mouseControls._yawTarget += (root.autoRotateSpeed / 60.0); mouseControls.updateCameraOrbit() } }
    }

    // ===============================================================
    // АНИМАЦИЯ РЫЧАГОВ
    // ===============================================================

    function updateLeverAngles() {
        var t = root.animationTime
        var A = root.userAmplitude
        var w = 2.0 * Math.PI * root.userFrequency
        var g = root.userPhaseGlobal * Math.PI / 180
        fl_angle = A * Math.sin(w * t + g + root.userPhaseFL * Math.PI / 180)
        fr_angle = A * Math.sin(w * t + g + root.userPhaseFR * Math.PI / 180)
        rl_angle = A * Math.sin(w * t + g + root.userPhaseRL * Math.PI / 180)
        rr_angle = A * Math.sin(w * t + g + root.userPhaseRR * Math.PI / 180)
    }

    onAnimationTimeChanged: if (isRunning) updateLeverAngles()
    onUserAmplitudeChanged: updateLeverAngles()
    onUserFrequencyChanged: updateLeverAngles()
    onUserPhaseGlobalChanged: updateLeverAngles()
    onUserPhaseFLChanged: updateLeverAngles()
    onUserPhaseFRChanged: updateLeverAngles()
    onUserPhaseRLChanged: updateLeverAngles()
    onUserPhaseRRChanged: updateLeverAngles()

    Component.onCompleted: {
        console.log("=".repeat(60))
        console.log("🚀 FULL MODEL LOADED - MODULAR ARCHITECTURE + IBL (centered) + extended controls + orbit smoothing")
        console.log("=".repeat(60))
    }
}
