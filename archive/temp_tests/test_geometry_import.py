from src.ui.custom_geometry import SphereGeometry, CubeGeometry

print("=== CUSTOM GEOMETRY IMPORT TEST ===")
print()

try:
    print("1. Importing SphereGeometry...")
    s = SphereGeometry()
    print(f"   ? SphereGeometry created: {type(s)}")
    print(f"   ? Methods available: {len([m for m in dir(s) if not m.startswith('_')])}")
    
    print()
    print("2. Importing CubeGeometry...")
    c = CubeGeometry()
    print(f"   ? CubeGeometry created: {type(c)}")
    
    print()
    print("3. Checking QML registration...")
    # Check if @QmlElement decorator worked
    if hasattr(s, 'staticMetaObject'):
        print("   ? QML registration metadata found")
    else:
        print("   ? No QML registration metadata")
    
    print()
    print("4. Testing geometry generation...")
    # Trigger geometry generation
    s.generate()
    print("   ? Geometry generation completed")
    
except Exception as e:
    print(f"   ? ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== IMPORT TEST COMPLETE ===")