# B-2. ���������� � ����������������� ������� - ��������� ?

## ����: ������� UI �������� �������� � ReceiverState � ReceiverVolumeMode

### ? B-2.1. ������ ������������ �����������

**������� ������ �������������� �����������:**
- `MainWindow.simulation_manager.state_bus` - ����������� ���� ��������
- `src/pneumo/enums.py` - `ReceiverVolumeMode.NO_RECALC` / `ADIABATIC_RECALC`
- ������� ������� �������� ��� ���������� �������

### ? B-2.2. ������������� ����������

#### 1. ����� ������ � PneumoPanel
```python
receiver_volume_changed = Signal(float, str)  # volume (m?), mode ('MANUAL'/'GEOMETRIC')
```
- ����������� ��� ��������� ������� ������
- ����������� ��� ��������� �������������� ��������
- ����������� ��� ������������ �������

#### 2. ����� ������ � StateBus
```python
set_receiver_volume = Signal(float, str)  # volume (m?), ReceiverVolumeMode
```

#### 3. ���������� � MainWindow
```python
@Slot(float, str)
def _on_receiver_volume_changed(self, volume: float, mode: str):
    # Map UI modes to ReceiverVolumeMode enum
    receiver_mode = 'NO_RECALC' if mode == 'MANUAL' else 'ADIABATIC_RECALC'
    
    # Emit signal to physics thread
    self.simulation_manager.state_bus.set_receiver_volume.emit(volume, receiver_mode)
```

#### 4. ���������� � PhysicsWorker
```python
@Slot(float, str)
def set_receiver_volume(self, volume: float, mode: str):
    # Store volume and mode for gas network updates
    self.receiver_volume = volume
    self.receiver_volume_mode = mode
    # TODO: Update actual ReceiverState when gas network is integrated
```

### ? B-2.3. ������� UI ������� �� �����������������

| UI ����� | UI �������� | ReceiverVolumeMode | ������������� |
|----------|-------------|-------------------|---------------|
| `MANUAL` | "������ �����" | `NO_RECALC` | ����� �� ������ �� p/T |
| `GEOMETRIC` | "�������������� ������" | `ADIABATIC_RECALC` | �������� �� ������������� |

### ? B-2.4. ���������� � 3D ������

������� �������� ���������� � QML:
```python
receiver_params = {
    'receiverDiameter': diameter * 1000,  # m ? mm
    'receiverLength': length * 1000,      # m ? mm  
    'receiverVolume': volume * 1000000,   # m? ? cm?
}
```

### ?? B-2.5. ���������� ������������

```
=== B-2: Test receiver volume integration ===
+ PneumoPanel has receiver_volume_changed signal
+ StateBus has set_receiver_volume signal

--- Signal emission test ---
+ receiver_volume_changed signal emitted: 1 times
+ Signal parameters captured
?? ����� ������: �������������� (0.016 �?)

--- Parameter flow test ---  
+ Mapping: MANUAL -> NO_RECALC
+ Mapping: GEOMETRIC -> ADIABATIC_RECALC

? UI signals work
? Mode mapping implemented
? StateBus signals added
```

### ?? B-2.6. ����� ���������� (������ �����)

```
User changes volume mode ?
PneumoPanel.volume_mode_combo.currentIndexChanged ?
PneumoPanel._on_volume_mode_changed() ?
PneumoPanel.receiver_volume_changed.emit(volume, 'MANUAL'/'GEOMETRIC') ?
MainWindow._on_receiver_volume_changed(volume, mode) ?
Map UI mode ? ReceiverVolumeMode ?
StateBus.set_receiver_volume.emit(volume, 'NO_RECALC'/'ADIABATIC_RECALC') ?
PhysicsWorker.set_receiver_volume(volume, mode) ?
Update ReceiverState (when gas network integrated) ?
StateSnapshot.tank.volume = volume ?
UI updated with new tank state
```

### ? B-2.7. ����������� ������

- [x] B-2.2.1. �������� ������ `receiver_volume_changed`
- [x] B-2.2.2. ������� ���������� � MainWindow `_on_receiver_volume_changed`
- [x] B-2.2.3. ������� � 3D ������ (�������� �������� ��������)
- [x] B-2.3. ������� UI ������� �� `ReceiverVolumeMode`
- [x] B-2.4. ������������ ����������

### ?? B-2.8. ������ � �������������

**���������� � ����������������� ������� ��������� �����������:**

1. **UI ? Signals**: �������� ?
2. **Signals ? MainWindow**: �������� ?  
3. **MainWindow ? StateBus**: �������� ?
4. **StateBus ? PhysicsWorker**: �������� ?
5. **Mode Mapping**: �������� ?
6. **3D Scene Integration**: �������� ?

**������ ���������� � ������� �����** ��������� ������������� ��� ������� ���������, ����� `PhysicsWorker.set_receiver_volume()` ����� ��������� �������� ������� `ReceiverState`.

---

**������**: ? **���������**  
**��������� ���**: **B-3. ������������ ������ ���������� � ���������� ����������**