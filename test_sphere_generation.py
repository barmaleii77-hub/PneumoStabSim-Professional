from src.ui.custom_geometry import SphereGeometry
import numpy as np

print("=== TESTING SPHERE GEOMETRY GENERATION ===")
print()

# Create geometry
sphere = SphereGeometry()

print("1. Geometry created")
print(f"   Type: {type(sphere)}")
print(f"   Object: {sphere}")

# Check if it has vertex data
print()
print("2. Checking internal data...")

# Access private attributes to check if generation worked
print(f"   _radius: {sphere._radius}")
print(f"   _segments: {sphere._segments}")
print(f"   _rings: {sphere._rings}")

# Test generate method
print()
print("3. Calling generate() method...")
sphere.generate()
print("   Generate completed")

# Check if Qt methods work
print()
print("4. Checking Qt methods...")
try:
    stride = sphere.stride()
    print(f"   Stride: {stride} bytes")
    
    bounds = sphere.bounds()
    print(f"   Bounds: {bounds}")
    
    primitive_type = sphere.primitiveType()
    print(f"   Primitive type: {primitive_type}")
    
    attribute_count = sphere.attributeCount()
    print(f"   Attribute count: {attribute_count}")
    
    if attribute_count > 0:
        print("   ? Geometry has attributes")
    else:
        print("   ? No attributes - geometry empty!")
        
except Exception as e:
    print(f"   ERROR accessing Qt methods: {e}")

# Test vertex calculation manually
print()
print("5. Manual vertex calculation test...")
r = 1.0
segs = 32
rings = 16

expected_vertices = (rings + 1) * (segs + 1) * 3  # 3 floats per vertex
expected_indices = rings * segs * 6  # 2 triangles per quad, 3 indices per triangle

print(f"   Expected vertices: {expected_vertices} floats")
print(f"   Expected indices: {expected_indices} indices")

print()
print("=== GEOMETRY TEST COMPLETE ===")