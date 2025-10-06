#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
������� �������� ��-1: ��������� ��������� ��������
"""

import sys
from PySide6.QtWidgets import QApplication

# ������� ����������
app = QApplication.instance() or QApplication(sys.argv)

# ������������� ������
from src.ui.panels.panel_geometry import GeometryPanel

print("=" * 60)
print("��-1: �������� ��������� ��������� ��������")
print("=" * 60)

# ������� ������
panel = GeometryPanel()

# �������� 1: ������� ����� ���������
print("\n? �������� 1: ����� ��������")
print(f"   cyl_diam_m_slider:  {hasattr(panel, 'cyl_diam_m_slider')}")
print(f"   stroke_m_slider:    {hasattr(panel, 'stroke_m_slider')}")
print(f"   dead_gap_m_slider:  {hasattr(panel, 'dead_gap_m_slider')}")

# �������� 2: ���������� ������ ���������
print("\n? �������� 2: ������ �������� �������")
print(f"   bore_head_slider:   {not hasattr(panel, 'bore_head_slider')} (������ ���� True)")
print(f"   bore_rod_slider:    {not hasattr(panel, 'bore_rod_slider')} (������ ���� True)")

# �������� 3: ��������� ���������
if hasattr(panel, 'cyl_diam_m_slider'):
    print("\n?? �������� 3a: ��������� cyl_diam_m_slider")
    slider = panel.cyl_diam_m_slider
    print(f"   minimum:   {slider.minimum()} (��������� 0.030)")
    print(f"   maximum:   {slider.maximum()} (��������� 0.150)")
    print(f"   value:     {slider.value()} (��������� 0.080)")
    print(f"   step:      {slider.step()} (��������� 0.001)")
    print(f"   decimals:  {slider.decimals()} (��������� 3)")
    print(f"   units:     '{slider.units()}' (��������� '�')")

if hasattr(panel, 'stroke_m_slider'):
    print("\n?? �������� 3b: ��������� stroke_m_slider")
    slider = panel.stroke_m_slider
    print(f"   minimum:   {slider.minimum()} (��������� 0.100)")
    print(f"   maximum:   {slider.maximum()} (��������� 0.500)")
    print(f"   value:     {slider.value()} (��������� 0.300)")
    print(f"   step:      {slider.step()} (��������� 0.001)")
    print(f"   decimals:  {slider.decimals()} (��������� 3)")
    print(f"   units:     '{slider.units()}' (��������� '�')")

if hasattr(panel, 'dead_gap_m_slider'):
    print("\n?? �������� 3c: ��������� dead_gap_m_slider")
    slider = panel.dead_gap_m_slider
    print(f"   minimum:   {slider.minimum()} (��������� 0.000)")
    print(f"   maximum:   {slider.maximum()} (��������� 0.020)")
    print(f"   value:     {slider.value()} (��������� 0.005)")
    print(f"   step:      {slider.step()} (��������� 0.001)")
    print(f"   decimals:  {slider.decimals()} (��������� 3)")
    print(f"   units:     '{slider.units()}' (��������� '�')")

# �������� 4: ��������� � �������
print("\n?? �������� 4: ��������� � �������")
params = panel.get_parameters()
print(f"   'cyl_diam_m' � parameters:  {('cyl_diam_m' in params)} = {params.get('cyl_diam_m', '�� �������')}")
print(f"   'stroke_m' � parameters:    {('stroke_m' in params)} = {params.get('stroke_m', '�� �������')}")
print(f"   'dead_gap_m' � parameters:  {('dead_gap_m' in params)} = {params.get('dead_gap_m', '�� �������')}")
print(f"   'bore_head' �����������:    {('bore_head' not in params)} (������ ���� True)")
print(f"   'bore_rod' �����������:     {('bore_rod' not in params)} (������ ���� True)")

# �������� ��������
print("\n" + "=" * 60)
all_checks = [
    hasattr(panel, 'cyl_diam_m_slider'),
    hasattr(panel, 'stroke_m_slider'),
    hasattr(panel, 'dead_gap_m_slider'),
    not hasattr(panel, 'bore_head_slider'),
    not hasattr(panel, 'bore_rod_slider'),
    'cyl_diam_m' in params,
    'stroke_m' in params,
    'dead_gap_m' in params,
    'bore_head' not in params,
    'bore_rod' not in params,
]

if all(all_checks):
    print("?? ��-1: ��� �������� �������� �������!")
    print("=" * 60)
    sys.exit(0)
else:
    print("? ��-1: ��������� �������� �� ��������")
    print(f"   ��������: {sum(all_checks)}/{len(all_checks)}")
    print("=" * 60)
    sys.exit(1)
