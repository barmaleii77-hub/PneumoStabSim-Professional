import QtQuick 6.10
import QtQuick3D 6.10
import QtQuick3D.Effects 6.10

// Оптимизированная конфигурация пост-эффектов
// Автогенерация: scripts/optimize_effects.py
QtObject {
    id: root

    // Базовые свойства, чтобы qmllint не ругался на dynamic свойства
    property bool bloomEnabled: true
    property real bloomThreshold: 0.7
    property real bloomIntensity: 0.3

    property bool ssaoEnabled: false
    property real ssaoRadius: 2.0
    property real ssaoIntensity: 0.5

    property bool tonemapActive: false
    property int tonemapModeIndex: 0

    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2000
    property real dofFocusRange: 1000

    // --- ОПТИМИЗИРОВАННЫЕ ПОСТ-ЭФФЕКТЫ ---
    property list<Effect> effects: [
        BloomEffect {
            id: bloom
            enabled: root.bloomEnabled
            threshold: root.bloomThreshold || 0.7
            strength: root.bloomIntensity || 0.3
        },
        SSAOEffect {
            id: ssao
            enabled: root.ssaoEnabled
            radius: root.ssaoRadius || 2.0
            strength: root.ssaoIntensity || 0.5
        },
        TonemappingEffect {
            id: tonemap
            enabled: root.tonemapActive
            mode: [
                TonemappingEffect.Mode.None,
                TonemappingEffect.Mode.Linear,
                TonemappingEffect.Mode.Reinhard,
                TonemappingEffect.Mode.Filmic
            ][Math.max(0, Math.min(3, root.tonemapModeIndex || 0))]
        },
        DepthOfFieldEffect {
            id: dof
            enabled: root.depthOfFieldEnabled || false
            focusDistance: root.dofFocusDistance || 2000
            focusRange: root.dofFocusRange || 1000
        }
    ]
}
