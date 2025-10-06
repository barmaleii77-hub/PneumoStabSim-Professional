# ��-2: ���������� ���� �������� ���������� � �� � ���� 0.001�

## ��������� ?

����: 2024-01-XX  
������: **���������**  

### ����
�������� ��� �������� ��������� � GeometryPanel � �������� �� (�����) � ������ ����� 0.001� � decimals=3.

### ���������

#### 1. Frame Dimensions (������� ����)
**��:**
```python
# Wheelbase: step=0.1, decimals=1  
# Track: step=0.1, decimals=1
```

**�����:**
```python
# Wheelbase: minimum=2.000, maximum=4.000, value=3.200, step=0.001, decimals=3
# Track: minimum=1.000, maximum=2.500, value=1.600, step=0.001, decimals=3
```

#### 2. Suspension Geometry (��������� ��������)  
**��:**
```python
# frame_to_pivot: step=0.05, decimals=2
# lever_length: step=0.05, decimals=2
# rod_position: step=0.05, decimals=2
```

**�����:**
```python  
# frame_to_pivot: minimum=0.300, maximum=1.000, value=0.600, step=0.001, decimals=3
# lever_length: minimum=0.500, maximum=1.500, value=0.800, step=0.001, decimals=3
# rod_position: minimum=0.300, maximum=0.900, value=0.600, step=0.001, decimals=3
```

#### 3. Default Values (�������� �� ���������)
��������� ��� ��������������� � ����� ���������:
```python
defaults = {
    'wheelbase': 3.200,       # ���� 3.2
    'track': 1.600,           # ���� 1.6  
    'frame_to_pivot': 0.600,  # ���� 0.6
    'lever_length': 0.800,    # ���� 0.8
    'rod_position': 0.600,    # ���� 0.6
    # ... ������� ��� ��� � �� �� ��-1
}
```

### ���������

��� �������� ��������� ������ ����������:
- **������� ��:** ����� (�)
- **������ ���:** 0.001 � (1 ��)  
- **��������:** decimals=3
- **���������������:** ��������������� ���������

### ����� ��������

1. `src/ui/panels/panel_geometry.py` - �������� ���������
   - `_create_frame_group()` - ��������� wheelbase/track ��������
   - `_create_suspension_group()` - ��������� frame_to_pivot/lever_length ��������  
   - `_set_default_values()` - ��������� ��������� ��������

### ���������

- ? ���������� ��� ������
- ? ������ ������ �������
- ? ��� �������� ��������� � ��
- ? ������ ��� 0.001 ��� ���� �������� ����������
- ? ������������� �������� decimals=3

### ��������� ���

**��-3:** ���������� ������ dependency resolution ��� ������ � ������ ��������� ��.

---
**������:** ��-2 �������� �������. ����� � �������� �� ��-3.