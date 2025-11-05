.pragma library

function normalizeType(eventType) {
    if (!eventType) {
        return "unknown";
    }
    return String(eventType).toLowerCase();
}

function forward(eventType, name, windowRef, component) {
    const normalizedType = normalizeType(eventType);
    const timestamp = new Date().toISOString();
    const payload = {
        event: name || "",
        eventType: normalizedType,
        component: component || "qml",
        timestamp: timestamp
    };

    if (windowRef && typeof windowRef.logQmlEvent === "function") {
        try {
            windowRef.logQmlEvent(normalizedType, name || "");
        } catch (err) {
            console.warn("LogBridge: window.logQmlEvent failed", err);
        }
    }

    console.log(JSON.stringify({
        level: "info",
        logger: "qml.diagnostics",
        event: "qml_event",
        payload: payload
    }));
}
