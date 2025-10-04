from src.ui.custom_geometry import SphereGeometry

s = SphereGeometry()
methods = [m for m in dir(s) if not m.startswith('_') and callable(getattr(s, m))]

print('Available methods:')
for m in sorted(methods):
    print(f'  {m}')

print()
print("Testing key methods:")
try:
    print(f"stride(): {s.stride()}")
except Exception as e:
    print(f"stride() ERROR: {e}")

try:
    print(f"attributeCount(): {s.attributeCount()}")
except Exception as e:
    print(f"attributeCount() ERROR: {e}")

try:
    print(f"primitiveType(): {s.primitiveType()}")
except Exception as e:
    print(f"primitiveType() ERROR: {e}")