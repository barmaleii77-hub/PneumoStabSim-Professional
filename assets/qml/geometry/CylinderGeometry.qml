import QtQuick 6.10
import QtQuick3D 6.10
import CustomGeometry 1.0

/*
 * CylinderGeometry Component - procedural cylinder mesh with adjustable quality.
 *
 * Provides a shared wrapper around the CustomGeometry.ProceduralCylinderGeometry
 * class so that other QML components can simply instantiate ``CylinderGeometry``
 * and bind its ``segments`` / ``rings`` properties to UI controls.
 */
ProceduralCylinderGeometry {
    id: cylinderGeometry

    Component.onCompleted: {
        console.log("🔷 CylinderGeometry ready (procedural mesh)")
        console.log("   segments=" + segments + ", rings=" + rings)
    }
}
