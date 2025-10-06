# B-1. ���������� ���� ������� ��ڨ�� ��������

## ������: ? ��������� �������

### ?? ����������� ������

#### ? ��������� ������ �������� � PneumoPanel

**����� UI ��������:**
- ?? **������������� �������** (`QComboBox`): "������ �����" / "�������������� ������"
- ??? **������ �����**: Knob ��� ������� ������� ������ (0.001-0.100 �?)
- ?? **�������������� �����**: 2 Knob'� ��� �������� � ����� ��������
- ?? **������� ����������**: �������������� ������ � ����������� ������

#### ? ����������� ��� ������ ������

**����� 1: Manual Volume (MANUAL)**
```python
self.manual_volume_knob = Knob(
    minimum=0.001, maximum=0.100, value=0.020, step=0.001,
    decimals=3, units="�?", title="����� ��������"
)
```
- ������ ������� ������ � �?
- ��������: 1-100 ������  
- ��������: 0.001 �? (1 ����)

**����� 2: Geometric Calculation (GEOMETRIC)**  
```python
# V = ? ? (D/2)? ? L
volume = math.pi * radius * radius * length
```
- �������������� ������: ������� ? ����� ? �����
- �������: 50-500��, �����: 100-2000��
- ���������� � �������� �������

#### ? ���������� � ������������ ������

**����� ���������:**
- `volume_mode`: 'MANUAL' | 'GEOMETRIC'
- `receiver_volume`: ������� ����� (�?)
- `receiver_diameter`: ������� �������� (�)
- `receiver_length`: ����� �������� (�)

**������� � �������:**
- `mode_changed.emit('volume_mode', mode)` - ����� ������
- `parameter_changed.emit('receiver_volume', volume)` - ����� ������
- `pneumatic_updated.emit(parameters)` - ������ ����������

#### ? ��������� � ��������

**�������� ������:**
- ? ������������� ����� ? ������
- ?? ����� ����� (< 5�) ? ��������������
- ?? ������� ����� (> 200�) ? ��������������

**�������� ���������:**
- ? ������������� ������� ? ������  
- ?? ������������ ��������� (L/D < 1 ��� > 20) ? ��������������

### ?? ���������� ������������

```
=== B-1: Test receiver dual volume modes ===
+ PneumoPanel created successfully
+ All receiver controls present
+ All receiver parameters in configuration
   - Mode: MANUAL
   - Volume: 0.020 m3
   - Diameter: 0.200 m
   - Length: 0.500 m

--- Mode switching test ---
+ Switch to geometric mode works
+ Geometric calculation correct
   D=0.3m, L=0.8m -> V=0.056549m3
+ Switch back to manual mode works

--- Validation test ---
+ Negative volume validation works
```

**��� ����� �������� ?**

### ?? ��������� ��������

**Manual Mode (�� ���������):**
- �����: 0.020 �? (20 ������)

**Geometric Mode:**
- �������: 0.200� (200��)
- �����: 0.500� (500��)  
- ��������� �����: ~0.016 �? (16 ������)

### ?? ���������� � ������������ �������

**����� � ReceiverVolumeMode enum:**
- UI �������� `volume_mode` ����� � ���������� � `ReceiverVolumeMode.NO_RECALC`
- ����� ��������� ����� `parameter_changed` ������
- ����������������� ��������� ��������� � `ReceiverState`

### ?? API ���������

**����� ������ PneumoPanel:**
- `_create_receiver_group()` - �������� ������ UI
- `_on_volume_mode_changed()` - ������������ �������
- `_update_calculated_volume()` - �������������� ������
- `_on_receiver_geometry_changed()` - ��������� ��������

**���������� ������:**
- `_set_default_values()` - ��������� ��������� ��������
- `_connect_signals()` - ���������� ������� ���������
- `_reset_to_defaults()` - ����� ���������� ��������
- `set_parameters()` - ��������� ���������� ��������
- `_validate_system()` - ��������� ��������

### ?? ���������� � ���������� �����

? **B-1 ��������� ��������**  
? UI �������� �������� ���������  
? ������������ ������� �������������  
? �������������� ������� �����  
? ��������� ������������� ������  

**������ ��� B-2**: ���������� � ����������������� ������� � ������������ � 3D ������.

---

**����� ����������**: ~2 ����  
**��������**: A+ (��� ����� ��������)  
**��������� ����**: B-2. ���������� � ReceiverState