# НАЧАЛЬНАЯ ГЕОМЕТРИЯ ПОДВЕСКИ

## ПРАВИЛЬНЫЙ РАСЧЁТ

### Исходные данные
```
D_cylinder = 80 mm (диаметр цилиндра)
D_rod = 32 mm (диаметр штока)
L_body = 250 mm (длина цилиндра)
L_piston = 20 mm (толщина поршня)
```

### Расчёт площадей
```
A_head = ? ? (D_cylinder/2)? = ? ? 40? = 5027 mm?
A_rod_steel = ? ? (D_rod/2)? = ? ? 16? = 804 mm?
A_rod = A_head - A_rod_steel = 4223 mm? (эффективная площадь штоковой полости)
```

### Начальное положение поршня (V_head = V_rod)

**Условие равенства объемов:**
```
V_head = V_rod
A_head ? L_head = A_rod ? L_rod
A_head ? L_head = A_rod ? (L_working - L_head)
L_head ? (A_head + A_rod) = A_rod ? L_working

L_head_0 = (A_rod ? L_working) / (A_head + A_rod)
```

**Расчёт:**
```
L_working = L_body - L_piston = 250 - 20 = 230 mm

L_head_0 = (4223 ? 230) / (5027 + 4223)
         = 970290 / 9250
         = 104.9 mm ? 105 mm

L_rod_0 = 230 - 105 = 125 mm
```

**Проверка равенства объёмов:**
```
V_head = 5027 ? 105 = 527835 mm?
V_rod = 4223 ? 125 = 527875 mm?
Разница = 40 mm? (0.0075% - пренебрежимо мала!)
```

### Позиция поршня
```
x_piston_0 = 105 mm от начала цилиндра
pistonRatio = 105 / 250 = 0.42 (42% от длины цилиндра)
```

### Начальное положение рычагов (ГОРИЗОНТАЛЬНО!)

**Рычаг ПЕРПЕНДИКУЛЯРЕН раме при нейтральном положении:**
```
Длина рычага: L_lever = 315 mm

Левая сторона (FL, RL):
j_rod = j_arm + (-315, 0, 0)

FL: (-150, 60, -1000) + (-315, 0, 0) = (-465, 60, -1000)
RL: (-150, 60, 1000) + (-315, 0, 0) = (-465, 60, 1000)

Правая сторона (FR, RR):
j_rod = j_arm + (+315, 0, 0)

FR: (150, 60, -1000) + (315, 0, 0) = (465, 60, -1000)
RR: (150, 60, 1000) + (315, 0, 0) = (465, 60, 1000)
```

### Длина хвостовика

**Вычисляется из начальной геометрии:**
```
Расстояние от j_tail до j_rod (при горизонтальном рычаге):

Для FL:
dx = j_rod.x - j_tail.x = -465 - (-100) = -365 mm
dy = j_rod.y - j_tail.y = 60 - 710 = -650 mm
L_total = ?(365? + 650?) = ?(133225 + 422500) = ?555725 = 745.5 mm

Компоненты:
L_tail = 100 mm (хвостовик)
L_cylinder = 250 mm (корпус цилиндра)
L_piston_rod = L_total - L_tail - L_cylinder = 745.5 - 100 - 250 = 395.5 mm
```

## QML КОД (ПРАВИЛЬНЫЙ)

```qml
// НАЧАЛЬНЫЕ ПОЗИЦИИ (фиксированные!)
property vector3d fl_j_arm: Qt.vector3d(-150, 60, -1000)
property vector3d fr_j_arm: Qt.vector3d(150, 60, -1000)
property vector3d rl_j_arm: Qt.vector3d(-150, 60, 1000)
property vector3d rr_j_arm: Qt.vector3d(150, 60, 1000)

property vector3d fl_j_tail: Qt.vector3d(-100, 710, -1000)
property vector3d fr_j_tail: Qt.vector3d(100, 710, -1000)
property vector3d rl_j_tail: Qt.vector3d(-100, 710, 1000)
property vector3d rr_j_tail: Qt.vector3d(100, 710, 1000)

// НАЧАЛЬНЫЕ j_rod (рычаг ГОРИЗОНТАЛЕН при angle=0!)
property vector3d fl_j_rod_0: Qt.vector3d(-465, 60, -1000)
property vector3d fr_j_rod_0: Qt.vector3d(465, 60, -1000)
property vector3d rl_j_rod_0: Qt.vector3d(-465, 60, 1000)
property vector3d rr_j_rod_0: Qt.vector3d(465, 60, 1000)

// ПОРШЕНЬ В ПОЛОЖЕНИИ РАВЕНСТВА ОБЪЁМОВ
property real pistonPositionMm: 105.0  // mm от начала цилиндра
property real pistonRatio: 0.42        // 42% от длины цилиндра

// ДЛИНА ШТОКА ПОРШНЯ (вычислена из геометрии)
property real pistonRodLength: 395.5   // mm
```

## ВАЖНО!

1. **Поршень НЕ в середине цилиндра!** Он смещён к безштоковой полости из-за объёма штока!
2. **Рычаг СТРОГО горизонтален** в нейтральном положении (не под углом!)
3. **Все координаты вычисляются** из начального состояния, а не наоборот!
4. **Длина хвостовика зависит** от расположения j_tail и j_rod_0!
