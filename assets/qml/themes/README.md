# High Contrast Theme Assets

This directory contains the accessibility-focused high-contrast theme used by
PneumoStabSim. The palette is exposed via QML singletons so QML files can import
`"themes"` and reference `HighContrastPalette`/`HighContrastTheme` directly.

* `HighContrastPalette.qml` — canonical colour definitions that satisfy WCAG
  AA+ contrast requirements for dark backgrounds.
* `HighContrastTheme.qml` — aggregates palette entries and exposes metadata
  (identifier, translated strings, and keyboard shortcut hints) consumed by the
  theme switcher UI.

The metadata intentionally describes the shortcut (`Ctrl+Alt+H`) so automated
accessibility tooling and documentation can surface the interaction without
hard-coding it elsewhere.
