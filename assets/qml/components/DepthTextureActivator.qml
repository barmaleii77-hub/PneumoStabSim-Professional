pragma Singleton

import QtQuick 6.10

QtObject {
    id: root

    property bool _missingViewLogged: false
    property bool _apiUnavailableLogged: false

    function activate(view3d) {
        if (!view3d) {
            if (!_missingViewLogged) {
                console.error("DepthTextureActivator: view3d is null")
                _missingViewLogged = true
            }
            return false
        }

        console.log("🔍 DepthTextureActivator: Activating depth/velocity textures for View3D")

        var activated = false
        activated = _setExplicitFlags(view3d) || activated
        activated = _setViewFlags(view3d) || activated
        activated = _setRenderSettingsFlags(view3d) || activated
        activated = _setEnvironmentFlags(view3d) || activated

        var depthAvailable = isDepthAvailable(view3d)
        if (depthAvailable) {
            console.log("🎬 DepthTextureActivator: Depth/velocity textures successfully activated")
            console.log("   This enables GLSL 450 shaders for DOF, SSAO, Fog, Motion Blur")
            _apiUnavailableLogged = false
            return true
        }

        if (activated) {
            console.warn("⚠️ DepthTextureActivator: Properties were toggled but depth textures still report unavailable")
            console.warn("   Verify backend support and ensure effects requesting depth are enabled")
        } else if (!_apiUnavailableLogged) {
            console.warn("⚠️ DepthTextureActivator: Could not explicitly enable depth textures")
            console.warn("   Qt Quick 3D will create them automatically when DOF/SSAO/Fog is enabled")
            console.warn("   Current Qt version may not expose explicit depth controls")
            _apiUnavailableLogged = true
        }

        return false
    }

    function isDepthAvailable(view3d) {
        if (!view3d)
            return false

        var checks = [
            function () { return _readProperty(view3d, "depthTextureEnabled") },
            function () { return _readProperty(view3d, "explicitDepthTextureEnabled") },
            function () {
                var renderSettings = _safeRead(function () { return view3d.renderSettings })
                return _readProperty(renderSettings, "depthTextureEnabled")
            },
            function () {
                var renderSettings = _safeRead(function () { return view3d.renderSettings })
                return _readProperty(renderSettings, "explicitDepthTextureEnabled")
            },
            function () {
                var environment = _safeRead(function () { return view3d.environment })
                return _readProperty(environment, "depthTextureEnabled")
            }
        ]

        for (var i = 0; i < checks.length; ++i) {
            try {
                if (checks[i]())
                    return true
            } catch (error) {
                console.debug("DepthTextureActivator: depth availability check failed", error)
            }
        }
        return false
    }

    function logStatus(view3d) {
        if (!view3d) {
            console.error("DepthTextureActivator: view3d is null")
            return
        }

        console.log("=== DepthTextureActivator Status Report ===")
        console.log("  depthTextureEnabled:", _readProperty(view3d, "depthTextureEnabled"))
        console.log("  explicitDepthTextureEnabled:", _readProperty(view3d, "explicitDepthTextureEnabled"))
        console.log("  velocityTextureEnabled:", _readProperty(view3d, "velocityTextureEnabled"))
        console.log("  explicitVelocityTextureEnabled:", _readProperty(view3d, "explicitVelocityTextureEnabled"))

        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        console.log("  renderSettings.depthTextureEnabled:", _readProperty(renderSettings, "depthTextureEnabled"))
        console.log("  renderSettings.explicitDepthTextureEnabled:", _readProperty(renderSettings, "explicitDepthTextureEnabled"))
        console.log("  renderSettings.velocityTextureEnabled:", _readProperty(renderSettings, "velocityTextureEnabled"))
        console.log("  renderSettings.explicitVelocityTextureEnabled:", _readProperty(renderSettings, "explicitVelocityTextureEnabled"))

        var environment = _safeRead(function () { return view3d.environment })
        console.log("  environment.depthTextureEnabled:", _readProperty(environment, "depthTextureEnabled"))
        console.log("  environment.velocityTextureEnabled:", _readProperty(environment, "velocityTextureEnabled"))
        console.log("===========================================")
    }

    function _setExplicitFlags(view3d) {
        var updated = false
        updated = _invokeEnableBufferMethod(view3d, "enableDepthBuffer", "View3D") || updated
        updated = _invokeEnableBufferMethod(view3d, "enableVelocityBuffer", "View3D") || updated

        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        updated = _invokeEnableBufferMethod(renderSettings, "enableDepthBuffer", "renderSettings") || updated
        updated = _invokeEnableBufferMethod(renderSettings, "enableVelocityBuffer", "renderSettings") || updated

        return updated
    }

    function _setViewFlags(view3d) {
        var updated = false
        updated = _trySetProperty(view3d, "depthTextureEnabled", true) || updated
        updated = _trySetProperty(view3d, "velocityTextureEnabled", true) || updated
        updated = _trySetProperty(view3d, "velocityBufferEnabled", true) || updated
        return updated
    }

    function _setRenderSettingsFlags(view3d) {
        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        if (!renderSettings)
            return false

        var updated = false
        updated = _trySetProperty(renderSettings, "depthTextureEnabled", true) || updated
        updated = _trySetProperty(renderSettings, "depthPrePassEnabled", true) || updated
        updated = _trySetProperty(renderSettings, "velocityTextureEnabled", true) || updated
        updated = _trySetProperty(renderSettings, "velocityBufferEnabled", true) || updated
        return updated
    }

    function _setEnvironmentFlags(view3d) {
        var environment = _safeRead(function () { return view3d.environment })
        if (!environment)
            return false

        var updated = false
        updated = _trySetProperty(environment, "depthTextureEnabled", true) || updated
        updated = _trySetProperty(environment, "velocityTextureEnabled", true) || updated
        updated = _trySetProperty(environment, "velocityBufferEnabled", true) || updated
        return updated
    }

    function _invokeEnableBufferMethod(target, methodName, contextLabel) {
        if (!target)
            return false

        var callable = null
        try {
            callable = target[methodName]
        } catch (error) {
            console.debug("DepthTextureActivator: failed to read method", contextLabel + "." + methodName, error)
            return false
        }

        if (typeof callable !== "function")
            return false

        try {
            var result = callable.call(target)
            console.log("✅ DepthTextureActivator:", contextLabel + "." + methodName + "() invoked", result)
            if (result === undefined)
                return true
            return !!result
        } catch (error) {
            console.debug("DepthTextureActivator:", contextLabel + "." + methodName + "() failed", error)
        }
        return false
    }

    function _trySetProperty(target, propertyName, value) {
        if (!target || !propertyName)
            return false

        function logSuccess() {
            console.log("✅ DepthTextureActivator:", propertyName, "=", value)
        }

        try {
            if (target[propertyName] === value)
                return true
        } catch (error) {
            console.debug("DepthTextureActivator: failed to read", propertyName, error)
        }

        try {
            target[propertyName] = value
            if (target[propertyName] === value) {
                logSuccess()
                return true
            }
        } catch (error) {
            console.debug("DepthTextureActivator: failed direct set", propertyName, "->", value, error)
        }

        // qmllint disable missing-property
        try {
            if (typeof target.setProperty === "function" && target.setProperty(propertyName, value)) {
                logSuccess()
                return true
            }
        } catch (error) {
            console.debug("DepthTextureActivator: setProperty fallback failed", propertyName, error)
        }
        // qmllint enable missing-property

        return false
    }

    function _readProperty(target, propertyName) {
        if (!target || !propertyName)
            return undefined
        try {
            return target[propertyName]
        } catch (error) {
            console.debug("DepthTextureActivator: failed to read", propertyName, error)
        }
        // qmllint disable missing-property
        try {
            if (typeof target.property === "function")
                return target.property(propertyName)
        } catch (error) {
            console.debug("DepthTextureActivator: QObject property lookup failed", propertyName, error)
        }
        // qmllint enable missing-property
        return undefined
    }

    function _safeRead(readFn) {
        try {
            return readFn()
        } catch (error) {
            console.debug("DepthTextureActivator: safe read failed", error)
            return null
        }
    }
}
