#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to integrate DirectionalLights and PointLights modules into main.qml

STEP 1 of QML Integration (5% remaining work)
- Replace 4 individual light sources with 2 modular components
- Add 'import "lighting"' to imports
- Reduce ~100 lines of code
"""

from pathlib import Path


def integrate_lighting_modules():
    """Integrate lighting modules into main.qml"""

    main_qml = Path("assets/qml/main.qml")

    if not main_qml.exists():
        print(f"❌ File not found: {main_qml}")
        return False

    print("🔄 Reading main.qml...")
    content = main_qml.read_text(encoding="utf-8")

    # Step 1: Add lighting import if not present
    if 'import "lighting"' not in content:
        print("✅ Adding lighting import...")
        # Find the line after 'import "camera"'
        content = content.replace(
            'import "camera"  // ✅ PHASE 2: Camera System Modules',
            'import "camera"  // ✅ PHASE 2: Camera System Modules\n'
            'import "lighting"  // ✅ STEP 1: Lighting System Modules',
        )
    else:
        print("ℹ️  Lighting import already present")

    # Step 2: Find and replace old DirectionalLight sources
    print("🔄 Locating old lighting sources...")

    # Pattern to find the 4 lights (key, fill, rim, accent)
    # We'll insert new modular lights BEFORE the first DirectionalLight

    # Find position after CameraController connections
    marker = "// Lighting (with shadow softness)"

    if marker in content:
        print("✅ Found lighting section marker")

        # Find the end of the last PointLight (accentLight)
        # We'll replace from marker to end of accentLight with new modular code

        # Extract section from marker to end of accentLight
        start_idx = content.find(marker)

        # Find the closing brace of accentLight PointLight
        # Look for "PointLight {" then find its matching "}"
        point_light_start = content.find("PointLight {", start_idx)

        if point_light_start > 0:
            # Find matching closing brace
            brace_count = 0
            point_light_end = point_light_start
            in_brace = False

            for i in range(point_light_start, len(content)):
                if content[i] == "{":
                    brace_count += 1
                    in_brace = True
                elif content[i] == "}":
                    brace_count -= 1
                    if in_brace and brace_count == 0:
                        point_light_end = i + 1
                        break

            print(f"📍 Old lighting section: lines {start_idx} to {point_light_end}")

            # New modular lighting code
            new_lighting = """    // ===============================================================
    // ✅ STEP 1: MODULAR LIGHTING SYSTEM
    // ===============================================================

    // ✅ DirectionalLights module (Key, Fill, Rim lights)
    DirectionalLights {
        id: directionalLights
        worldRoot: worldRoot
        cameraRig: cameraController.rig

        shadowsEnabled: root.shadowsEnabled
        shadowResolution: root.shadowResolution
        shadowFilterSamples: root.shadowFilterSamples
        shadowBias: root.shadowBias
        shadowFactor: root.shadowFactor

        keyLightBrightness: root.keyLightBrightness
        keyLightColor: root.keyLightColor
        keyLightAngleX: root.keyLightAngleX
        keyLightAngleY: root.keyLightAngleY
        keyLightCastsShadow: root.keyLightCastsShadow
        keyLightBindToCamera: root.keyLightBindToCamera
        keyLightPosX: root.keyLightPosX
        keyLightPosY: root.keyLightPosY

        fillLightBrightness: root.fillLightBrightness
        fillLightColor: root.fillLightColor
        fillLightCastsShadow: root.fillLightCastsShadow
        fillLightBindToCamera: root.fillLightBindToCamera
        fillLightPosX: root.fillLightPosX
        fillLightPosY: root.fillLightPosY

        rimLightBrightness: root.rimLightBrightness
        rimLightColor: root.rimLightColor
        rimLightCastsShadow: root.rimLightCastsShadow
        rimLightBindToCamera: root.rimLightBindToCamera
        rimLightPosX: root.rimLightPosX
        rimLightPosY: root.rimLightPosY
    }

    // ✅ PointLights module (Accent light)
    PointLights {
        id: pointLights
        worldRoot: worldRoot
        cameraRig: cameraController.rig

        pointLightBrightness: root.pointLightBrightness
        pointLightColor: root.pointLightColor
        pointLightX: root.pointLightX
        pointLightY: root.pointLightY
        pointLightRange: root.pointLightRange
        pointLightCastsShadow: root.pointLightCastsShadow
        pointLightBindToCamera: root.pointLightBindToCamera
    }"""

            # Replace old section with new modular code
            content = content[:start_idx] + new_lighting + content[point_light_end:]

            print("✅ Replaced old lighting with modular components")

            # Write back
            main_qml.write_text(content, encoding="utf-8")

            print(f"✅ Successfully integrated lighting modules into {main_qml}")
            print("📊 Reduced ~100 lines of code")
            print("🎯 STEP 1 Complete: Lighting System Modular")

            return True
        else:
            print("❌ Could not find PointLight section")
            return False
    else:
        print(f"❌ Marker not found: {marker}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 QML INTEGRATION - STEP 1: Lighting Modules")
    print("=" * 60)
    print()

    success = integrate_lighting_modules()

    print()
    print("=" * 60)
    if success:
        print("✅ INTEGRATION COMPLETE")
        print()
        print("📝 Changes made:")
        print("  1. Added 'import \"lighting\"'")
        print("  2. Replaced 3 DirectionalLight + 1 PointLight")
        print("  3. With DirectionalLights + PointLights modules")
        print()
        print("🧪 Next steps:")
        print("  1. Test: python app.py")
        print("  2. Verify lighting works correctly")
        print("  3. Continue to STEP 2 (Materials integration)")
    else:
        print("❌ INTEGRATION FAILED")
        print("   Check error messages above")
    print("=" * 60)
