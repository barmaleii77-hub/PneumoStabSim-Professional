# Диагностика «чёрного экрана»

## 1. Наблюдение

При запуске QtQuick3D сцены в логе отсутствуют сообщения о создании моделей (`SuspensionAssembly loaded`, `Frame initialized`, `SuspensionCorner initialized`). Во View3D присутствуют камера и освещение, но отсутствуют компоненты `Model` с геометрией подвески.

## 2. Архитектура сцены

```
assets/qml/main.qml
  └── Loader → PneumoStabSim/SimulationRoot.qml
        └── SuspensionAssembly.qml  ← ожидается создание модели
            ├── Frame.qml
            └── 4 × SuspensionCorner.qml
```

`SimulationRoot.qml` подключает `SuspensionAssembly` из каталога `assets/qml/scene` и передаёт туда состояние геометрии, материалы и параметры отражательного probe.

## 3. Фактическое состояние

* В сцене активны DirectionalLights, PointLights и камера (`CameraController`).
* Консоль не содержит сообщений о `SuspensionAssembly` и дочерних компонентах, что указывает на то, что `Component.onCompleted` в `SuspensionAssembly.qml` не исполнился.
* Следовательно, `SuspensionAssembly` (а значит и `Frame`/`SuspensionCorner`) не инициализируются.

## 4. Возможные причины

1. Ошибка импорта модуля сцены: `SimulationRoot.qml` использует `import "../scene"`, но при запуске этот импорт может быть недоступен (неверный `QML2_IMPORT_PATH`).
2. Компонент `SuspensionAssembly` создаётся через `Loader`/`Component` и остаётся неактивным (например, из-за `active: false`).
3. Нарушены обязательные свойства `required property` в `SuspensionAssembly.qml`, что приводит к silent failure при инстанцировании.

## 5. Рекомендуемые проверки

* Убедиться, что каталог `assets/qml/scene` присутствует в путях QML (переменная окружения `QML2_IMPORT_PATH`).
* В `SimulationRoot.qml` временно добавить `Component.onCompleted` рядом с `SuspensionAssembly` и убедиться, что блок выполняется.
* Проверить передачу свойств `worldRoot`, `geometryState`, `sharedMaterials` и `materialsDefaults` при создании `SuspensionAssembly`.

## 6. Команда для поиска использования

```powershell
Get-Content assets\qml\PneumoStabSim\SimulationRoot.qml | Select-String "SuspensionAssembly" -Context 5
```

Команда поможет быстро просмотреть участок, где инстанцируется `SuspensionAssembly`, при необходимости внести правки или добавить диагностику.
