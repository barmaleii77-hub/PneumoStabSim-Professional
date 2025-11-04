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
        "focus": HighContrastPalette.focus,
        "accent": HighContrastPalette.accent,
        "accentStrong": HighContrastPalette.accentStrong,
        "textPrimary": HighContrastPalette.textPrimary,
        "textSecondary": HighContrastPalette.textSecondary,
        "textDisabled": HighContrastPalette.textDisabled,
        "warning": HighContrastPalette.warning,
        "success": HighContrastPalette.success,
        "info": HighContrastPalette.info
    })

    readonly property var accessibility: ({
        "role": "theme",
        "contrastRatio": 12.8,
        "shortcuts": [
            {
                "sequence": "Ctrl+Alt+H",
                "description": qsTr("Toggle the high contrast theme")
            }
        ],
        "notes": qsTr("Optimised for WCAG AAA large text contrast requirements.")
    })
}
