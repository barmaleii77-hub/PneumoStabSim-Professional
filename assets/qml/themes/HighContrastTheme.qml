pragma Singleton
import QtQuick 6.10
import "./"

QtObject {
    readonly property string identifier: "high-contrast"
    readonly property string displayName: qsTr("High contrast")
    readonly property string description: qsTr("Dark background with vivid accents for accessibility reviews.")

    readonly property var palette: ({
        "window": HighContrastPalette.window,
        "surface": HighContrastPalette.surface,
        "card": HighContrastPalette.card,
        "border": HighContrastPalette.border,
        "outline": HighContrastPalette.outline,
        "focus": HighContrastPalette.focus,
        "focusOutline": HighContrastPalette.focusOutline,
        "accent": HighContrastPalette.accent,
        "accentStrong": HighContrastPalette.accentStrong,
        "accentMuted": HighContrastPalette.accentMuted,
        "textPrimary": HighContrastPalette.textPrimary,
        "textSecondary": HighContrastPalette.textSecondary,
        "textDisabled": HighContrastPalette.textDisabled,
        "selection": HighContrastPalette.selection,
        "selectionText": HighContrastPalette.selectionText,
        "warning": HighContrastPalette.warning,
        "danger": HighContrastPalette.danger,
        "success": HighContrastPalette.success,
        "info": HighContrastPalette.info
    })

    readonly property var widgetAccessibility: ({
        "knob": {
            "role": "dial",
            "label": qsTr("Rotary value selector"),
            "description": qsTr("Use the knob to adjust continuous values with precise keyboard support."),
            "shortcuts": [
                {
                    "sequence": "Ctrl+Alt+Up",
                    "description": qsTr("Increase the current knob value by one step."),
                },
                {
                    "sequence": "Ctrl+Alt+Down",
                    "description": qsTr("Decrease the current knob value by one step."),
                },
                {
                    "sequence": "Ctrl+Alt+0",
                    "description": qsTr("Reset the knob to the midpoint of its range.")
                }
            ]
        },
        "rangeSlider": {
            "role": "range-slider",
            "label": qsTr("Continuous range slider"),
            "description": qsTr("Adjust minimum, maximum, and live values while tracking slider position."),
            "shortcuts": [
                {
                    "sequence": "Ctrl+Alt+Right",
                    "description": qsTr("Increase the slider value by one step."),
                },
                {
                    "sequence": "Ctrl+Alt+Left",
                    "description": qsTr("Decrease the slider value by one step."),
                },
                {
                    "sequence": "Ctrl+Alt+1",
                    "description": qsTr("Move focus to the minimum value field."),
                },
                {
                    "sequence": "Ctrl+Alt+2",
                    "description": qsTr("Move focus to the current value field."),
                },
                {
                    "sequence": "Ctrl+Alt+3",
                    "description": qsTr("Move focus to the maximum value field.")
                }
            ]
        }
    })

    readonly property var accessibility: ({
        "role": "theme",
        "roles": widgetAccessibility,
        "contrastRatio": 12.8,
        "shortcuts": [
            {
                "sequence": "Ctrl+Alt+H",
                "description": qsTr("Toggle the high contrast theme")
            }
        ],
        "notes": qsTr("Optimised for WCAG AAA large text contrast requirements with reinforced focus outlines.")
    })
}
