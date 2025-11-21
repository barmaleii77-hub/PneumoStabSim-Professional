// ShaderProfileHelper.js
// Унифицированный помощник профиля/резолвера шейдеров.
// Russian comments with English technical terms.

// Глобальный кэш (shared между эффектами)
var _variantCache = {}
var _statusCache = {}
var _metrics = {
    resolutions: 0,
    cacheHits: 0,
    variantsMissing: 0,
    profileSwitches: 0
}

function metricsSnapshot() {
    // Возвращаем копию для безопасного чтения
    return {
        resolutions: _metrics.resolutions,
        cacheHits: _metrics.cacheHits,
        variantsMissing: _metrics.variantsMissing,
        profileSwitches: _metrics.profileSwitches
    }
}

function resetCaches() {
    _variantCache = {}
    _statusCache = {}
    _metrics.resolutions = 0
    _metrics.cacheHits = 0
    _metrics.variantsMissing = 0
    // profileSwitches не сбрасываем — это сквозная метрика
}

function markProfileSwitch() {
    _metrics.profileSwitches += 1
}

function preferDesktopProfile(forceDesktop, forceGles, normalizedApi, reportedGlesContext, qtRequiresDesktop, graphicsInfo) {
    if (forceGles) return false
    if (forceDesktop) return true
    if (normalizedApi && normalizedApi.length) {
        var condensed = normalizedApi.replace(/[\s_-]+/g, "")
        var spaced = normalizedApi.replace(/[_-]+/g, " ")
        if (normalizedApi.indexOf("angle") !== -1) return false
        if (spaced.indexOf("opengl es") !== -1) return false
        if (condensed.indexOf("opengles") !== -1) return false
        if (condensed.indexOf("gles") !== -1) return false
    }
    try {
        if (typeof qtRequiresDesktop === "boolean")
            return qtRequiresDesktop
    } catch (e) {}
    try {
        if (!reportedGlesContext && graphicsInfo && graphicsInfo.api === graphicsInfo.OpenGL)
            return true
    } catch (e) {}
    if (!graphicsInfo) return true
    return graphicsInfo.api === graphicsInfo.Direct3D11
        || graphicsInfo.api === graphicsInfo.Vulkan
        || graphicsInfo.api === graphicsInfo.Metal
        || graphicsInfo.api === graphicsInfo.Null
}

function candidateNames(baseName, extension, suffixes, normalizedOriginal) {
    var list = [normalizedOriginal]
    if (suffixes && suffixes.length) {
        for (var i = 0; i < suffixes.length; ++i)
            list.push(baseName + suffixes[i] + extension)
        // Fallback-es вариант в конец
        if (suffixes.indexOf("_fallback_es") === -1)
            list.push(baseName + "_fallback_es" + extension)
    }
    return list
}

function resolveVariant(fileName, useGles, preferUnified, desktopSuffixes, glesSuffixes, directories, manifest, existsFn, urlFn, verbose) {
    if (!fileName || typeof fileName !== "string") return ""
    if (_variantCache[fileName]) {
        _metrics.cacheHits += 1
        return _variantCache[fileName]
    }
    var dotIndex = fileName.lastIndexOf('.')
    var baseName = dotIndex >= 0 ? fileName.slice(0, dotIndex) : fileName
    var extension = dotIndex >= 0 ? fileName.slice(dotIndex) : ''
    var suffixes = []
    if (!preferUnified) suffixes = useGles ? glesSuffixes : desktopSuffixes
    var names = candidateNames(baseName, extension, suffixes, fileName)
    if (!directories || !directories.length) directories = [""]
    var selectedName = fileName
    var selectedUrl = urlFn(fileName, directories[0])
    var found = false
    for (var i = 0; i < names.length; ++i) {
        var cname = names[i]
        var suppressErrors = cname === fileName ? false : true
        for (var d = 0; d < directories.length; ++d) {
            var dir = directories[d]
            var curl = urlFn(cname, dir)
            if (existsFn(curl, cname, suppressErrors, manifest)) {
                selectedName = cname
                selectedUrl = curl
                found = true
                break
            }
        }
        if (found) break
        if (useGles && cname !== fileName) {
            _metrics.variantsMissing += 1
        }
    }
    _metrics.resolutions += 1
    _variantCache[fileName] = selectedUrl
    if (verbose) console.log("[ShaderProfileHelper] resolve", fileName, "->", selectedName)
    return selectedUrl
}

// existsFn должна иметь сигнатуру (url, resourceName, suppressErrors, manifest)
// urlFn — (resourceName, directory) → url

function registerStatus(name, status) {
    _statusCache[name] = status
}

function statusSnapshot() {
    var copy = {}
    for (var k in _statusCache) if (Object.prototype.hasOwnProperty.call(_statusCache, k)) copy[k] = _statusCache[k]
    return copy
}

// Публичный API
var ShaderProfileHelper = {
    preferDesktopProfile: preferDesktopProfile,
    resolveVariant: resolveVariant,
    resetCaches: resetCaches,
    markProfileSwitch: markProfileSwitch,
    metricsSnapshot: metricsSnapshot,
    registerStatus: registerStatus,
    statusSnapshot: statusSnapshot
}

// Экспорт
// Использование: import "../components/ShaderProfileHelper.js" as SPH
// SPH.ShaderProfileHelper.resolveVariant(...)

