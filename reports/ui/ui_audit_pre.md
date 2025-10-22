# UI AUDIT REPORT (PRE-CHANGES)
**Generated:** 2025-10-05 19:00

## 1. MAIN WINDOW STRUCTURE

**File:** `src/ui/main_window.py`
**Class:** `MainWindow(QMainWindow)`
**Backend:** Qt Quick 3D (U-Frame PBR) with Direct3D 11 RHI

### Central Widget
- **Type:** `QQuickWidget` (Qt Quick 3D scene)
- **QML Source:** `assets/qml/main.qml`
- **Resize Mode:** `SizeRootObjectToView`
- **Features:**
  - Full 3D suspension visualization
  - U-Frame with PBR materials
  - 4 suspension corners with cylinders, levers
  - Orbit camera controls

### Current Layout
```
???????????????????????????????????????????????????
?  Menu Bar                                       ?
???????????????????????????????????????????????????
?      ?                                 ?        ?
? Left ?      3D SCENE (Center)          ? Right  ?
? Dock ?    (QQuickWidget)               ? Dock   ?
?      ?                                 ?        ?
???????????????????????????????????????????????????
?  Bottom Dock (Road Panel - Hidden)              ?
???????????????????????????????????????????????????
?  Status Bar                                     ?
???????????????????????????????????????????????????
```

## 2. DOCK PANELS (CURRENT STATE)

### Left Dock Area (TABIFIED)
1. **Geometry Dock** (`geometry_dock`)
   - **Class:** `GeometryPanel`
   - **File:** `src/ui/panels/panel_geometry.py`
   - **ObjectName:** `"GeometryDock"`
   - **Title:** "Geometry" (English)
   - **Min Width:** 200px, **Max Width:** 350px
   - **Min Height:** 200px

2. **Pneumatics Dock** (`pneumo_dock`) - TABIFIED with Geometry
   - **Class:** `PneumoPanel`
   - **File:** `src/ui/panels/panel_pneumo.py`
   - **ObjectName:** `"PneumaticsDock"`
   - **Title:** "Pneumatics" (English)
   - **Min Width:** 200px, **Max Width:** 350px
   - **Min Height:** 200px

### Right Dock Area (TABIFIED)
3. **Charts Dock** (`charts_dock`)
   - **Class:** `ChartWidget`
   - **File:** `src/ui/charts.py`
   - **ObjectName:** `"ChartsDocker"`
   - **Title:** "Charts" (English)
   - **Min Width:** 300px, **Max Width:** 500px
   - **Min Height:** 250px

4. **Modes Dock** (`modes_dock`) - TABIFIED with Charts
   - **Class:** `ModesPanel`
   - **File:** `src/ui/panels/panel_modes.py`
   - **ObjectName:** `"ModesDock"`
   - **Title:** "Simulation & Modes" (English)
   - **Min Width:** 300px, **Max Width:** 500px
   - **Min Height:** 200px

### Bottom Dock Area (HIDDEN)
5. **Road Panel** (`road_dock`)
   - **Class:** `RoadPanel`
   - **File:** `src/ui/panels/panel_road.py`
   - **ObjectName:** `"RoadDock"`
   - **Title:** "Road Profiles" (English)
   - **Min Height:** 150px, **Max Height:** 250px
   - **Visibility:** HIDDEN by default (`dock.hide()`)

## 3. CURRENT ISSUES FOUND

### ? ЯЗЫК (Language)
- **ALL** titles in English: "Geometry", "Pneumatics", "Charts", etc.
- Need Russian: "Геометрия", "Пневмосистема", "Графики"

### ? LAYOUT
- Charts in RIGHT dock (NOT bottom across full width)
- Should be: Vertical splitter with charts BELOW scene

### ? ACCORDIONS
**Status:** NO accordions found in current code
- ? Good! No `QToolBox`, no `Collapsible` widgets
- Already using dock tabs (tabified panels)

### ? SCROLLBARS
- Panels use fixed layouts
- NO `QScrollArea` wrappers for overflow handling
- Need to add scroll areas inside each tab

### ? COMBOBOXES (Выпадающие списки)
- Limited use of `QComboBox` for presets/units
- Need to add comboboxes for:
  - Unit selection (mm/m/bar/Pa)
  - Geometry presets
  - Mode selection

## 4. PANEL CONTENT ANALYSIS

### 4.1 GeometryPanel
**File:** `src/ui/panels/panel_geometry.py`

**Current Widgets:**
- Frame dimensions (sliders/knobs)
- Lever parameters
- Cylinder specs
- Track width settings

**Language:** English labels
**Scrolling:** NO (fixed layout)
**Comboboxes:** Minimal

### 4.2 PneumoPanel
**File:** `src/ui/panels/panel_pneumo.py`

**Current Widgets:**
- Thermo mode selection
- Pressure settings
- Valve parameters
- Master isolation toggle

**Language:** English labels
**Scrolling:** NO
**Comboboxes:** Some for mode selection

### 4.3 ModesPanel
**File:** `src/ui/panels/panel_modes.py`

**Current Widgets:**
- Simulation controls (Start/Stop/Pause)
- Animation parameters
- Physics options
- Mode switches

**Language:** English labels
**Scrolling:** NO
**Comboboxes:** Some for mode types

### 4.4 RoadPanel
**File:** `src/ui/panels/panel_road.py`

**Current Widgets:**
- CSV file loader
- Profile presets
- Wheel assignment
- Clear profiles button

**Language:** English
**Status:** Hidden by default (good!)
**Note:** Need to hide/disable in final UI

### 4.5 ChartWidget
**File:** `src/ui/charts.py`

**Current Position:** RIGHT dock (WRONG!)
**Target Position:** BOTTOM splitter section
**Width:** Constrained (300-500px)
**Target Width:** FULL WIDTH

## 5. QML SCENE FILES

**Main QML:** `assets/qml/main.qml`
**Components:**
- `UFrameScene.qml` - Main 3D scene
- `CorrectedSuspensionCorner.qml` - Suspension corners
- `Materials.qml` - PBR materials
- `MechCorner.qml` - Mechanical components

**Language in QML:** Mixed (mostly English property names, some Russian strings)
**Action Needed:** Russify UI labels in QML overlays

## 6. MENU BAR & TOOLBAR

### Menus (English)
- **File** ? Need: "Файл"
  - Save Preset, Load Preset, Export, Exit
- **Road** ? Need: "Дорога" (or hide completely)
- **Parameters** ? Need: "Параметры"
- **View** ? Need: "Вид"

### Toolbar
- Actions: Start, Stop, Pause, Reset, Toggle Panels
- **Language:** English
- **Target:** Russian ("Старт", "Стоп", "Пауза", "Сброс")

## 7. STATUS BAR

**Widgets (all English):**
- `sim_time_label` - "Sim Time: 0.000s"
- `step_count_label` - "Steps: 0"
- `fps_label` - "Physics FPS: 0"
- `realtime_label` - "RT: 1.00x"
- `queue_label` - "Queue: 0/0"
- `kinematics_label` - "alpha: 0.0deg | s: 0.0mm | V_h: 0cm3 | V_r: 0cm3"

**Target:** Russian labels ("Время симуляции", "Шаги", "FPS физики", etc.)

## 8. WIDGETS INVENTORY

### Custom Widgets Found
1. **Knob** - `src/ui/widgets/knob.py`
   - Circular rotary control
   - Used for precise value input

2. **RangeSlider** - `src/ui/widgets/range_slider.py`
   - Two-handle slider for ranges
   - Used for min/max bounds

**Status:** ? Keep these! They're the "крутилки/слайдеры" to preserve

### Standard Qt Widgets
- `QSlider` - Many instances
- `QSpinBox`, `QDoubleSpinBox` - Value inputs
- `QCheckBox`, `QRadioButton` - Toggles
- `QGroupBox` - Section grouping
- `QLabel` - Text labels
- `QComboBox` - Limited use (need MORE!)

## 9. SIGNALS & CONNECTIONS

### Geometry Panel Signals
- `parameter_changed(name: str, value: float)`
- `geometry_changed(params: dict)`

### Pneumo Panel Signals
- `mode_changed(mode_type: str, new_mode: str)`
- `parameter_changed(name: str, value: float)`

### Modes Panel Signals
- `simulation_control(command: str)`
- `mode_changed(mode_type: str, new_mode: str)`
- `animation_changed(params: dict)`

**Action:** All working correctly, keep as-is

## 10. DEPENDENCIES & IMPORTS

### Qt Modules Used
- `PySide6.QtWidgets` - Main widgets
- `PySide6.QtCore` - Signals, slots, properties
- `PySide6.QtGui` - Actions, shortcuts
- `PySide6.QtQuickWidgets` - QQuickWidget for QML
- `PySide6.QtQuick3D` - 3D scene (via QML)

### Custom Modules
- `src.ui.panels.*` - Panel modules
- `src.ui.charts` - Chart widget
- `src.ui.widgets.*` - Custom widgets
- `src.ui.geometry_bridge` - Python?QML bridge
- `src.runtime` - Simulation manager

**Status:** ? All dependencies available

## 11. SETTINGS & PERSISTENCE

**Using:** `QSettings` (Qt's native settings)
**Organization:** `"PneumoStabSim"`
**Application:** `"PneumoStabSimApp"`

**Saved State:**
- Window geometry (CURRENTLY DISABLED - causes crashes)
- Window state (dock positions)
- Last preset path

**Action:** Keep settings system, but verify Russian text persistence

## 12. CRITICAL FINDINGS SUMMARY

### ? GOOD (Keep As-Is)
- NO accordions in code
- Dock tabification already used (space-efficient)
- Custom knobs/sliders exist and work
- Signal system functional
- 3D scene integration working

### ? NEEDS CHANGING
1. **Language:** ALL English ? Russian
2. **Layout:** Charts in RIGHT dock ? BOTTOM splitter (full width)
3. **Scrolling:** Add `QScrollArea` wrappers in tabs
4. **Comboboxes:** Add for presets/units selection
5. **Road Panel:** Hide or make stub (no CSV loading)

## 13. FILE PATHS REFERENCE

```
MAIN WINDOW:
  src/ui/main_window.py             (MainWindow class)

PANELS:
  src/ui/panels/panel_geometry.py   (GeometryPanel)
  src/ui/panels/panel_pneumo.py     (PneumoPanel)
  src/ui/panels/panel_modes.py      (ModesPanel)
  src/ui/panels/panel_road.py       (RoadPanel - to hide)

CHARTS:
  src/ui/charts.py                  (ChartWidget)

CUSTOM WIDGETS:
  src/ui/widgets/knob.py            (Knob - rotary control)
  src/ui/widgets/range_slider.py   (RangeSlider)

QML SCENE:
  assets/qml/main.qml               (Main 3D scene)
  assets/qml/UFrameScene.qml        (U-Frame component)
  assets/qml/components/*.qml       (Suspension components)
```

## 14. READINESS CHECKLIST

- ? Folder structure identified
- ? Main window located (`src/ui/main_window.py`)
- ? All panels found (4 docks + charts)
- ? No accordions present (good!)
- ? Custom widgets cataloged (knobs, sliders)
- ? Charts location identified (right dock - needs moving)
- ? QML scene files mapped
- ? Language audit complete (all English ? needs Russian)
- ? Layout issues documented (charts placement)
- ? Scrolling gaps identified (no QScrollArea)
- ? Combobox usage reviewed (need more)

## 15. NEXT STEPS (Per PROMPT #1)

1. **Restructure Layout:**
   - Replace docks with `QTabWidget` (right side)
   - Move charts to bottom via `QSplitter(Qt.Vertical)`
   - Wrap each tab content in `QScrollArea`

2. **Full Russification:**
   - All dock/tab titles
   - All labels, buttons, tooltips
   - Menu items, toolbar actions
   - Status bar widgets
   - Units (mm, bar, °)

3. **Add Comboboxes:**
   - Geometry presets dropdown
   - Unit selection (mm/m, bar/Pa)
   - Mode selections (where applicable)

4. **Hide Road Panel:**
   - Keep code, but don't show in UI
   - Create stub "Динамика движения" tab

5. **Testing:**
   - pytest-qt structure tests
   - Value tracing tests
   - Russian text rendering tests

---

**Audit Complete** ?
**Ready for Implementation:** YES
**Critical Blockers:** NONE
