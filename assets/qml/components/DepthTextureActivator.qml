pragma Singleton

import QtQuick 6.10

QtObject {
    id: root

    property bool _missingViewLogged: false
    property bool _apiUnavailableLogged: false
    property var _propertyPresenceCache: new Map()
    property var _diagnosticDedup: ({})
    // Guard rails for Qt 6.10+: deprecated toggles such as explicitDepthTextureEnabled
    // no longer exist and must never be invoked. Keeping the list centralised allows
    // runtime to skip them while leaving a breadcrumb for diagnostics.
    readonly property var _legacyDepthProperties: [
        "explicitDepthTextureEnabled",
        "explicitVelocityTextureEnabled",
        "requiresDepthTexture",
        "requiresVelocityTexture"
    ]

    function _clearPropertyCache() {
        if (_propertyPresenceCache && typeof _propertyPresenceCache.clear === "function")
            _propertyPresenceCache.clear()
    }

    function _resetDiagnostics() {
        _clearPropertyCache()
        _diagnosticDedup = ({})
    }

    function _readCachedPresence(target, propertyName) {
        if (!_propertyPresenceCache || !_propertyPresenceCache.has(target))
            return undefined
        var cacheEntry = _propertyPresenceCache.get(target)
        if (!cacheEntry)
            return undefined
        if (Object.prototype.hasOwnProperty.call(cacheEntry, propertyName))
            return cacheEntry[propertyName]
        return undefined
    }

    function _cachePresenceResult(target, propertyName, available) {
        if (!_propertyPresenceCache)
            _propertyPresenceCache = new Map()
        var cacheEntry = _propertyPresenceCache.get(target)
        if (!cacheEntry) {
            cacheEntry = {}
            _propertyPresenceCache.set(target, cacheEntry)
        }
        cacheEntry[propertyName] = available
        return available
    }

    function _logDebugOnce(kind, propertyName, error) {
        var identifier = kind + "::" + (propertyName || "<unknown>") + "::" + String(error)
        if (_diagnosticDedup && _diagnosticDedup[identifier])
            return
        if (!_diagnosticDedup)
            _diagnosticDedup = {}
        _diagnosticDedup[identifier] = true
        if (propertyName)
            console.debug("DepthTextureActivator:", kind, propertyName, error)
        else
            console.debug("DepthTextureActivator:", kind, error)
    }

    function activate(view3d) {
        if (!view3d) {
            if (!_missingViewLogged) {
                console.error("DepthTextureActivator: view3d is null")
                _missingViewLogged = true
            }
            return false
        }

        _resetDiagnostics()

        console.log("🔍 DepthTextureActivator: Activating depth/velocity textures for View3D")

        var activated = false

        activated = prepareRenderSettings(view3d) || activated
        activated = _setViewFlags(view3d) || activated
        activated = _setRenderSettingsFlags(view3d) || activated
        activated = _setEnvironmentFlags(view3d) || activated
        activated = _invokeDepthBufferMethods(view3d) || activated
        activated = _invokeVelocityBufferMethods(view3d) || activated

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
            function () {
                var renderSettings = _safeRead(function () { return view3d.renderSettings })
                return _readProperty(renderSettings, "depthTextureEnabled")
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
        if (_hasProperty(view3d, "velocityTextureEnabled"))
            console.log("  velocityTextureEnabled:", _readProperty(view3d, "velocityTextureEnabled"))

        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        console.log("  renderSettings.depthTextureEnabled:", _readProperty(renderSettings, "depthTextureEnabled"))
        if (_hasProperty(renderSettings, "velocityTextureEnabled"))
            console.log("  renderSettings.velocityTextureEnabled:", _readProperty(renderSettings, "velocityTextureEnabled"))

        var environment = _safeRead(function () { return view3d.environment })
        console.log("  environment.depthTextureEnabled:", _readProperty(environment, "depthTextureEnabled"))
        if (_hasProperty(environment, "velocityTextureEnabled"))
            console.log("  environment.velocityTextureEnabled:", _readProperty(environment, "velocityTextureEnabled"))
        console.log("===========================================")
    }

    function _setViewFlags(view3d) {
        var updated = false
        updated = _trySetProperty(view3d, "depthTextureEnabled", true) || updated
        updated = _trySetProperty(view3d, "velocityTextureEnabled", true) || updated
        updated = _trySetProperty(view3d, "velocityBufferEnabled", true) || updated
        return updated
    }

    function prepareRenderSettings(view3d, renderSettingsOverride) {
        var target = renderSettingsOverride
        if (!target)
            target = _safeRead(function () { return view3d ? view3d.renderSettings : null })
        if (!target)
            return false

        var updated = false
        updated = _trySetProperty(target, "depthTextureEnabled", true) || updated
        updated = _trySetProperty(target, "depthPrePassEnabled", true) || updated
        updated = _trySetProperty(target, "velocityTextureEnabled", true) || updated
        updated = _trySetProperty(target, "velocityBufferEnabled", true) || updated
        updated = _invokeBufferMethod(target, "enableDepthBuffer", "RenderSettings") || updated
        updated = _invokeBufferMethod(target, "enableVelocityBuffer", "RenderSettings") || updated
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

    function _invokeDepthBufferMethods(view3d) {
        if (!view3d)
            return false

        var invoked = false
        invoked = _invokeBufferMethod(view3d, "enableDepthBuffer", "View3D") || invoked

        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        invoked = _invokeBufferMethod(renderSettings, "enableDepthBuffer", "RenderSettings") || invoked

        var environment = _safeRead(function () { return view3d.environment })
        invoked = _invokeBufferMethod(environment, "enableDepthBuffer", "Environment") || invoked

        return invoked
    }

    function _invokeVelocityBufferMethods(view3d) {
        if (!view3d)
            return false

        var invoked = false
        invoked = _invokeBufferMethod(view3d, "enableVelocityBuffer", "View3D") || invoked

        var renderSettings = _safeRead(function () { return view3d.renderSettings })
        invoked = _invokeBufferMethod(renderSettings, "enableVelocityBuffer", "RenderSettings") || invoked

        var environment = _safeRead(function () { return view3d.environment })
        invoked = _invokeBufferMethod(environment, "enableVelocityBuffer", "Environment") || invoked

        return invoked
    }

    function _invokeBufferMethod(target, methodName, label) {
        if (!target)
            return false

        try {
            var method = target[methodName]
            if (typeof method === "function") {
                method.call(target)
                console.log("✅ DepthTextureActivator:", label + "." + methodName + "() called")
                return true
            }
        } catch (error) {
            console.debug("DepthTextureActivator:", label + "." + methodName + "() failed", error)
        }
        return false
    }

    function _hasProperty(target, propertyName) {
        if (!target || !propertyName)
            return false
        var cached = _readCachedPresence(target, propertyName)
        if (cached !== undefined)
            return cached
        try {
            return _cachePresenceResult(target, propertyName, propertyName in target)
        } catch (error) {
            _logDebugOnce("property presence check failed", propertyName, error)
        }
        return _cachePresenceResult(target, propertyName, false)
    }

    function _trySetProperty(target, propertyName, value) {
        if (!target || !propertyName)
            return false

        if (_legacyDepthProperties.indexOf(propertyName) !== -1) {
            _logDebugOnce("legacy property skipped", propertyName, "unsupported depth toggle")
            return false
        }

        if (!_hasProperty(target, propertyName))
            return false

        function logSuccess() {
            console.log("✅ DepthTextureActivator:", propertyName, "=", value)
        }

        try {
            if (target[propertyName] === value)
                return true
        } catch (error) {
            _logDebugOnce("failed to read", propertyName, error)
        }

        try {
            target[propertyName] = value
            if (target[propertyName] === value) {
                logSuccess()
                _cachePresenceResult(target, propertyName, true)
                return true
            }
        } catch (error) {
            _logDebugOnce("failed direct set" + " -> " + value, propertyName, error)
        }

        // qmllint disable missing-property
        try {
            if (typeof target.setProperty === "function" && target.setProperty(propertyName, value)) {
                logSuccess()
                _cachePresenceResult(target, propertyName, true)
                return true
            }
        } catch (error) {
            _logDebugOnce("setProperty fallback failed", propertyName, error)
        }
        // qmllint enable missing-property

        return false
    }

    function _readProperty(target, propertyName) {
        if (!target || !propertyName)
            return undefined

        if (!_hasProperty(target, propertyName))
            return undefined

        try {
            return target[propertyName]
        } catch (error) {
            _logDebugOnce("failed to read", propertyName, error)
        }
        // qmllint disable missing-property
        try {
            if (typeof target.property === "function")
                return target.property(propertyName)
        } catch (error) {
            _logDebugOnce("QObject property lookup failed", propertyName, error)
        }
        // qmllint enable missing-property
        return undefined
    }

    function _safeRead(readFn) {
        try {
            return readFn()
        } catch (error) {
            _logDebugOnce("safe read failed", "", error)
            return null
        }
    }
}
