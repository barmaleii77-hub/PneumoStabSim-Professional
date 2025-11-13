import QtQuick 6.10
import QtQuick3D 6.10

// Совместимый адаптер для ReflectionProbe, предоставляющий свойство `enabled`
// даже в окружениях, где у базового типа отсутствует это свойство.
// Логика:
// - Экспортирует собственное свойство `enabled`
// - Пытается установить нативное свойство через setProperty("enabled", ...)
//   если оно поддерживается конкретной сборкой
// - Дублирует состояние в `visible` как минимально достаточный переключатель
ReflectionProbe {
    id: probe

    // Экспортируемое свойство для тестов и внешних биндингов
    property bool enabled: true

    // Синхронизация флагов
    function _syncEnabled() {
        try {
            // Попытка установить нативное свойство, если доступно
            // qmllint disable missing-property
            if (probe.setProperty !== undefined) {
                probe.setProperty("enabled", enabled)
            }
            // qmllint enable missing-property
        } catch (e) {
            // best-effort, продолжаем
        }
        probe.visible = enabled
    }

    Component.onCompleted: _syncEnabled()
    onEnabledChanged: _syncEnabled()
}
