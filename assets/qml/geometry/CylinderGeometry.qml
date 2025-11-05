import QtQuick 6.10
import QtQuick3D 6.10
import CustomGeometry 1.0 as Custom

/*
 * CylinderGeometry Component - wraps the built-in Helpers.CylinderGeometry so
 * other QML components can bind ``segments`` / ``rings`` without depending on
 * the Python-based CustomGeometry module. This keeps headless/offscreen loads
 * lightweight while matching the original API surface.
 */
Custom.ProceduralCylinderGeometry {
    id: cylinderGeometry

    Component.onCompleted: {
        console.log("🔷 CylinderGeometry ready (procedural mesh)")
        console.log("   segments=" + segments + ", rings=" + rings)
    }
}
