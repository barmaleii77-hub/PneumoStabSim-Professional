pragma Singleton
import QtQuick 6.10

QtObject {
    id: root

    readonly property url sourceUrl: Qt.resolvedUrl("../../config/ui_constants.json")
    readonly property var payload: _loadPayload()

    readonly property var panels: ({
        background: _color(_section(payload, "panels", "background"), Qt.rgba(0.06, 0.09, 0.13, 0.92)),
        border: _color(_section(payload, "panels", "border"), Qt.rgba(0.18, 0.24, 0.33, 0.9))
    })

    readonly property var flow: ({
        animation: _flowAnimation(),
        intake: _flowSet("intake", {
            start: Qt.rgba(0.16, 0.44, 0.9, 0.55),
            end: Qt.rgba(0.35, 0.82, 1.0, 0.9),
            tip: Qt.rgba(0.65, 0.98, 1.0, 0.98),
            highlight: Qt.rgba(0.55, 0.9, 1.0, 0.6),
            highlightEnd: Qt.rgba(0.75, 1.0, 1.0, 0.95)
        }),
        exhaust: _flowSet("exhaust", {
            start: Qt.rgba(0.88, 0.36, 0.28, 0.55),
            end: Qt.rgba(0.99, 0.64, 0.38, 0.9),
            tip: Qt.rgba(1.0, 0.76, 0.45, 0.98),
            highlight: Qt.rgba(1.0, 0.75, 0.55, 0.6),
            highlightEnd: Qt.rgba(1.0, 0.9, 0.7, 0.95)
        })
    })

    readonly property var reservoir: ({
        fluidColor: _color(_section(payload, "reservoir", "fluidColor"), Qt.rgba(0.27, 0.6, 0.95, 0.65)),
        surfaceHighlightColor: _color(_section(payload, "reservoir", "surfaceHighlightColor"), Qt.rgba(1, 1, 1, 0.45)),
        borderColor: _color(_section(payload, "reservoir", "borderColor"), Qt.rgba(0.24, 0.31, 0.42, 0.9)),
        atmosphericLineColor: _color(_section(payload, "reservoir", "atmosphericLineColor"), Qt.rgba(0.55, 0.78, 1.0, 0.8)),
        valveOpenColor: _color(_section(payload, "reservoir", "valveOpenColor"), Qt.rgba(0.32, 0.78, 0.48, 0.95)),
        valveClosedColor: _color(_section(payload, "reservoir", "valveClosedColor"), Qt.rgba(0.86, 0.33, 0.33, 0.95)),
        lowPressureColor: _color(_section(payload, "reservoir", "lowPressureColor"), Qt.rgba(0.26, 0.56, 0.94, 0.7)),
        highPressureColor: _color(_section(payload, "reservoir", "highPressureColor"), Qt.rgba(0.94, 0.43, 0.34, 0.85))
    })

    function _loadPayload() {
        try {
            var xhr = new XMLHttpRequest()
            xhr.open("GET", sourceUrl, false)
            xhr.send()
            if (xhr.status === 0 || (xhr.status >= 200 && xhr.status < 300)) {
                return JSON.parse(xhr.responseText)
            }
        } catch (error) {
            console.warn("UiConstants: failed to load JSON", error)
        }
        return {}
    }

    function _section(rootNode, section, key) {
        if (!rootNode || typeof rootNode !== "object")
            return undefined
        var container = rootNode[section]
        if (!container || typeof container !== "object")
            return undefined
        return container[key]
    }

    function _color(value, fallback) {
        if (Array.isArray(value) && value.length >= 3) {
            var alpha = value.length > 3 ? value[3] : 1.0
            return Qt.rgba(value[0], value[1], value[2], alpha)
        }
        if (value !== undefined && value !== null && typeof value === "string")
            return value
        return fallback
    }

    function _flowAnimation() {
        var defaults = { baseMs: 900, speedFactor: 620, minMs: 160, maxMs: 1200, activationThreshold: 0.01 }
        var node = _section(payload, "flow", "animation")
        if (node && typeof node === "object") {
            return {
                baseMs: Number(node.baseMs) || defaults.baseMs,
                speedFactor: Number(node.speedFactor) || defaults.speedFactor,
                minMs: Number(node.minMs) || defaults.minMs,
                maxMs: Number(node.maxMs) || defaults.maxMs,
                activationThreshold: Number(node.activationThreshold) || defaults.activationThreshold
            }
        }
        return defaults
    }

    function _flowSet(key, defaults) {
        var node = _section(payload, "flow", key)
        if (node && typeof node === "object") {
            return {
                start: _color(node.start, defaults.start),
                end: _color(node.end, defaults.end),
                tip: _color(node.tip, defaults.tip),
                highlight: _color(node.highlight, defaults.highlight),
                highlightEnd: _color(node.highlightEnd, defaults.highlightEnd)
            }
        }
        return defaults
    }

    function _mixColor(colorA, colorB, ratio) {
        var clamped = _clamp(ratio)
        return Qt.rgba(
            colorA.r + (colorB.r - colorA.r) * clamped,
            colorA.g + (colorB.g - colorA.g) * clamped,
            colorA.b + (colorB.b - colorA.b) * clamped,
            colorA.a + (colorB.a - colorA.a) * clamped
        )
    }

    function flowPalette(isExhaust, ratio) {
        var target = isExhaust ? flow.exhaust : flow.intake
        return {
            base: _mixColor(target.start, target.end, ratio),
            tip: _mixColor(target.start, target.tip, ratio),
            highlight: _mixColor(target.highlight, target.highlightEnd, ratio)
        }
    }

    function _clamp(value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        if (numeric < 0.0)
            numeric = 0.0
        if (numeric > 1.0)
            numeric = 1.0
        return numeric
    }
}
