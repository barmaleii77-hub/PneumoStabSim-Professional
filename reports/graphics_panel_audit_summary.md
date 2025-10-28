# Graphics Panel Audit Summary

## Summary

GraphicsPanel exposes six tabs—lighting, environment, quality, camera, materials, and effects—which map to the major graphics sections of `config/app_settings.json`, but the settings file also contains a `scene` block that has no corresponding UI controls, so those parameters remain inaccessible from the panel.

Environment tab sliders for fog and SSAO use millimetre-scaled ranges (`Near`: 0–200 mm, `Far`: 400–5000 mm, `AO radius`: 0.5–50 mm) that cannot represent the metre-based defaults from the settings file (e.g., `fog_near` = 2.0 m, `fog_far` = 20.0 m, `ao_radius` = 0.008 m); the QML scene expects metre values and converts them with `toSceneLength`, so the current ranges clamp or misreport the real values.

The effects tab’s depth-of-field slider is limited to 200–20 000 (labelled as an unspecified unit) while the stored default is only 2.5 m and the QML environment again expects metre input, so users cannot reproduce the saved focus distance from the panel.

Motion blur and lens flare controls are presented in the effects tab, but the implementation notes they require a custom effect and the QML controller only toggles a boolean without applying the numeric parameters, leaving `motion_blur_amount`, `lens_flare_ghost_count`, and related settings without any runtime effect.

## Testing

⚠️ Tests not run (analysis-only audit).
