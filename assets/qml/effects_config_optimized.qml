        // --- ОПТИМИЗИРОВАННЫЕ ПОСТ-ЭФФЕКТЫ ---
        effects: [
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
