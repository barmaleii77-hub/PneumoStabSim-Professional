#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
������� �������� ��-2: ������� �� + ��� 0.001�
"""

import sys
from PySide6.QtWidgets import QApplication

# ������� ����������
app = QApplication.instance() or QApplication(sys.argv)

# ������������� ������
from src.ui.panels.panel_geometry import GeometryPanel

print("=" * 70)
print("��-2: �������� ������ �� + ��� 0.001�")
print("=" * 70)

# ������� ������
panel = GeometryPanel()

# �������� 1: ������� ����� ��������� � ������
print("\nPROVERKA 1: Novye slaydery v metrakh")
print(f"   rod_diameter_m_slider:       {hasattr(panel, 'rod_diameter_m_slider')}")
print(f"   piston_rod_length_m_slider:  {hasattr(panel, 'piston_rod_length_m_slider')}")  
print(f"   piston_thickness_m_slider:   {hasattr(panel, 'piston_thickness_m_slider')}")

# �������� 2: ���������� ������ ��������� � ��
print("\nPROVERKA 2: Starye slaydery v mm udaleny")
print(f"   rod_diameter_slider:         {not hasattr(panel, 'rod_diameter_slider')} (dolzhno byt' True)")
print(f"   piston_rod_length_slider:    {not hasattr(panel, 'piston_rod_length_slider')} (dolzhno byt' True)")
print(f"   piston_thickness_slider:     {not hasattr(panel, 'piston_thickness_slider')} (dolzhno byt' True)")

# ��������� � �������
print("\nPROVERKA 4: Parametry v slovare")
params = panel.get_parameters()
print(f"   'rod_diameter_m' v parameters:     {('rod_diameter_m' in params)} = {params.get('rod_diameter_m', 'NE NAYDENO')}")
print(f"   'piston_rod_length_m' v parameters: {('piston_rod_length_m' in params)} = {params.get('piston_rod_length_m', 'NE NAYDENO')}")
print(f"   'piston_thickness_m' v parameters:  {('piston_thickness_m' in params)} = {params.get('piston_thickness_m', 'NE NAYDENO')}")
print(f"   'rod_diameter' OTSUTSTVUET:         {('rod_diameter' not in params)} (dolzhno byt' True)")
print(f"   'piston_rod_length' OTSUTSTVUET:    {('piston_rod_length' not in params)} (dolzhno byt' True)")  
print(f"   'piston_thickness' OTSUTSTVUET:     {('piston_thickness' not in params)} (dolzhno byt' True)")

# �������� ��������
print("\n" + "=" * 70)
all_checks = [
    hasattr(panel, 'rod_diameter_m_slider'),
    hasattr(panel, 'piston_rod_length_m_slider'),
    hasattr(panel, 'piston_thickness_m_slider'),
    not hasattr(panel, 'rod_diameter_slider'),
    not hasattr(panel, 'piston_rod_length_slider'),
    not hasattr(panel, 'piston_thickness_slider'),
    'rod_diameter_m' in params,
    'piston_rod_length_m' in params,
    'piston_thickness_m' in params,
    'rod_diameter' not in params,
    'piston_rod_length' not in params,
    'piston_thickness' not in params
]

if all(all_checks):
    print("MS-2: VSE PROVERKI PROYDENY USPESHNO!")
    print("Vse lineynye parametry pervedeny v SI edinicy (metry)")
    print("=" * 70)
    sys.exit(0)
else:
    print("MS-2: NEKOTORYE PROVERKI NE PROYDENY")
    print(f"   Proydeno: {sum(all_checks)}/{len(all_checks)}")
    print("=" * 70)
    sys.exit(1)