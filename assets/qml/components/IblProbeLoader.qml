import QtQuick
import QtQuick3D

QtObject {
    id: controller

    /**
      * Primary HDR environment map used for IBL/skybox lighting.
      * Defaults to the studio lighting provided with the project.
      */
    property url primarySource: Qt.resolvedUrl("../../hdr/studio.hdr")

    /**
      * Optional fallback map that is tried automatically when the primary
      * asset is missing (useful for developer setups without HDR packages).
      */
    property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")

    /** Internal flag preventing infinite fallback recursion. */
    property bool _fallbackTried: false

    /** Expose the probe for consumers. */
    property Texture probe: Texture {
        id: hdrProbe
        source: controller.primarySource
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }

    /** Simple ready flag to avoid binding against an invalid texture. */
    readonly property bool ready: probe.status === Texture.Ready

    property Connections _statusMonitor: Connections {
        target: controller.probe
        function onStatusChanged() {
            if (controller.probe.status === Texture.Error && !controller._fallbackTried) {
                controller._fallbackTried = true
                console.warn("⚠️ HDR probe not found at", controller.probe.source, "— falling back to", controller.fallbackSource)
                controller.probe.source = controller.fallbackSource
            } else if (controller.probe.status === Texture.Ready) {
                console.log("✅ HDR probe ready:", controller.probe.source)
            } else if (controller.probe.status === Texture.Error && controller._fallbackTried) {
                console.warn("❌ Both HDR probes failed to load, IBL will be disabled")
            }
        }
    }
}
