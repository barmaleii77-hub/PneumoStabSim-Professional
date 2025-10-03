from PySide6 import QtQuick3D
import sys

print("="*80)
print("Qt Quick 3D CAPABILITIES CHECK")
print("="*80)
print()

print("QtQuick3D module members:")
members = [m for m in dir(QtQuick3D) if not m.startswith('_')]
for m in members:
    print(f"  - {m}")

print()
print("="*80)
print("Checking for geometry-related classes:")
print("="*80)

geometry_classes = [
    'QQuick3DGeometry',
    'QQuick3DModel',
    'QQuick3DNode',
    'QQuick3DObject',
]

for cls_name in geometry_classes:
    if hasattr(QtQuick3D, cls_name):
        cls = getattr(QtQuick3D, cls_name)
        print(f"\n{cls_name}:")
        print(f"  Type: {type(cls)}")
        methods = [m for m in dir(cls) if not m.startswith('_')]
        print(f"  Methods: {len(methods)}")
        if cls_name == 'QQuick3DGeometry':
            print("  Key methods:")
            for m in ['addAttribute', 'setVertexData', 'setIndexData', 'setStride', 'setBounds']:
                if m in methods:
                    print(f"    ? {m}")
