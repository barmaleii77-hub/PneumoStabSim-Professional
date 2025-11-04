import QtQuick 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10 as Helpers

/*
 * CylinderGeometry Component - wraps the built-in Helpers.CylinderGeometry so
 * other QML components can bind ``segments`` / ``rings`` without depending on
 * the Python-based CustomGeometry module. This keeps headless/offscreen loads
 * lightweight while matching the original API surface.
 */
Helpers.CylinderGeometry {
    id: cylinderGeometry

    Component.onCompleted: {
        console.log("🔷 CylinderGeometry ready (helpers mesh)")
        console.log("   segments=" + segments + ", rings=" + rings)
    }
}
