# ?? КРИТИЧЕСКАЯ ДИАГНОСТИКА: Черная канва и статичные графики

**Дата:** 3 января 2025, 12:00 UTC
**Проблемы:**
1. ? Черная канва вместо 3D анимации
2. ? График давления не меняется (всегда 101325 Pa)
3. ? Frame heave = 293 метра (свободное падение!)

**Статус:** ?? **КРИТИЧЕСКИЕ ОШИБКИ НАЙДЕНЫ**

---

## ?? ДИАГНОСТИКА ВЫПОЛНЕНА

### Запущено: `diagnose_simulation.py`

**Результаты за 10 секунд:**
```
Total states received: 783 ? (симуляция работает)

Sim time: 7.730s
Step: 7730
Frame heave: 293.087975m  ? ПРОБЛЕМА! (должно быть ~0.0m)
Frame roll: 0.000000rad   ? (не изменяется)
Frame pitch: 0.000000rad  ? (не изменяется)

A1 pressure: 101325.0Pa   ? (атмосферное, не меняется)
B1 pressure: 101325.0Pa   ?
A2 pressure: 101325.0Pa   ?
B2 pressure: 101325.0Pa   ?
Tank pressure: 101325.0Pa ?
```

---

## ?? КОРНЕВЫЕ ПРИЧИНЫ

### Проблема #1: Свободное падение (heave = 293m)

**Файл:** `src/physics/odes.py:98-130`

**Код:**
```python
def assemble_forces(...):
    # ...
    for i, wheel_name in enumerate(wheel_names):
        # ...

        # TODO: Calculate pneumatic cylinder force
        F_cyl_axis = 0.0  # ? ПРОБЛЕМА! Всегда 0

        # TODO: Calculate spring force
        F_spring_axis = 0.0  # ? ПРОБЛЕМА! Всегда 0

        # TODO: Calculate damper force
        F_damper_axis = 0.0  # ? ПРОБЛЕМА! Всегда 0
```

**Что происходит:**
```python
# В f_rhs():
F_suspension_total = np.sum(vertical_forces)  # = 0 (все силы = 0)
F_gravity = params.M * params.g  # ? 9810 N (вниз)

d2Y = (F_gravity + F_suspension_total) / params.M
    = (9810 + 0) / 1000
    = 9.81 m/s?  # Свободное падение!
```

**Результат:**
- Машина падает с ускорением свободного падения
- За 7.7 секунд: heave ? 0.5 * g * t? = 0.5 * 9.81 * 7.7? ? **291 метра** ?

---

### Проблема #2: Давление не меняется

**Файл:** `src/runtime/sim_loop.py:228-241`

**Код:**
```python
# Line states (placeholder)
for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
    line_state = LineState(line=line)
    # TODO: Get actual line state from gas network  ? НЕ РЕАЛИЗОВАНО!
    snapshot.lines[line] = line_state

# Tank state (placeholder)
snapshot.tank = TankState()  # ? Создается с дефолтными значениями
```

**Что происходит:**
```python
# В LineState.__init__():
self.pressure = 101325.0  # Атмосферное давление (дефолт)

# В TankState.__init__():
self.pressure = 101325.0  # Атмосферное давление (дефолт)
```

**Результат:**
- Каждый snapshot создает НОВЫЕ объекты с дефолтным давлением
- Газовая сеть НЕ подключена
- Давление всегда 101325 Pa (1 атм)

---

### Проблема #3: Черная канва (QML не рендерится)

**Возможные причины:**

**A. QML сцена загружена, но НЕ обновляется**

Проверка в `main_window.py:456-469`:
```python
@Slot()
def _update_render(self):
    if not self._qml_root_object:
        return  # ? Если root = None, рендеринг НЕ работает

    # Update QML properties...
```

**Проверить:** Установлен ли `self._qml_root_object`?

**B. QML имеет темный фон (сливается с черным)**

В `assets/qml/main.qml:11`:
```qml
environment: SceneEnvironment {
    clearColor: "#101418"  // Очень темный
}
```

**C. 3D объекты вне камеры**

В `main.qml:21-27`:
```qml
PerspectiveCamera {
    position: Qt.vector3d(0, 1.5, 5)
    eulerRotation.x: -15
}
```

---

## ? ИСПРАВЛЕНИЯ (ТРЕБУЮТСЯ)

### Исправление #1: Добавить силы подвески (КРИТИЧНО)

**Файл:** `src/physics/odes.py`

**Добавить базовую пружину и демпфер:**

```python
def assemble_forces(system: Any, gas: Any, y: np.ndarray,
                   params: RigidBody3DOF) -> Tuple[np.ndarray, float, float]:
    """Assemble forces and moments from suspension system"""
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    wheel_names = ['LP', 'PP', 'LZ', 'PZ']
    vertical_forces = np.zeros(4)

    # TEMPORARY: Add basic spring/damper until pneumatics connected
    k_spring = 50000.0  # N/m (spring constant)
    c_damper = 2000.0   # N·s/m (damping coefficient)

    for i, wheel_name in enumerate(wheel_names):
        x_i, z_i = params.attachment_points.get(wheel_name, (0.0, 0.0))

        # Calculate wheel vertical position relative to frame
        # Y is heave (positive down), so suspension compression is Y
        compression = Y  # Simplified

        # Spring force (resists compression, acts upward = negative)
        F_spring = -k_spring * compression

        # Damper force (resists velocity, acts upward if moving down)
        F_damper = -c_damper * dY

        # Pneumatic force (TODO: get from gas network)
        F_pneumatic = 0.0

        # Total vertical force (positive downward)
        F_total = F_spring + F_damper + F_pneumatic
        vertical_forces[i] = F_total

    # Calculate moments
    tau_x = 0.0
    tau_z = 0.0

    for i, wheel_name in enumerate(wheel_names):
        x_i, z_i = params.attachment_points.get(wheel_name, (0.0, 0.0))
        tau_x += vertical_forces[i] * z_i
        tau_z += vertical_forces[i] * x_i

    return vertical_forces, tau_x, tau_z
```

**Эффект:**
- ? Машина будет удерживаться на месте пружинами
- ? Heave stabilизируется около 0
- ? График heave покажет колебания

---

### Исправление #2: Инициализировать давления (ВРЕМЕННОЕ)

**Файл:** `src/runtime/state.py`

**Изменить дефолтное давление:**

```python
@dataclass
class LineState:
    line: Line
    pressure: float = 150000.0  # 1.5 bar вместо 1.0 bar
    temperature: float = 293.15
    mass: float = 0.001
    # ...

@dataclass
class TankState:
    pressure: float = 200000.0  # 2.0 bar вместо 1.0 bar
    temperature: float = 293.15
    mass: float = 1.0
    # ...
```

**Эффект:**
- ? График давления покажет разные значения для линий/бака
- ??  Временное решение - нужно подключить газовую сеть

---

### Исправление #3: Проверить QML рендеринг

**Добавить debug в `main_window.py`:**

```python
def _update_render(self):
    if not self._qml_root_object:
        print("??  QML root object is None!")  # DEBUG
        return

    # Debug: print first time
    if not hasattr(self, '_debug_printed'):
        print(f"? QML root object: {self._qml_root_object}")
        print(f"  width: {self._qml_root_object.property('width')}")
        print(f"  height: {self._qml_root_object.property('height')}")
        self._debug_printed = True

    # Update properties...
```

---

### Исправление #4: Изменить цвет фона QML (ОПЦИОНАЛЬНО)

**Файл:** `assets/qml/main.qml`

**Изменить на более светлый фон:**

```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color
    clearColor: "#2a2a3e"  // Светлее для видимости (было #101418)
    antialiasingMode: SceneEnvironment.MSAA
    antialiasingQuality: SceneEnvironment.High
}
```

---

## ?? ПРИОРИТЕТ ИСПРАВЛЕНИЙ

| № | Исправление | Приоритет | Эффект |
|---|-------------|-----------|--------|
| **1** | Добавить силы подвески | ?? КРИТИЧНО | Остановит свободное падение |
| **2** | Инициализировать давления | ??  ВАЖНО | Покажет разные давления |
| **3** | Debug QML рендеринга | ?? ВАЖНО | Выяснит причину черной канвы |
| **4** | Изменить фон QML | ?? ОПЦИОНАЛЬНО | Улучшит видимость |

---

## ?? КАК ПРОВЕРИТЬ ИСПРАВЛЕНИЯ

### Шаг 1: Применить исправление #1 (силы подвески)

```powershell
# Открыть файл
code src/physics/odes.py

# Заменить assemble_forces() на код выше
# Сохранить
```

### Шаг 2: Запустить диагностику

```powershell
.\env\Scripts\python.exe diagnose_simulation.py
```

**Ожидаемый результат:**
```
State #100
  Frame heave: 0.049m  ? (около 0, колебания)
  Frame roll: 0.002rad ? (небольшие колебания)
  Frame pitch: 0.001rad ?
```

### Шаг 3: Запустить приложение

```powershell
.\env\Scripts\python.exe app.py
```

**Проверить:**
1. ? График "Dynamics" ? вкладка показывает колебания heave
2. ? График "Pressures" ? вкладка показывает линии (если исправление #2 применено)

---

## ?? ДОПОЛНИТЕЛЬНЫЕ НАХОДКИ

### График давления НЕ обновляется (дополнительная причина)

**Файл:** `src/ui/charts.py:234-246`

**Код:**
```python
def _update_pressure_data(self, snapshot: StateSnapshot):
    # Line pressures
    for line_name, line_state in snapshot.lines.items():
        buffer_key = line_name.value  # A1, B1, A2, B2
        if buffer_key in self.pressure_buffers:
            self.pressure_buffers[buffer_key].append(line_state.pressure)
```

**Проблема:** Если все давления = 101325, график будет ПЛОСКОЙ ЛИНИЕЙ (не "не меняется", а "одинаковый")

**Проверка:** Посмотреть на график - если линия есть, но плоская, это подтверждает проблему.

---

## ?? ВЫВОДЫ

### Симуляция РАБОТАЕТ, но:

1. ? **Физика некорректна:**
   - Нет сил подвески ? свободное падение
   - Нужно добавить временные пружины/демпферы

2. ? **Пневматика НЕ подключена:**
   - Давления всегда дефолтные (101325 Pa)
   - Нужно инициализировать газовую сеть

3. ? **QML может не рендериться:**
   - Нужно проверить `_qml_root_object`
   - Возможно, темный фон сливается

### Что работает:

- ? SimulationManager запущен
- ? Physics worker генерирует states (~78 states/sec)
- ? State bus передает snapshots в UI
- ? ChartWidget получает данные
- ? QTimer работает

### Что НЕ работает:

- ? Силы подвески (всегда 0)
- ? Газовая сеть (placeholders)
- ? 3D анимация (черная канва)

---

## ?? СЛЕДУЮЩИЕ ШАГИ

### Немедленно (КРИТИЧНО):

1. **Добавить временные силы подвески** (исправление #1)
   - Остановит свободное падение
   - Покажет реалистичную динамику

2. **Проверить QML рендеринг** (исправление #3)
   - Выяснить, почему черная канва
   - Добавить debug logging

### В ближайшее время:

3. **Подключить газовую сеть**
   - Создать GasNetwork в PhysicsWorker
   - Инициализировать давления
   - Обновлять в _execute_physics_step()

4. **Подключить пневматическую систему**
   - Создать PneumaticSystem
   - Связать с газовой сетью
   - Вычислять силы цилиндров

---

## ?? ФАЙЛЫ ДЛЯ ИСПРАВЛЕНИЯ

| Файл | Действие | Приоритет |
|------|----------|-----------|
| `src/physics/odes.py` | Добавить силы подвески | ?? КРИТИЧНО |
| `src/runtime/state.py` | Изменить дефолтные давления | ??  ВАЖНО |
| `src/ui/main_window.py` | Debug QML рендеринга | ?? ВАЖНО |
| `assets/qml/main.qml` | Изменить clearColor | ?? ОПЦИОНАЛЬНО |

---

**Дата завершения диагностики:** 3 января 2025, 12:00 UTC
**Статус:** ?? **КРИТИЧЕСКИЕ ПРОБЛЕМЫ ТРЕБУЮТ НЕМЕДЛЕННОГО ИСПРАВЛЕНИЯ**

?? **ПРИЛОЖЕНИЕ НЕ ФУНКЦИОНАЛЬНО БЕЗ ИСПРАВЛЕНИЙ!** ??
