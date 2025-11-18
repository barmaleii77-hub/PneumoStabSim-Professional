# UI Panels & Widgets Documentation

## Overview

Панели управления и виджеты отвечают за интерактивную настройку симуляции
PneumoStabSim. Все актуальные компоненты работают поверх PySide6 и получают
данные из `SettingsManager`, а устаревшие панели переведены в режим
совместимости и служат для поддержки старых сценариев.

- **Фокус обновления (март 2026):** завершён аудит «мертвых» ссылок, панели и
  виджеты описаны с актуальными путями модулей и назначением сигналов.
- **Устранение дублей:** ссылки на архивные QML-заглушки перенесены в раздел
  legacy (`archive/assets/qml/legacy_backups`); взаимодействие с `archive/old_qml`
  прекращено после удаления каталога.
- **Июнь 2026 (обновление мета-параметров):** `RangeSlider` теперь публикует
  сигналы `stepChanged`, `decimalsChanged`, `unitsChanged` для сохранения
  пользовательских настроек точности и отображения. `GeometryPanel`_SERIALIZUET
  эти значения под ключами `current.geometry.meta.<param>.*`.

## Inventory (March 2026)

| Компонент | Модуль | Статус | Основные особенности |
|-----------|--------|--------|----------------------|
| `GeometryPanel` | `src/ui/panels/panel_geometry.py` | ✅ В эксплуатации | Загружает параметры из `app_settings.json`, публикует сигналы `geometry_changed` и `geometry_updated`, использует расширенный `RangeSlider` для всех непрерывных диапазонов. 【F:src/ui/panels/panel_geometry.py†L34-L112】【F:src/ui/panels/panel_geometry.py†L150-L232】|
| `PneumoPanel` | `src/ui/panels/panel_pneumo.py` | ✅ В эксплуатации | Совместимый реэкспорт модульной реализации (`src/ui/panels/pneumo/`), используется в главном окне и автотестах. 【F:src/ui/panels/panel_pneumo.py†L1-L8】|
| `ModesPanel` | `src/ui/panels/panel_modes.py` | ⚠️ Legacy | Поддержка исторических сценариев через стандартные Qt-слайдеры; сохраняет настройки через `SettingsManager`, но в новых сборках заменён QML-панелью. 【F:src/ui/panels/panel_modes.py†L1-L77】|
| `RoadPanel` | `src/ui/panels/panel_road.py` | ✅ В эксплуатации | Управление CSV-профилями дорог, пресетами и назначением на колёса, включает сигналы `load_csv_profile`, `apply_preset`, `apply_to_wheels`. 【F:src/ui/panels/panel_road.py†L1-L78】|
| `RangeSlider` | `src/ui/widgets/range_slider.py` | ✅ Виджет общего назначения | Поддерживает дебаунс, визуальные подсказки и кастомные шорткаты для доступности. Теперь также публикует `stepChanged`, `decimalsChanged`, `unitsChanged` для сериализации пользовательской точности диапазонов. 【F:src/ui/widgets/range_slider.py†L1-L103】【F:src/ui/widgets/range_slider.py†L143-L206】|
| `Knob` | `src/ui/widgets/knob.py` | ✅ Виджет общего назначения | Ротари-контрол с двойным вводом (dial + spinbox), поддерживает шорткаты и отображение единиц измерения. 【F:src/ui/widgets/knob.py†L1-L60】|

## GeometryPanel

`GeometryPanel` синхронизирует геометрию подвески с JSON-настройками и
расширенным журналированием.

- Все поля читаются из `SettingsManager` при инициализации, UI строится на основе
  полученных значений, а не внутренних дефолтов. 【F:src/ui/panels/panel_geometry.py†L44-L108】
- Для линейных диапазонов используется `RangeSlider`, обеспечивающий точность до
  тысячных метра и дебаунс сигналов `valueEdited`. 【F:src/ui/panels/panel_geometry.py†L150-L232】
- Панель публикует события `geometry_changed` и `geometry_updated`, что позволяет
  синхронизировать модуль геометрии и визуализацию. 【F:src/ui/panels/panel_geometry.py†L35-L76】
- Новые мета-параметры шага/точности/единиц для каждого диапазона сохраняются в
  `current.geometry.meta.<param>.step|decimals|units` через обработчики
  `_on_slider_step_changed`, `_on_slider_decimals_changed`, `_on_slider_units_changed`.

## PneumoPanel

`PneumoPanel` является совместимым фасадом для полностью переработанного
пневматического интерфейса.

- Основная логика размещена в пакете `src/ui/panels/pneumo/`; модуль
  `panel_pneumo.py` экспортирует её под историческим именем, что упрощает
  миграцию тестов и QML-связей. 【F:src/ui/panels/panel_pneumo.py†L1-L8】
- Структура вкладок (`pressures_tab.py`, `thermo_tab.py`, `valves_tab.py`,
  `receiver_tab.py`) документирована в README пакета и покрывает контроль
  давления, терморежимов и клапанов. 【F:src/ui/panels/pneumo/README.md†L1-L80】

## ModesPanel (Legacy)

`ModesPanel` остаётся доступным для сценариев, где требуется классический Qt UI.

- Использует `StandardSlider` и группы переключателей для настройки режимов
  симуляции; значения синхронизируются с `SettingsManager`. 【F:src/ui/panels/panel_modes.py†L1-L89】
- В новых проектах рекомендуется переходить на QML `SimulationPanel`. Документ
  фиксирует статус компонента как legacy и оставляет ссылку для обслуживания
  старых макросов.
- QML `SimulationPanel` собирает режимы в одном блоке: переключатели
  кинематика/динамика и изотермия/адиабата, селектор дорожных профилей с
  пресетами и полем «Custom», флажок проверки интерференции, отдельные тумблеры
  для учёта пружин/демпферов в кинематике, а также ввод температуры среды,
  синхронно обновляющий категории `modes` и `pneumatic` в `SettingsManager`.
  【F:qml/SimulationPanel.qml†L1337-L1443】【F:qml/SimulationPanel.qml†L1398-L1403】【F:qml/SimulationPanel.qml†L1593-L1609】【F:src/ui/main_window_pkg/signals_router.py†L1455-L1496】
- Refactored Qt-вкладки `ModesPanel` повторяют связку настроек: вкладка
  симуляции содержит переключатель проверки пересечений и ввод температуры
  среды, блок «Физика» — отдельные флажки пружин/демпферов в кинематике,
  а вкладка дороги — селектор дорожных профилей с полем «Пользовательский».
  Все изменения немедленно записываются в `SettingsManager`, включая синхронное
  обновление категории `pneumatic` для температуры воздуха. 【F:src/ui/panels/modes/simulation_tab.py†L62-L175】【F:src/ui/panels/modes/physics_tab.py†L60-L150】【F:src/ui/panels/modes/road_excitation_tab.py†L68-L155】

## RoadPanel

`RoadPanel` отвечает за подготовку профилей дорожных возмущений.

- Поддерживает загрузку произвольных CSV-файлов, набор предустановок и
  назначение профилей на отдельные колёса. 【F:src/ui/panels/panel_road.py†L21-L78】
- Сигналы `load_csv_profile`, `apply_preset`, `apply_to_wheels` и `clear_profiles`
  используются главным окном для синхронизации UI с симуляцией. 【F:src/ui/panels/panel_road.py†L29-L55】

## Common Widgets

### RangeSlider

- Предоставляет три варианта сигналов (`valueChanged`, `valueEdited`,
  `rangeChanged`) и подробные визуальные подсказки диапазона. 【F:src/ui/widgets/range_slider.py†L32-L104】
- Встроенные шорткаты (`Ctrl+Alt+Right/Left`, `Ctrl+Alt+1..3`) повышают
  доступность и повторяют конфигурацию панели геометрии. 【F:src/ui/widgets/range_slider.py†L143-L206】
- Метапараметры пользовательской точности (`step`, `decimals`, `units`) имеют
  собственные сигналы и могут сохраняться панелями в SettingsManager, исключая
  скрытые дефолты.

### Knob

- Сочетает `QDial` и `QDoubleSpinBox` для плавной и точной регулировки.
  Дополняется метками единиц и настраиваемыми шорткатами для инкрементов. 【F:src/ui/widgets/knob.py†L1-L60】
- Виджет применяется в специализированных вкладках пневмопанели для управления
  клапанами и режимами давления.
- Атрибут `units_label` теперь создаётся при инициализации и может быть `None`,
  пока единицы не заданы, что упрощает типизацию и обслуживание тестов. 【F:src/ui/widgets/knob.py†L95-L164】

## Maintenance Notes

- Все панели используют централизованный `SettingsManager`; новое поле должно
  быть добавлено в схему и панели синхронно.
- Legacy QML-заглушки перенесены в архив, активные Python-панели остаются в
  `src/ui/panels/`. Удаление `archive/old_qml/` исключило дублированные
  инвентари, на которые ссылки в документации больше не выдаются.
