# Conditional ditheringEnabled Support (Qt 6.10+)

## Overview
This document describes the implementation of conditional `ditheringEnabled` support in PneumoStabSim, which is only available in Qt 6.10 and later versions.

## Implementation Details

### 1. Qt Version Detection (main.qml)
```qml
// Version detection properties
readonly property var qtVersionParts: Qt.version.split('.')
readonly property int qtMajor: parseInt(qtVersionParts[0])
readonly property int qtMinor: parseInt(qtVersionParts[1])
readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10

// Dithering control
property bool ditheringEnabled: true  // Controlled from GraphicsPanel
readonly property bool canUseDithering: supportsQtQuick3D610Features
```

### 2. Dynamic Property Binding (ExtendedSceneEnvironment)
```qml
environment: ExtendedSceneEnvironment {
    id: mainEnvironment
    // ... other properties ...

    // Conditional activation: ditheringEnabled only available in Qt 6.10+
    Component.onCompleted: {
        if (root.canUseDithering) {
            console.log("✅ Qt 6.10+ detected - enabling ditheringEnabled support")
            mainEnvironment.ditheringEnabled = Qt.binding(function() {
                return root.ditheringEnabled
            })
        } else {
            console.log("⚠️ Qt < 6.10 - ditheringEnabled not available (current version: Qt " + Qt.version + ")")
        }
    }
}
```

### 3. Python-side Detection (app.py)
```python
# Check Qt version for dithering support
from PySide6.QtCore import qVersion
qt_version = qVersion()
major, minor = qt_version.split('.')[:2]
qt_major = int(major)
qt_minor = int(minor)
supports_dithering = qt_major == 6 and qt_minor >= 10

# Log dithering support status
print(f"Dithering support: {'✅ YES (Qt 6.10+)' if supports_dithering else '⚠️ NO (Qt < 6.10)'}")
```

## Benefits

### ✅ Advantages
1. **No Runtime Errors**: Avoids setting unknown properties on older Qt versions
2. **Graceful Degradation**: Application works on Qt 6.8+ without dithering
3. **Future-Proof**: Automatically enables dithering when Qt 6.10+ is detected
4. **User Feedback**: Clear console logging about feature availability
5. **Dynamic**: Uses Qt.binding() for reactive property updates

### 🎯 Compatibility Matrix
| Qt Version | Dithering Support | Status |
|------------|-------------------|---------|
| < 6.8      | ❌ No             | Not tested |
| 6.8 - 6.9  | ❌ No             | Compatible (feature disabled) |
| 6.10+      | ✅ Yes            | Full support |

## User Experience

### Visual Indicators
1. **Info Panel**: Shows Qt version and dithering status
   ```
   🔧 Qt 6.10.1 | Dithering: ✅ Supported
   ```
   or
   ```
   🔧 Qt 6.8.0 | Dithering: ❌ Not available
   ```

2. **Console Logs**: Detailed version information at startup
   ```
   Qt version: 6.10.1 (6.10)
   Dithering support: ✅ YES (Qt 6.10+)
      ✅ ExtendedSceneEnvironment.ditheringEnabled поддерживается
   ```

## Technical Notes

### Why Dynamic Property Binding?
- **Problem**: QML properties must exist at compile time
- **Solution**: Set property dynamically in `Component.onCompleted` after version check
- **Binding**: Use `Qt.binding()` to maintain reactivity with GraphicsPanel

### Alternative Approaches Considered
1. ❌ **Static Property**: Would cause errors on Qt < 6.10
2. ❌ **Property Alias**: Can't be conditional
3. ✅ **Dynamic Binding**: Cleanest solution, no errors, maintains reactivity

## Testing Recommendations

### Test Cases
1. **Qt 6.10+**: Verify dithering toggle works in GraphicsPanel
2. **Qt 6.8-6.9**: Verify no errors, feature gracefully disabled
3. **Version Detection**: Check console logs match actual Qt version
4. **UI Feedback**: Confirm info panel shows correct status

### Expected Console Output (Qt 6.10+)
```
✅ Qt 6.10+ detected - enabling ditheringEnabled support
🔧 Qt Version: 6.10.1
   Qt Major: 6 | Qt Minor: 10
   Dithering support: ✅ YES (Qt 6.10+)
```

### Expected Console Output (Qt < 6.10)
```
⚠️ Qt < 6.10 - ditheringEnabled not available (current version: Qt 6.8.0)
🔧 Qt Version: 6.8.0
   Qt Major: 6 | Qt Minor: 8
   Dithering support: ❌ NO (Qt < 6.10)
```

## Integration with GraphicsPanel

The `ditheringEnabled` property can be controlled from GraphicsPanel like other settings:

```python
# In graphics_panel.py or similar
self.qml_engine.rootObjects()[0].setProperty("ditheringEnabled", True)
```

The QML will automatically check version compatibility and only apply if Qt 6.10+ is detected.

## Conclusion

This implementation provides:
- ✅ Robust version detection
- ✅ Graceful fallback behavior
- ✅ Clear user feedback
- ✅ No breaking changes
- ✅ Future compatibility

The application now works seamlessly across Qt 6.8 - 6.10+ with appropriate feature availability based on the installed Qt version.
