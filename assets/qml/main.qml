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

    // Универсальный clamp для безопасного приёма числовых значений из Python/UI
    function clamp(value, minValue, maxValue) {
        if (typeof value !== 'number' || !isFinite(value)) {
            return minValue;
        }
        return Math.max(minValue, Math.min(maxValue, value));
    }

    // Конвертация строкового режима тонемаппинга в enum Qt
    function tonemapModeFromString(mode) {
        switch ((mode || '').toLowerCase()) {
        case 'filmic':
            return SceneEnvironment.TonemapModeFilmic;
        case 'aces':
            return SceneEnvironment.TonemapModeAces;
        case 'reinhard':
            return SceneEnvironment.TonemapModeReinhard;
        case 'gamma':
            return SceneEnvironment.TonemapModeGamma;
        case 'linear':
            return SceneEnvironment.TonemapModeLinear;
        case 'none':
            return SceneEnvironment.TonemapModeNone;
        default:
            return SceneEnvironment.TonemapModeFilmic;
        }
    }

    // Конвертация строкового режима фона в enum Qt
    function backgroundModeFromString(mode) {
        switch ((mode || '').toLowerCase()) {
        case 'color':
            return SceneEnvironment.Color;
        case 'transparent':
            return SceneEnvironment.Transparent;
        default:
            return SceneEnvironment.SkyBox;
        }
    }

    function alphaModeFromString(mode) {
        switch ((mode || '').toLowerCase()) {
        case 'mask':
            return PrincipledMaterial.Mask;
        case 'blend':
            return PrincipledMaterial.Blend;
        default:
            return PrincipledMaterial.Default;
        }
    }

    // Нормализация и резолв путей для IBL источников
    function normalizeSourcePath(value) {
        if (value === undefined || value === null)
            return "";
        var str = String(value);
        return str.trim();
    }

    function resolveIblUrl(path) {
        var normalized = normalizeSourcePath(path);
        if (!normalized)
            return "";
        try {
            return Qt.resolvedUrl(normalized);
        } catch (err) {
            console.warn("⚠️ Не удалось разрешить путь IBL:", normalized, err);
            return "";
        }
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

        function resolveColor(value) {
            if (value === undefined || value === null)
                return null;
            if (typeof value === 'string')
                return value;
            if (typeof value === 'object' && value.r !== undefined && value.g !== undefined && value.b !== undefined) {
                var a = (value.a === undefined) ? 1.0 : clamp(value.a, 0.0, 1.0);
                return Qt.rgba(clamp(value.r, 0.0, 1.0), clamp(value.g, 0.0, 1.0), clamp(value.b, 0.0, 1.0), a);
            }
            return null;
        }

        function applyDir(lightObj, data) {
            if (!data) return;
            var prefix = '';
            if (lightObj === keyLight) {
                prefix = 'key';
            } else if (lightObj === fillLight) {
                prefix = 'fill';
            } else if (lightObj === rimLight) {
                prefix = 'rim';
            }
            var isKey = prefix === 'key';

            if (typeof data.brightness === 'number' && isFinite(data.brightness)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightBrightness', data.brightness);
                } else {
                    setIfExists(lightObj, 'brightness', data.brightness);
                }
            }

            if (data.color !== undefined) {
                var color = resolveColor(data.color);
                if (color !== null) {
                    if (prefix) {
                        setIfExists(root, prefix + 'LightColor', color);
                    } else {
                        setIfExists(lightObj, 'color', color);
                    }
                }
            }

            if (typeof data.angle_x === 'number' && isFinite(data.angle_x)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightAngleX', data.angle_x);
                } else {
                    lightObj.eulerRotation.x = data.angle_x;
                }
            }

            if (typeof data.angle_y === 'number' && isFinite(data.angle_y)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightAngleY', data.angle_y);
                } else {
                    lightObj.eulerRotation.y = data.angle_y;
                }
            }

            if (typeof data.angle_z === 'number' && isFinite(data.angle_z)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightAngleZ', data.angle_z);
                } else {
                    lightObj.eulerRotation.z = data.angle_z;
                }
            }

            if (typeof data.position_x === 'number' && isFinite(data.position_x)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightPosX', data.position_x);
                } else {
                    lightObj.position.x = data.position_x;
                }
            }
            if (typeof data.position_y === 'number' && isFinite(data.position_y)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightPosY', data.position_y);
                } else {
                    lightObj.position.y = data.position_y;
                }
            }
            if (typeof data.position_z === 'number' && isFinite(data.position_z)) {
                if (prefix) {
                    setIfExists(root, prefix + 'LightPosZ', data.position_z);
                } else {
                    lightObj.position.z = data.position_z;
                }
            }

            if (typeof data.cast_shadow === 'boolean') {
                if (isKey) {
                    root.shadowsEnabled = data.cast_shadow;
                    setIfExists(root, 'keyLightCastShadow', data.cast_shadow);
                } else if (prefix) {
                    setIfExists(root, prefix + 'LightCastShadow', data.cast_shadow);
                } else {
                    setIfExists(lightObj, 'castsShadow', data.cast_shadow);
                }
            }
        }
        if (p.key) applyDir(keyLight, p.key);
        if (p.fill) applyDir(fillLight, p.fill);
        if (p.rim) applyDir(rimLight, p.rim);
        if (p.point && pointLight) {
            var d = p.point;
            if (typeof d.brightness === 'number' && isFinite(d.brightness)) setIfExists(root, 'pointLightBrightness', d.brightness);
            if (d.color !== undefined) {
                var pColor = resolveColor(d.color);
                if (pColor !== null) setIfExists(root, 'pointLightColor', pColor);
            }
            if (typeof d.position_x === 'number' && isFinite(d.position_x)) setIfExists(root, 'pointLightPosX', d.position_x);
            if (typeof d.position_y === 'number' && isFinite(d.position_y)) setIfExists(root, 'pointLightPosY', d.position_y);
            if (typeof d.position_z === 'number' && isFinite(d.position_z)) setIfExists(root, 'pointLightPosZ', d.position_z);
            if (typeof d.constant_fade === 'number' && isFinite(d.constant_fade)) setIfExists(root, 'pointLightConstantFade', d.constant_fade);
            if (typeof d.linear_fade === 'number' && isFinite(d.linear_fade)) setIfExists(root, 'pointLightLinearFade', d.linear_fade);
            if (typeof d.quadratic_fade === 'number' && isFinite(d.quadratic_fade)) setIfExists(root, 'pointLightQuadraticFade', d.quadratic_fade);
            if (typeof d.cast_shadow === 'boolean') setIfExists(root, 'pointLightCastShadow', d.cast_shadow);
        }
        if (p.spot && spotLight) {
            var s = p.spot;
            if (typeof s.brightness === 'number' && isFinite(s.brightness)) setIfExists(root, 'spotLightBrightness', s.brightness);
            if (s.color !== undefined) {
                var sColor = resolveColor(s.color);
                if (sColor !== null) setIfExists(root, 'spotLightColor', sColor);
            }
            if (typeof s.position_x === 'number' && isFinite(s.position_x)) setIfExists(root, 'spotLightPosX', s.position_x);
            if (typeof s.position_y === 'number' && isFinite(s.position_y)) setIfExists(root, 'spotLightPosY', s.position_y);
            if (typeof s.position_z === 'number' && isFinite(s.position_z)) setIfExists(root, 'spotLightPosZ', s.position_z);
            if (typeof s.angle_x === 'number' && isFinite(s.angle_x)) setIfExists(root, 'spotLightAngleX', s.angle_x);
            if (typeof s.angle_y === 'number' && isFinite(s.angle_y)) setIfExists(root, 'spotLightAngleY', s.angle_y);
            if (typeof s.angle_z === 'number' && isFinite(s.angle_z)) setIfExists(root, 'spotLightAngleZ', s.angle_z);
            if (typeof s.range === 'number' && isFinite(s.range)) setIfExists(root, 'spotLightRange', s.range);
            if (typeof s.cone_angle === 'number' && isFinite(s.cone_angle)) setIfExists(root, 'spotLightConeAngle', s.cone_angle);
            if (typeof s.inner_cone_angle === 'number' && isFinite(s.inner_cone_angle)) setIfExists(root, 'spotLightInnerConeAngle', s.inner_cone_angle);
            if (typeof s.cast_shadow === 'boolean') setIfExists(root, 'spotLightCastShadow', s.cast_shadow);
        }
    }

    function applyEnvironmentUpdates(p) {
        if (!p) return;
        if (p.background_color) root.backgroundColor = p.background_color;
        if (typeof p.skybox_enabled === 'boolean') {
            root.iblBackgroundEnabled = p.skybox_enabled;
            if (!p.background_mode) {
                root.backgroundMode = p.skybox_enabled ? SceneEnvironment.SkyBox : SceneEnvironment.Color;
            }
        }
        if (typeof p.ibl_enabled === 'boolean') root.iblLightingEnabled = p.ibl_enabled;
        if (p.background_mode) {
            switch (p.background_mode) {
            case 'color':
                root.backgroundMode = SceneEnvironment.Color;
                root.iblBackgroundEnabled = false;
                break;
            case 'skybox':
                root.backgroundMode = SceneEnvironment.SkyBox;
                root.iblBackgroundEnabled = true;
                break;
            case 'transparent':
                root.backgroundMode = SceneEnvironment.Transparent;
                root.iblBackgroundEnabled = false;
                break;
            }
        }
        // Храним пути источников IBL в свойстве root, реальный url формируется биндингом
        if (Object.prototype.hasOwnProperty.call(p, 'ibl_source')) {
            root.iblPrimarySourceSetting = normalizeSourcePath(p.ibl_source);
        }
        if (Object.prototype.hasOwnProperty.call(p, 'ibl_fallback')) {
            root.iblFallbackSourceSetting = normalizeSourcePath(p.ibl_fallback);
        }
        if (typeof p.ibl_intensity === 'number' && isFinite(p.ibl_intensity)) root.iblIntensity = Math.max(0.0, Math.min(8.0, p.ibl_intensity));
        if (typeof p.probe_brightness === 'number' && isFinite(p.probe_brightness)) root.envProbeBrightness = Math.max(0.0, Math.min(8.0, p.probe_brightness));
        if (typeof p.probe_horizon === 'number' && isFinite(p.probe_horizon)) root.envProbeHorizon = Math.max(-1.0, Math.min(1.0, p.probe_horizon));
        if (typeof p.ibl_rotation === 'number' && isFinite(p.ibl_rotation)) root.iblRotationDeg = Math.max(-1080.0, Math.min(1080.0, p.ibl_rotation));
        if (typeof p.ibl_offset_x === 'number' && isFinite(p.ibl_offset_x)) root.iblOffsetXDeg = Math.max(-180.0, Math.min(180.0, p.ibl_offset_x));
        if (typeof p.ibl_offset_y === 'number' && isFinite(p.ibl_offset_y)) root.iblOffsetYDeg = Math.max(-180.0, Math.min(180.0, p.ibl_offset_y));
        if (typeof p.ibl_bind_to_camera === 'boolean') root.iblBindToCamera = p.ibl_bind_to_camera;
        if (typeof p.skybox_blur === 'number' && isFinite(p.skybox_blur)) root.envSkyboxBlurAmount = Math.max(0.0, Math.min(1.0, p.skybox_blur));

        // Туман
        if (typeof p.fog_enabled === 'boolean') root.fogEnabledSetting = p.fog_enabled;
        if (p.fog_color) root.fogColorSetting = p.fog_color;
        if (typeof p.fog_density === 'number' && isFinite(p.fog_density)) root.fogDensitySetting = Math.max(0.0, Math.min(1.0, p.fog_density));
        if (typeof p.fog_near === 'number' && isFinite(p.fog_near)) root.fogNearSetting = Math.max(0.0, Math.min(200000.0, p.fog_near));
        if (typeof p.fog_far === 'number' && isFinite(p.fog_far)) root.fogFarSetting = Math.max(500.0, Math.min(400000.0, p.fog_far));
        if (typeof p.fog_height_enabled === 'boolean') root.fogHeightEnabledSetting = p.fog_height_enabled;
        if (typeof p.fog_least_intense_y === 'number' && isFinite(p.fog_least_intense_y)) root.fogGroundLevelSetting = Math.max(-100000.0, Math.min(100000.0, p.fog_least_intense_y));
        if (typeof p.fog_most_intense_y === 'number' && isFinite(p.fog_most_intense_y)) root.fogHeightSetting = Math.max(-100000.0, Math.min(100000.0, p.fog_most_intense_y));
        if (typeof p.fog_height_curve === 'number' && isFinite(p.fog_height_curve)) root.fogHeightFalloffSetting = Math.max(0.0, Math.min(4.0, p.fog_height_curve));
        if (typeof p.fog_transmit_enabled === 'boolean') root.fogTransmittanceEnabledSetting = p.fog_transmit_enabled;
        if (typeof p.fog_transmit_curve === 'number' && isFinite(p.fog_transmit_curve)) root.fogTransmittanceFalloffSetting = Math.max(0.0, Math.min(4.0, p.fog_transmit_curve));
        if (root.fogFarSetting < root.fogNearSetting) {
            root.fogFarSetting = root.fogNearSetting;
        }

        // SSAO расширенный (если доступно)
        if (typeof p.ao_enabled === 'boolean') root.aoEnabledSetting = p.ao_enabled;
        if (typeof p.ao_strength === 'number' && isFinite(p.ao_strength)) root.aoStrengthSetting = Math.max(0.0, Math.min(100.0, p.ao_strength));
        if (typeof p.ao_radius === 'number' && isFinite(p.ao_radius)) root.aoRadiusSetting = Math.max(0.5, Math.min(50.0, p.ao_radius));
        if (typeof p.ao_softness === 'number' && isFinite(p.ao_softness)) root.aoSoftnessSetting = Math.max(0.0, Math.min(50.0, p.ao_softness));
        if (typeof p.ao_dither === 'boolean') root.aoDitherSetting = p.ao_dither;
        if (typeof p.ao_sample_rate === 'number' && isFinite(p.ao_sample_rate)) root.aoSampleRateSetting = Math.max(1, Math.min(4, Math.round(p.ao_sample_rate)));
    }

    function updatePostAaState() {
        var post = (root.aaPostMode || "").toLowerCase();
        var wantsTaa = post.indexOf('taa') !== -1;
        var wantsFxaa = post.indexOf('fxaa') !== -1;
        var taaActive = root.taaEnabledSetting && wantsTaa;
        if (taaActive && root.taaMotionAdaptive && root.cameraMovementActive) {
            taaActive = false;
        }
        setIfExists(env, 'temporalAAEnabled', taaActive);
        setIfExists(env, 'temporalAAStrength', Math.max(0.0, Math.min(1.0, root.taaStrengthSetting || 0.0)));
        var fxaaActive = root.fxaaEnabledSetting && wantsFxaa;
        setIfExists(env, 'fxaaEnabled', fxaaActive);
        setIfExists(env, 'specularAAEnabled', !!root.specularAAEnabledSetting);
    }

    onAaPostModeChanged: updatePostAaState()
    onTaaEnabledSettingChanged: updatePostAaState()
    onTaaMotionAdaptiveChanged: updatePostAaState()
    onFxaaEnabledSettingChanged: updatePostAaState()
    onSpecularAAEnabledSettingChanged: updatePostAaState()
    onCameraMovementActiveChanged: updatePostAaState()
    onTaaStrengthSettingChanged: updatePostAaState()

    function applyQualityUpdates(p) {
        if (!p) return;
        console.log("🎨 applyQualityUpdates вызван с параметрами:", JSON.stringify(p));
        
        // ======== ANTIALIASING ========
        // Вариант 1: вложенный объект (новый формат)
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
        if (p.antialiasing && typeof p.antialiasing.post === 'string') {
            root.aaPostMode = p.antialiasing.post.toLowerCase();
        }
        
        // Вариант 2: плоская структура (старый формат GraphicsPanel)
        if (typeof p.antialiasing === 'string') {
            console.log("  → antialiasing (flat):", p.antialiasing);
            switch (p.antialiasing) {
            case 'off': env.antialiasingMode = SceneEnvironment.NoAA; break;
            case 'msaa': env.antialiasingMode = SceneEnvironment.MSAA; break;
            case 'ssaa': env.antialiasingMode = SceneEnvironment.SSAA; break;
            }
        }
        if (typeof p.aa_quality === 'string') {
            console.log("  → aa_quality (flat):", p.aa_quality);
            switch (p.aa_quality) {
            case 'low': env.antialiasingQuality = SceneEnvironment.Low; break;
            case 'medium': env.antialiasingQuality = SceneEnvironment.Medium; break;
            case 'high': env.antialiasingQuality = SceneEnvironment.High; break;
            }
        }
        if (typeof p.aa_post === 'string') {
            root.aaPostMode = p.aa_post.toLowerCase();
        }
        
        // Temporal AA (Qt 6.10)
        if (p.taa_enabled !== undefined) root.taaEnabledSetting = !!p.taa_enabled;
        if (typeof p.taa_strength === 'number' && isFinite(p.taa_strength)) {
            root.taaStrengthSetting = Math.max(0.0, Math.min(1.0, p.taa_strength));
        }
        if (p.taa_motion_adaptive !== undefined) root.taaMotionAdaptive = !!p.taa_motion_adaptive;

        if (p.fxaa_enabled !== undefined) root.fxaaEnabledSetting = !!p.fxaa_enabled;
        if (p.specular_aa !== undefined) root.specularAAEnabledSetting = !!p.specular_aa;

        if (typeof p.dithering === 'boolean') setIfExists(env, 'ditheringEnabled', p.dithering);
        
        // ======== SHADOWS ========
        // Вариант 1: плоская структура (GraphicsPanel)
        if (typeof p.shadows_enabled === 'boolean') {
            console.log("  → shadows_enabled (flat):", p.shadows_enabled);
            root.shadowsEnabled = p.shadows_enabled;
            root.keyLightCastShadow = p.shadows_enabled;
            root.fillLightCastShadow = false;
            root.rimLightCastShadow = false;
            console.log("  ✅ Тени установлены (flat):", p.shadows_enabled);
        }
        
        // Вариант 2: вложенная структура (старый формат)
        if (p.shadows && typeof p.shadows.enabled === 'boolean') {
            console.log("  → shadows.enabled (legacy):", p.shadows.enabled);
            root.shadowsEnabled = p.shadows.enabled;
            root.keyLightCastShadow = p.shadows.enabled;
            console.log("  ✅ Тени установлены (legacy):", p.shadows.enabled);
        }
        if (p.shadows && typeof p.shadows.filter === 'number' && isFinite(p.shadows.filter)) {
            root.shadowFilterSamples = Math.max(1, Math.round(p.shadows.filter));
        }
        if (p.shadows && typeof p.shadows.bias === 'number' && isFinite(p.shadows.bias)) {
            root.shadowBias = Math.max(0.0, p.shadows.bias);
        }
        if (p.shadows && typeof p.shadows.darkness === 'number' && isFinite(p.shadows.darkness)) {
            root.shadowFactor = Math.max(0.0, Math.min(100.0, p.shadows.darkness));
        }
        
        // Качество теней - плоская структура
        if (typeof p.shadow_quality === 'string') {
            console.log("  → shadow_quality (flat):", p.shadow_quality);
            switch (p.shadow_quality) {
            case 'low': env.shadowMapQuality = SceneEnvironment.Low; break;
            case 'medium': env.shadowMapQuality = SceneEnvironment.Medium; break;
            case 'high': env.shadowMapQuality = SceneEnvironment.High; break;
            }
        }
        
        // Качество теней - вложенная структура
        if (p.shadows && typeof p.shadows.resolution === 'string') {
            console.log("  → shadows.resolution (legacy):", p.shadows.resolution);
            switch (p.shadows.resolution) {
            case '512': env.shadowMapQuality = SceneEnvironment.VeryLow; break;
            case '1024': env.shadowMapQuality = SceneEnvironment.Low; break;
            case '2048': env.shadowMapQuality = SceneEnvironment.Medium; break;
            case '4096': env.shadowMapQuality = SceneEnvironment.High; break;
            }
        }
        
        // Мягкость теней
        if (typeof p.shadow_softness === 'number' && isFinite(p.shadow_softness)) {
            console.log("  → shadow_softness:", p.shadow_softness);
            root.shadowFilterSamples = Math.max(1, Math.round(4 + Math.max(0, p.shadow_softness) * 28));
        }
        
        // Прозрачность (Order-Independent Transparency)
        if (typeof p.oit === 'string') {
            switch (p.oit) {
            case 'none': env.transparencyMode = SceneEnvironment.Transparent; break;
            case 'weighted': env.transparencyMode = SceneEnvironment.ScreenSpace; break;
            }
        }

        // Render scale & policy & frame rate limit
        if (typeof p.render_scale === 'number' && isFinite(p.render_scale)) {
            var scale = Math.max(0.1, Math.min(8.0, p.render_scale));
            root.renderScaleSetting = scale;
        }
        if (typeof p.render_policy === 'string') {
            var policy = p.render_policy.toLowerCase();
            if (policy === 'ondemand' || policy === 'always') {
                root.renderPolicySetting = policy;
            }
        }
        if (typeof p.frame_rate_limit === 'number' && isFinite(p.frame_rate_limit)) {
            var fps = Math.max(0.0, Math.min(480.0, p.frame_rate_limit));
            root.frameRateLimitSetting = fps;
        }
        
        // Mesh quality
        if (p.mesh) {
            if (typeof p.mesh.cylinder_segments === 'number') root.cylinderSegments = p.mesh.cylinder_segments;
            if (typeof p.mesh.cylinder_rings === 'number') root.cylinderRings = p.mesh.cylinder_rings;
            if (typeof p.mesh.tail_rod_length === 'number') root.tailRodLength = p.mesh.tail_rod_length;
            if (typeof p.mesh.joint_tail_scale === 'number') root.jointTailScale = p.mesh.joint_tail_scale;
            if (typeof p.mesh.joint_arm_scale === 'number') root.jointArmScale = p.mesh.joint_arm_scale;
            if (typeof p.mesh.joint_rod_scale === 'number') root.jointRodScale = p.mesh.joint_rod_scale;
        }

        updatePostAaState();
    }

    function applyEffectsUpdates(p) {
        if (!p) return;
        console.log("✨ applyEffectsUpdates вызван с параметрами:", JSON.stringify(p));
        try {
            // ======== BLOOM/GLOW ========
            if (typeof p.bloom_enabled === 'boolean') {
                console.log("  → bloom_enabled:", p.bloom_enabled);
                root.bloomEnabledSetting = p.bloom_enabled;
            }
            if (typeof p.bloom_intensity === 'number' && isFinite(p.bloom_intensity)) root.bloomIntensitySetting = clamp(p.bloom_intensity, 0.0, 10.0);
            if (typeof p.bloom_threshold === 'number' && isFinite(p.bloom_threshold)) root.bloomThresholdSetting = clamp(p.bloom_threshold, 0.0, 20.0);
            if (typeof p.bloom_spread === 'number' && isFinite(p.bloom_spread)) root.bloomSpreadSetting = clamp(p.bloom_spread, 0.0, 5.0);
            if (typeof p.bloom_glow_strength === 'number' && isFinite(p.bloom_glow_strength)) root.bloomGlowStrengthSetting = clamp(p.bloom_glow_strength, 0.0, 10.0);
            if (typeof p.bloom_hdr_max === 'number' && isFinite(p.bloom_hdr_max)) root.bloomHdrMaxSetting = clamp(p.bloom_hdr_max, 0.0, 100.0);
            if (typeof p.bloom_hdr_scale === 'number' && isFinite(p.bloom_hdr_scale)) root.bloomHdrScaleSetting = clamp(p.bloom_hdr_scale, 0.0, 10.0);
            if (typeof p.bloom_quality_high === 'boolean') root.bloomQualityHighSetting = p.bloom_quality_high;
            if (typeof p.bloom_bicubic_upscale === 'boolean') root.bloomBicubicUpscaleSetting = p.bloom_bicubic_upscale;
            
            // ======== TONEMAP ========
            // Проверяем ОБА варианта: с enabled и без
            if (typeof p.tonemap_enabled === 'boolean') {
                console.log("  → tonemap_enabled:", p.tonemap_enabled);
                root.tonemapEnabledSetting = p.tonemap_enabled;
            }
            if (typeof p.tonemap_mode === 'string') {
                console.log("  → tonemap_mode:", p.tonemap_mode);
                var tonemapValue = p.tonemap_mode.toLowerCase();
                var knownTonemapModes = ['filmic', 'aces', 'reinhard', 'gamma', 'linear', 'none'];
                if (knownTonemapModes.indexOf(tonemapValue) === -1) {
                    console.warn("  ⚠️ Неизвестный режим тонемаппинга:", p.tonemap_mode);
                }
                root.tonemapModeSetting = tonemapValue;
                if (typeof p.tonemap_enabled !== 'boolean') {
                    root.tonemapEnabledSetting = tonemapValue !== 'none';
                }
            }
            
            if (typeof p.tonemap_exposure === 'number' && isFinite(p.tonemap_exposure)) root.tonemapExposureSetting = clamp(p.tonemap_exposure, 0.0, 10.0);
            if (typeof p.tonemap_white_point === 'number' && isFinite(p.tonemap_white_point)) root.tonemapWhitePointSetting = clamp(p.tonemap_white_point, 0.0, 20.0);
            
            // ======== DEPTH OF FIELD ========
            if (typeof p.depth_of_field === 'boolean') root.depthOfFieldEnabledSetting = p.depth_of_field;
            if (typeof p.dof_focus_distance === 'number' && isFinite(p.dof_focus_distance)) root.dofFocusDistanceSetting = clamp(p.dof_focus_distance, 0.0, 400000.0);
            if (typeof p.dof_blur === 'number' && isFinite(p.dof_blur)) root.dofBlurAmountSetting = clamp(p.dof_blur, 0.0, 100.0);
            
            // ======== LENS FLARE ========
            if (typeof p.lens_flare === 'boolean') root.lensFlareEnabledSetting = p.lens_flare;
            if (typeof p.lens_flare_ghost_count === 'number' && isFinite(p.lens_flare_ghost_count)) root.lensFlareGhostCountSetting = Math.max(0, Math.min(8, Math.round(p.lens_flare_ghost_count)));
            if (typeof p.lens_flare_ghost_dispersal === 'number' && isFinite(p.lens_flare_ghost_dispersal)) root.lensFlareGhostDispersalSetting = clamp(p.lens_flare_ghost_dispersal, 0.0, 5.0);
            if (typeof p.lens_flare_halo_width === 'number' && isFinite(p.lens_flare_halo_width)) root.lensFlareHaloWidthSetting = clamp(p.lens_flare_halo_width, 0.0, 10.0);
            if (typeof p.lens_flare_bloom_bias === 'number' && isFinite(p.lens_flare_bloom_bias)) root.lensFlareBloomBiasSetting = clamp(p.lens_flare_bloom_bias, 0.0, 5.0);
            if (typeof p.lens_flare_stretch_to_aspect === 'boolean') root.lensFlareStretchSetting = p.lens_flare_stretch_to_aspect;
            
            // ======== VIGNETTE ========
            if (typeof p.vignette === 'boolean') {
                console.log("  → vignette:", p.vignette);
                root.vignetteEnabledSetting = p.vignette;
            }
            if (typeof p.vignette_strength === 'number' && isFinite(p.vignette_strength)) {
                console.log("  → vignette_strength:", p.vignette_strength);
                root.vignetteStrengthSetting = clamp(p.vignette_strength, 0.0, 1.0);
            }
            if (typeof p.vignette_radius === 'number' && isFinite(p.vignette_radius)) root.vignetteRadiusSetting = clamp(p.vignette_radius, 0.0, 1.0);
            
            // ======== MOTION BLUR ========
            if (typeof p.motion_blur === 'boolean') root.motionBlurEnabledSetting = p.motion_blur;
            if (typeof p.motion_blur_amount === 'number' && isFinite(p.motion_blur_amount)) root.motionBlurAmountSetting = clamp(p.motion_blur_amount, 0.0, 1.0);
            
            // ======== COLOR ADJUSTMENTS ========
            if (typeof p.adjustment_brightness === 'number' && isFinite(p.adjustment_brightness)) root.adjustmentBrightnessSetting = clamp(p.adjustment_brightness, -10.0, 10.0);
            if (typeof p.adjustment_contrast === 'number' && isFinite(p.adjustment_contrast)) root.adjustmentContrastSetting = clamp(p.adjustment_contrast, -10.0, 10.0);
            if (typeof p.adjustment_saturation === 'number' && isFinite(p.adjustment_saturation)) root.adjustmentSaturationSetting = clamp(p.adjustment_saturation, -10.0, 10.0);
            
            console.log("✅ applyEffectsUpdates завершён успешно");
        } catch (e) {
            console.error("❌ Ошибка в applyEffectsUpdates:", e, e.stack);
        }
    }

    // === Анимация: обновления из Python/панелей ===
    function applyAnimationUpdates(params) {
        if (!params) return;

        function asNumber(value) {
            if (value === undefined || value === null)
                return null;
            var num = Number(value);
            return isFinite(num) ? num : null;
        }

        var amplitude = asNumber(params.amplitude);
        if (amplitude !== null)
            root.userAmplitude = clamp(amplitude, 0.0, 0.2);

        var frequency = asNumber(params.frequency);
        if (frequency !== null)
            root.userFrequency = clamp(frequency, 0.1, 10.0);

        var phase = asNumber(params.phase);
        if (phase !== null)
            root.userPhaseGlobal = clamp(phase, 0.0, 360.0);

        var lfPhase = asNumber(params.lf_phase);
        if (lfPhase !== null)
            root.userPhaseFL = clamp(lfPhase, 0.0, 360.0);

        var rfPhase = asNumber(params.rf_phase);
        if (rfPhase !== null)
            root.userPhaseFR = clamp(rfPhase, 0.0, 360.0);

        var lrPhase = asNumber(params.lr_phase);
        if (lrPhase !== null)
            root.userPhaseRL = clamp(lrPhase, 0.0, 360.0);

        var rrPhase = asNumber(params.rr_phase);
        if (rrPhase !== null)
            root.userPhaseRR = clamp(rrPhase, 0.0, 360.0);

        updateLeverAngles();
    }

    function updatePistonPositions(positions) {
        if (!positions) return;
        if (positions.fl !== undefined) root.userPistonPositionFL = Number(positions.fl);
        if (positions.fr !== undefined) root.userPistonPositionFR = Number(positions.fr);
        if (positions.rl !== undefined) root.userPistonPositionRL = Number(positions.rl);
        if (positions.rr !== undefined) root.userPistonPositionRR = Number(positions.rr);
    }

    // Совместимость: простые update* функции вызывают соответствующие apply*Updates
    function updateGeometry(params) { applyGeometryUpdates(params); }
    function updateCamera(params) { applyCameraUpdates(params); }
    function updateLighting(params) { applyLightingUpdates(params); }
    function updateEnvironment(params) { applyEnvironmentUpdates(params); }
    function updateQuality(params) { applyQualityUpdates(params); }
    function updateMaterials(params) { applyMaterialUpdates(params); }
    function updateEffects(params) { applyEffectsUpdates(params); }
    function updateAnimation(params) { applyAnimationUpdates(params); }
    function applyAnimParamsUpdates(params) { applyAnimationUpdates(params); }
    function updateAnimParams(params) { applyAnimationUpdates(params); }

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
    property real keyLightAngleZ: 0.0
    property real keyLightPosX: 0.0
    property real keyLightPosY: 0.0
    property real keyLightPosZ: 0.0
    property bool keyLightCastShadow: true

    property real fillLightBrightness: 0.7
    property color fillLightColor: "#dfe7ff"
    property real fillLightAngleX: -60
    property real fillLightAngleY: 135
    property real fillLightAngleZ: 0.0
    property real fillLightPosX: 0.0
    property real fillLightPosY: 0.0
    property real fillLightPosZ: 0.0
    property bool fillLightCastShadow: false

    property real rimLightBrightness: 0.6
    property color rimLightColor: "#ffe2b0"
    property real rimLightAngleX: 30
    property real rimLightAngleY: -135
    property real rimLightAngleZ: 0.0
    property real rimLightPosX: 0.0
    property real rimLightPosY: 0.0
    property real rimLightPosZ: 0.0
    property bool rimLightCastShadow: false

    property real pointLightBrightness: 0.0
    property color pointLightColor: "#ffffff"
    property real pointLightPosX: 0.0
    property real pointLightPosY: 2200.0
    property real pointLightPosZ: 0.0
    property real pointLightConstantFade: 1.0
    property real pointLightLinearFade: 0.0
    property real pointLightQuadraticFade: 0.0
    property bool pointLightCastShadow: false

    property real spotLightBrightness: 0.0
    property color spotLightColor: "#ffffff"
    property real spotLightPosX: 0.0
    property real spotLightPosY: 2500.0
    property real spotLightPosZ: 1000.0
    property real spotLightAngleX: 0.0
    property real spotLightAngleY: 0.0
    property real spotLightAngleZ: 0.0
    property real spotLightRange: 0.0
    property real spotLightConeAngle: 45.0
    property real spotLightInnerConeAngle: 25.0
    property bool spotLightCastShadow: false

    // ====== MATERIAL STATE (каждый параметр хранится в структуре для полной трассировки) ======
    // Централизованный список ключей материалов
    readonly property var materialKeys: [
        'frame', 'lever', 'tail', 'cylinder', 'piston_body', 'piston_rod',
        'joint_tail', 'joint_arm', 'joint_rod'
    ]
    property var materialsState: ({
        frame: {
            base_color: "#c53030",
            metalness: 0.85,
            roughness: 0.35,
            specular: 0.8,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        lever: {
            base_color: "#9ea4ab",
            metalness: 1.0,
            roughness: 0.28,
            specular: 0.9,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        tail: {
            base_color: "#d5d9df",
            metalness: 1.0,
            roughness: 0.3,
            specular: 0.8,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        cylinder: {
            base_color: "#e1f5ff",
            metalness: 0.0,
            roughness: 0.2,
            specular: 0.6,
            specular_tint: "#ffffff",
            opacity: 0.3,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "blend",
            alpha_cutoff: 0.0
        },
        piston_body: {
            base_color: "#ff3c6e",
            metalness: 1.0,
            roughness: 0.26,
            specular: 0.9,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        piston_rod: {
            base_color: "#ececec",
            metalness: 1.0,
            roughness: 0.18,
            specular: 1.0,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        joint_tail: {
            base_color: "#2a82ff",
            metalness: 0.9,
            roughness: 0.35,
            specular: 0.7,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        joint_arm: {
            base_color: "#ff9c3a",
            metalness: 0.9,
            roughness: 0.32,
            specular: 0.7,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        },
        joint_rod: {
            base_color: "#00ff55",
            metalness: 0.9,
            roughness: 0.3,
            specular: 0.7,
            specular_tint: "#ffffff",
            opacity: 1.0,
            clearcoat: 0.0,
            clearcoat_roughness: 0.0,
            transmission: 0.0,
            ior: 1.0,
            thickness: 0.0,
            attenuation_distance: 0.0,
            attenuation_color: "#ffffff",
            emissive_color: "#000000",
            emissive_intensity: 0.0,
            normal_strength: 0.0,
            occlusion_amount: 0.0,
            alpha_mode: "default",
            alpha_cutoff: 0.0
        }
    })

    // ====== Окружение/эффекты: стартовые значения из контекста Python (start*) ======
    property color backgroundColor: (typeof startBackgroundColor === 'string' && startBackgroundColor.length)
            ? startBackgroundColor
            : "#1f242c"
    property int backgroundMode: backgroundModeFromString(
            typeof startBackgroundMode === 'string' && startBackgroundMode.length
            ? startBackgroundMode
            : 'skybox')
    property bool iblBackgroundEnabled: typeof startSkyboxEnabled === 'boolean'
            ? startSkyboxEnabled
            : backgroundMode === SceneEnvironment.SkyBox
    property bool iblLightingEnabled: typeof startIblEnabled === 'boolean' ? startIblEnabled : true
    property string iblPrimarySourceSetting: typeof startIblSource === 'string' ? normalizeSourcePath(startIblSource) : ""
    property url iblPrimarySourceUrl: resolveIblUrl(iblPrimarySourceSetting)
    property string iblFallbackSourceSetting: typeof startIblFallback === 'string'
            ? normalizeSourcePath(startIblFallback)
            : (typeof startIblSource === 'string' ? normalizeSourcePath(startIblSource) : "")
    property url iblFallbackSourceUrl: resolveIblUrl(iblFallbackSourceSetting)
    property real iblRotationDeg: (function() {
        var v = Number(startIblRotation);
        return isFinite(v) ? clamp(v, -1080.0, 1080.0) : 0.0;
    })()
    // Управление IBL: привязка к камере и смещения
    property bool iblBindToCamera: typeof startIblBindToCamera === 'boolean' ? startIblBindToCamera : false
    property real iblOffsetXDeg: (function() {
        var v = Number(startIblOffsetX);
        return isFinite(v) ? clamp(v, -180.0, 180.0) : 0.0;
    })()
    property real iblOffsetYDeg: (function() {
        var v = Number(startIblOffsetY);
        return isFinite(v) ? clamp(v, -180.0, 180.0) : 0.0;
    })()
    property real iblIntensity: (function() {
        var v = Number(startIblIntensity);
        return isFinite(v) ? clamp(v, 0.0, 8.0) : 1.0;
    })()
    property real envProbeBrightness: (function() {
        var v = Number(startProbeBrightness);
        return isFinite(v) ? clamp(v, 0.0, 8.0) : 1.0;
    })()
    property real envProbeHorizon: (function() {
        var v = Number(startProbeHorizon);
        return isFinite(v) ? clamp(v, -1.0, 1.0) : 0.0;
    })()
    property real envSkyboxBlurAmount: (function() {
        var v = Number(startSkyboxBlur);
        return isFinite(v) ? clamp(v, 0.0, 1.0) : 0.0;
    })()

    // Fog
    property bool fogEnabledSetting: typeof startFogEnabled === 'boolean' ? startFogEnabled : false
    property color fogColorSetting: (typeof startFogColor === 'string' && startFogColor.length)
            ? startFogColor
            : "#000000"
    property real fogDensitySetting: (function() {
        var v = Number(startFogDensity);
        return isFinite(v) ? clamp(v, 0.0, 1.0) : 0.0;
    })()
    property real fogNearSetting: (function() {
        var v = Number(startFogNear);
        return isFinite(v) ? clamp(v, 0.0, 200000.0) : 0.0;
    })()
    property real fogFarSetting: (function() {
        var v = Number(startFogFar);
        var clamped = isFinite(v) ? clamp(v, 500.0, 400000.0) : 0.0;
        return clamped < fogNearSetting ? fogNearSetting : clamped;
    })()
    property bool fogHeightEnabledSetting: typeof startFogHeightEnabled === 'boolean' ? startFogHeightEnabled : false
    property real fogGroundLevelSetting: (function() {
        var v = Number(startFogLeastY);
        return isFinite(v) ? clamp(v, -100000.0, 100000.0) : 0.0;
    })()
    property real fogHeightSetting: (function() {
        var v = Number(startFogMostY);
        return isFinite(v) ? clamp(v, -100000.0, 100000.0) : 0.0;
    })()
    property real fogHeightFalloffSetting: (function() {
        var v = Number(startFogHeightCurve);
        return isFinite(v) ? clamp(v, 0.0, 4.0) : 0.0;
    })()
    property bool fogTransmittanceEnabledSetting: typeof startFogTransmitEnabled === 'boolean'
            ? startFogTransmitEnabled
            : false
    property real fogTransmittanceFalloffSetting: (function() {
        var v = Number(startFogTransmitCurve);
        return isFinite(v) ? clamp(v, 0.0, 4.0) : 0.0;
    })()

    // AO
    property bool aoEnabledSetting: typeof startAoEnabled === 'boolean' ? startAoEnabled : false
    property real aoStrengthSetting: (function() {
        var v = Number(startAoStrength);
        return isFinite(v) ? clamp(v, 0.0, 100.0) : 0.0;
    })()
    property real aoRadiusSetting: (function() {
        var v = Number(startAoRadius);
        return isFinite(v) ? clamp(v, 0.5, 50.0) : 0.5;
    })()
    property real aoSoftnessSetting: (function() {
        var v = Number(startAoSoftness);
        return isFinite(v) ? clamp(v, 0.0, 50.0) : 0.0;
    })()
    property bool aoDitherSetting: typeof startAoDither === 'boolean' ? startAoDither : false
    property int aoSampleRateSetting: (function() {
        var v = Number(startAoSampleRate);
        return isFinite(v) ? Math.max(1, Math.min(4, Math.round(v))) : 2;
    })()

    // Effects / post-processing state
    property bool bloomEnabledSetting: false
    property real bloomIntensitySetting: 0.0
    property real bloomThresholdSetting: 1.0
    property real bloomSpreadSetting: 0.0
    property real bloomGlowStrengthSetting: 0.0
    property real bloomHdrMaxSetting: 0.0
    property real bloomHdrScaleSetting: 1.0
    property bool bloomQualityHighSetting: false
    property bool bloomBicubicUpscaleSetting: false
    property bool tonemapEnabledSetting: false
    property string tonemapModeSetting: "none"
    property real tonemapExposureSetting: 1.0
    property real tonemapWhitePointSetting: 1.0
    property bool depthOfFieldEnabledSetting: false
    property real dofFocusDistanceSetting: 0.0
    property real dofBlurAmountSetting: 0.0
    property bool lensFlareEnabledSetting: false
    property int lensFlareGhostCountSetting: 0
    property real lensFlareGhostDispersalSetting: 0.0
    property real lensFlareHaloWidthSetting: 0.0
    property real lensFlareBloomBiasSetting: 0.0
    property bool lensFlareStretchSetting: false
    property bool motionBlurEnabledSetting: false
    property real motionBlurAmountSetting: 0.0
    property bool vignetteEnabledSetting: false
    property real vignetteStrengthSetting: 0.0
    property real vignetteRadiusSetting: 0.0
    property real adjustmentBrightnessSetting: 0.0
    property real adjustmentContrastSetting: 0.0
    property real adjustmentSaturationSetting: 0.0

    // Quality
    property bool shadowsEnabled: true
    property string shadowResolution: "2048"
    property int shadowFilterSamples: 16
    property real shadowBias: 0.0
    property real shadowFactor: 75.0
    property string aaPostMode: "off"
    property bool taaEnabledSetting: false
    property real taaStrengthSetting: 0.0
    property bool taaMotionAdaptive: false
    property bool fxaaEnabledSetting: false
    property bool specularAAEnabledSetting: false
    property real renderScaleSetting: 1.0
    property string renderPolicySetting: "always"
    property real frameRateLimitSetting: 0.0
    property bool cameraMovementActive: false
    property int cylinderSegments: 32
    property int cylinderRings: 4

    onShadowsEnabledChanged: {
        if (root.keyLightCastShadow !== root.shadowsEnabled) {
            root.keyLightCastShadow = root.shadowsEnabled;
        }
    }

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

    function emissiveVector(colorValue, intensity) {
        try {
            // Приводим к типу color через Qt.darker(..., 1.0), затем берём компоненты r/g/b
            var c = Qt.darker(colorValue, 1.0);
            var i = (typeof intensity === 'number' && isFinite(intensity)) ? intensity : 0.0;
            return Qt.vector3d(c.r * i, c.g * i, c.b * i, i);
        } catch (e) {
            var ii = (typeof intensity === 'number' && isFinite(intensity)) ? intensity : 0.0;
            return Qt.vector3d(ii, ii, ii, ii);
        }
    }

    PrincipledMaterial {
        id: leverMat
        readonly property var state: root.materialsState.lever
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: tailRodMat
        readonly property var state: root.materialsState.tail
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: cylinderMat
        readonly property var state: root.materialsState.cylinder
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: pistonBodyMat
        readonly property var state: root.materialsState.piston_body
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: pistonRodMat
        readonly property var state: root.materialsState.piston_rod
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: jointTailMat
        readonly property var state: root.materialsState.joint_tail
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: jointArmMat
        readonly property var state: root.materialsState.joint_arm
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: jointRodMat
        readonly property var state: root.materialsState.joint_rod
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }
    PrincipledMaterial {
        id: frameMat
        readonly property var state: root.materialsState.frame
        baseColor: state.base_color
        metalness: state.metalness
        roughness: state.roughness
        specularAmount: state.specular
        specularTint: state.specular_tint
        opacity: state.opacity
        clearcoatAmount: state.clearcoat
        clearcoatRoughness: state.clearcoat_roughness
        transmissionFactor: state.transmission
        indexOfRefraction: state.ior
        thicknessFactor: state.thickness
        attenuationDistance: state.attenuation_distance
        attenuationColor: state.attenuation_color
        emissiveFactor: emissiveVector(state.emissive_color, state.emissive_intensity)
        normalStrength: state.normal_strength
        occlusionAmount: state.occlusion_amount
        alphaMode: alphaModeFromString(state.alpha_mode)
        alphaCutoff: state.alpha_cutoff
    }

    // ===============================================================
    // VIEW3D - 3D СЦЕНА + IBL PROBE
    // ===============================================================

    IblProbeLoader {
        id: iblProbe
        primarySource: root.iblPrimarySourceUrl
        fallbackSource: root.iblFallbackSourceUrl || root.iblPrimarySourceUrl
    }

    View3D {
        id: view3d
        anchors.fill: parent

        environment: ExtendedSceneEnvironment {
            id: env
            // ❌ НЕТ ДЕФОЛТНЫХ ЗНАЧЕНИЙ В QML!
            // ✅ ВСЕ значения устанавливаются ТОЛЬКО из Python через applyBatchedUpdates()
            
            // Только критичные для работы сцены
            backgroundMode: root.backgroundMode
            clearColor: root.backgroundColor
            lightProbe: iblProbe.ready ? iblProbe.probe : null
            probeExposure: root.iblLightingEnabled ? root.iblIntensity : 0.0
            probeBrightness: root.envProbeBrightness
            probeHorizon: root.envProbeHorizon
            skyBoxBlurAmount: root.envSkyboxBlurAmount
            probeOrientation: Qt.vector3d(
                root.iblOffsetXDeg,
                root.iblRotationDeg + (root.iblBindToCamera ? mouseControls.orbitYaw : 0),
                root.iblOffsetYDeg
            )
            fogEnabled: root.fogEnabledSetting
            fogColor: root.fogColorSetting
            fogDensity: root.fogDensitySetting
            fogDepthNear: root.fogNearSetting
            fogDepthFar: root.fogFarSetting
            fogHeightEnabled: root.fogHeightEnabledSetting
            fogGroundLevel: root.fogGroundLevelSetting
            fogHeight: root.fogHeightSetting
            fogHeightFalloff: root.fogHeightFalloffSetting
            fogTransmittanceEnabled: root.fogTransmittanceEnabledSetting
            fogTransmittanceFalloff: root.fogTransmittanceFalloffSetting
            aoEnabled: root.aoEnabledSetting
            aoStrength: root.aoStrengthSetting
            aoDistance: root.aoRadiusSetting
            aoSoftness: root.aoSoftnessSetting
            aoDither: root.aoDitherSetting
            aoSampleRate: root.aoSampleRateSetting
            glowEnabled: root.bloomEnabledSetting
            glowIntensity: root.bloomIntensitySetting
            glowHDRMinimumValue: root.bloomThresholdSetting
            glowBloom: root.bloomSpreadSetting
            glowStrength: root.bloomGlowStrengthSetting
            glowHDRMaximumValue: root.bloomHdrMaxSetting
            glowHDRScale: root.bloomHdrScaleSetting
            glowQualityHigh: root.bloomQualityHighSetting
            glowUseBicubicUpscale: root.bloomBicubicUpscaleSetting
            tonemapMode: root.tonemapEnabledSetting ? tonemapModeFromString(root.tonemapModeSetting) : SceneEnvironment.TonemapModeNone
            exposure: root.tonemapExposureSetting
            whitePoint: root.tonemapWhitePointSetting
            depthOfFieldEnabled: root.depthOfFieldEnabledSetting
            depthOfFieldFocusDistance: root.dofFocusDistanceSetting
            depthOfFieldBlurAmount: root.dofBlurAmountSetting
            lensFlareEnabled: root.lensFlareEnabledSetting
            lensFlareGhostCount: root.lensFlareGhostCountSetting
            lensFlareGhostDispersal: root.lensFlareGhostDispersalSetting
            lensFlareHaloWidth: root.lensFlareHaloWidthSetting
            lensFlareBloomBias: root.lensFlareBloomBiasSetting
            lensFlareStretchToAspect: root.lensFlareStretchSetting
            motionBlurEnabled: root.motionBlurEnabledSetting
            motionBlurAmount: root.motionBlurAmountSetting
            vignetteEnabled: root.vignetteEnabledSetting
            vignetteStrength: root.vignetteStrengthSetting
            vignetteRadius: root.vignetteRadiusSetting
            adjustmentBrightness: root.adjustmentBrightnessSetting
            adjustmentContrast: root.adjustmentContrastSetting
            adjustmentSaturation: root.adjustmentSaturationSetting
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

            DirectionalLight {
                id: keyLight
                eulerRotation: Qt.vector3d(root.keyLightAngleX, root.keyLightAngleY, root.keyLightAngleZ)
                position: Qt.vector3d(root.keyLightPosX, root.keyLightPosY, root.keyLightPosZ)
                brightness: root.keyLightBrightness
                color: root.keyLightColor
                castsShadow: root.keyLightCastShadow
                shadowFilter: root.shadowFilterSamples
                shadowBias: root.shadowBias
                shadowFactor: root.shadowFactor
            }
            DirectionalLight {
                id: fillLight
                eulerRotation: Qt.vector3d(root.fillLightAngleX, root.fillLightAngleY, root.fillLightAngleZ)
                position: Qt.vector3d(root.fillLightPosX, root.fillLightPosY, root.fillLightPosZ)
                brightness: root.fillLightBrightness
                color: root.fillLightColor
                castsShadow: root.fillLightCastShadow
            }
            DirectionalLight {
                id: rimLight
                eulerRotation: Qt.vector3d(root.rimLightAngleX, root.rimLightAngleY, root.rimLightAngleZ)
                position: Qt.vector3d(root.rimLightPosX, root.rimLightPosY, root.rimLightPosZ)
                brightness: root.rimLightBrightness
                color: root.rimLightColor
                castsShadow: root.rimLightCastShadow
            }
            PointLight {
                id: pointLight
                position: Qt.vector3d(root.pointLightPosX, root.pointLightPosY, root.pointLightPosZ)
                brightness: root.pointLightBrightness
                color: root.pointLightColor
                constantFade: root.pointLightConstantFade
                linearFade: root.pointLightLinearFade
                quadraticFade: root.pointLightQuadraticFade
                castsShadow: root.pointLightCastShadow
            }
            SpotLight {
                id: spotLight
                position: Qt.vector3d(root.spotLightPosX, root.spotLightPosY, root.spotLightPosZ)
                brightness: root.spotLightBrightness
                color: root.spotLightColor
                eulerRotation: Qt.vector3d(root.spotLightAngleX, root.spotLightAngleY, root.spotLightAngleZ)
                range: root.spotLightRange
                coneAngle: root.spotLightConeAngle
                innerConeAngle: root.spotLightInnerConeAngle
                castsShadow: root.spotLightCastShadow
            }

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
            Text { text: "✅ Геометрия в центре (U-образная, 3 балки)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ 4 угла подвески (FL, FR, RL, RR)"; color: "#00ff88"; font.pixelSize: 10 }
            Text { text: "✅ Загрузчик IBL ожидает ../hdr/*.hdr относительно assets/qml"; color: "#00ff88"; font.pixelSize: 9 }
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

                var moving = mouseControls.isDragging || root.autoRotateEnabled ||
                        Math.abs(mouseControls._yawTarget - mouseControls.orbitYaw) > 0.01 ||
                        Math.abs(mouseControls._pitchTarget - mouseControls.orbitPitch) > 0.01 ||
                        Math.abs(mouseControls._distanceTarget - mouseControls.orbitDistance) > 0.5 ||
                        Math.abs(mouseControls._targetTarget.x - mouseControls.orbitTarget.x) > 0.5 ||
                        Math.abs(mouseControls._targetTarget.y - mouseControls.orbitTarget.y) > 0.5 ||
                        Math.abs(mouseControls._targetTarget.z - mouseControls.orbitTarget.z) > 0.5 ||
                        Math.abs(root.panVX) > 0.01 || Math.abs(root.panVY) > 0.01 ||
                        Math.abs(root.zoomVelocity) > 0.01 || Math.abs(root.yawVelocity) > 0.01 ||
                        Math.abs(root.pitchVelocity) > 0.01;
                if (root.cameraMovementActive !== moving) {
                    root.cameraMovementActive = moving;
                }
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

    // Применение стартовых состояний из контекста Python (если заданы)
    function primeInitialStateFromContext() {
        try {
            if (typeof startMaterialsState === 'object' && startMaterialsState)
                applyMaterialUpdates(startMaterialsState);
            if (typeof startLightingState === 'object' && startLightingState)
                applyLightingUpdates(startLightingState);
            if (typeof startQualityState === 'object' && startQualityState)
                applyQualityUpdates(startQualityState);
            if (typeof startEffectsState === 'object' && startEffectsState)
                applyEffectsUpdates(startEffectsState);
            if (typeof startCameraState === 'object' && startCameraState)
                applyCameraUpdates(startCameraState);
        } catch (err) {
            console.error("❌ Ошибка применения стартовых параметров из контекста:", err);
        }
    }

    // Без использования QML-типа RenderSettings — настраиваем программно
    function applyRenderSettings() {
        try {
            var rs = view3d && view3d.renderSettings ? view3d.renderSettings : null;
            if (!rs) return;
            rs.renderScale = root.renderScaleSetting;
            rs.maximumFrameRate = root.frameRateLimitSetting > 0 ? root.frameRateLimitSetting : 0;
            // Числовые значения enum (без зависимости от QML-типа): Always=0, OnDemand=1
            rs.renderPolicy = (root.renderPolicySetting === 'ondemand') ? 1 : 0;
        } catch (e) {
            console.warn('⚠️ applyRenderSettings failed:', e);
        }
    }

    onRenderScaleSettingChanged: applyRenderSettings()
    onRenderPolicySettingChanged: applyRenderSettings()
    onFrameRateLimitSettingChanged: applyRenderSettings()

    Component.onCompleted: {
        primeInitialStateFromContext();
        updatePostAaState();
        applyRenderSettings();
        console.log("=".repeat(60))
        console.log("🚀 FULL MODEL LOADED - MODULAR ARCHITECTURE + IBL (centered) + extended controls + orbit smoothing")
        console.log("=".repeat(60))
    }
}
