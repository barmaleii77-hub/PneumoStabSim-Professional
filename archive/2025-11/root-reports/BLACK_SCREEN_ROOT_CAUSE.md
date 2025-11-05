# Black Screen Investigation Report

## Summary
During scene initialization the `Scene.SuspensionAssembly` component logged a binding loop for its `geometryDefaults` property:

```
QML SuspensionAssembly: Binding loop detected for property "geometryDefaults"
```

The loop prevented the initial geometry snapshot from propagating to the 3D frame, leaving all simulated parts with zero dimensions and rendering the background fully black.

## Root Cause Analysis
- `assets/qml/PneumoStabSim/SimulationRoot.qml` exposed the `geometryDefaults` payload received from Python.
- Inside the same file, the `Scene.SuspensionAssembly` instance declared the binding
  ```qml
  geometryDefaults: geometryDefaults || ({})
  ```
- Within the component scope the identifier `geometryDefaults` referred to the property being assigned, not `root.geometryDefaults`. When the expression evaluated, the binding attempted to read its own target, continuously producing a fallback `{}` object. Qt detected the self-reference and reported a binding loop, leaving the property at the empty fallback.
- With an empty geometry payload the suspension frame collapsed to `0 × 0 × 0 m`, which in turn hid the models and left the View3D background unlit.

## Resolution
1. Introduced a reusable `emptyObject` placeholder on the root item so that fallback bindings reuse the same instance.
2. Updated the suspension assembly binding to explicitly reference `root.geometryDefaults`, ensuring the initial geometry snapshot flows into the component without triggering a self-referential loop.
3. Defaulted the root `geometryDefaults` property to `emptyObject` when the context payload is missing, avoiding repeated allocation of empty maps.

## Verification
- Restart the QML scene and confirm that the binding loop warning no longer appears in the console.
- Observe that the frame initializes with the expected non-zero dimensions, restoring the environment lighting and background rendering.

## Follow-up Recommendations
- Add a lightweight unit or integration check that fails if essential simulation payloads (geometry, materials) resolve to empty dictionaries.
- Consider augmenting the diagnostics overlay to surface binding loop warnings directly to the operator.
