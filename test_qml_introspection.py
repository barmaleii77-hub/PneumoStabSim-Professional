"""
Test QML root object introspection
Shows all properties and methods available
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl, QMetaObject
from PySide6.QtQuickWidgets import QQuickWidget

app = QApplication(sys.argv)

# Load main.qml
widget = QQuickWidget()
widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

qml_path = Path("assets/qml/main.qml")
qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))

print(f"Loading QML: {qml_url.toString()}")
widget.setSource(qml_url)

if widget.status() == QQuickWidget.Status.Error:
    errors = widget.errors()
    error_msg = "\n".join(str(e) for e in errors)
    print(f"? QML errors:\n{error_msg}")
    sys.exit(1)

root = widget.rootObject()
if not root:
    print("? Failed to get root object!")
    sys.exit(1)

print(f"? Root object obtained: {type(root)}")
print(f"   Class name: {root.__class__.__name__}")

# Introspect properties
meta = root.metaObject()
print(f"\n?? QML Object Properties ({meta.propertyCount()}):")
print("=" * 60)

user_props = []
for i in range(meta.propertyCount()):
    prop = meta.property(i)
    prop_name_bytes = prop.name()
    prop_name = prop_name_bytes.decode('utf-8') if isinstance(prop_name_bytes, bytes) else prop_name_bytes
    
    if prop_name.startswith('user'):
        user_props.append(prop_name)
        value = root.property(prop_name)
        print(f"   ? {prop_name} = {value}")

print(f"\nFound {len(user_props)} user* properties")

# Introspect methods
print(f"\n?? QML Object Methods ({meta.methodCount()}):")
print("=" * 60)

update_methods = []
for i in range(meta.methodCount()):
    method = meta.method(i)
    method_name_bytes = method.name().data()
    method_name = method_name_bytes.decode('utf-8') if isinstance(method_name_bytes, bytes) else method_name_bytes
    
    if 'update' in method_name.lower() or method_name in ['resetView', 'updateAnimation']:
        update_methods.append(method_name)
        print(f"   ? {method_name}()")

print(f"\nFound {len(update_methods)} update* methods")

# Try to get updateGeometry as property
print(f"\n?? Testing updateGeometry access:")
print("=" * 60)

try:
    update_geo = root.property("updateGeometry")
    print(f"   property('updateGeometry'): {update_geo}")
    print(f"   Type: {type(update_geo)}")
    if update_geo:
        print(f"   Is callable: {update_geo.isCallable() if hasattr(update_geo, 'isCallable') else 'N/A'}")
except Exception as e:
    print(f"   ? Error: {e}")

# Try to call it
print(f"\n?? Testing updateGeometry() call:")
print("=" * 60)

try:
    from PySide6.QtQml import QJSValue
    
    update_geo = root.property("updateGeometry")
    if update_geo and hasattr(update_geo, 'isCallable') and update_geo.isCallable():
        print("   ? Function is callable!")
        
        # Try calling with test data
        engine = widget.engine()
        test_params = {
            'frameLength': 3000.0,
            'leverLength': 600.0
        }
        js_value = engine.toScriptValue(test_params)
        result = update_geo.call([js_value])
        
        if result.isError():
            print(f"   ? Call error: {result.toString()}")
        else:
            print(f"   ? Call successful!")
    else:
        print("   ? Function not callable or doesn't exist")
        print("   Trying direct method invocation...")
        
        # Try QMetaObject.invokeMethod
        from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QVariant
        
        # Create QVariant with JS object
        test_params_variant = QVariant({"frameLength": 3000.0})
        
        success = QMetaObject.invokeMethod(
            root,
            "updateGeometry",
            Q_ARG("QVariant", test_params_variant)
        )
        print(f"   invokeMethod result: {success}")
        
except Exception as e:
    print(f"   ? Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("?? Introspection complete")
print("=" * 60)

sys.exit(0)
