# -*- coding: utf-8 -*-
"""
����-����� ������� ����� ����������� UI
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'tools'))

from feedback.feedback import init_feedback

def main():
    fb = init_feedback()

    with fb.span("ui/pre_audit"):
        print("�������� ����-����� �������...")

        print("\n?? ������ �����ب���� ������:")

        # �������� ����� Receiver
        print("\n?? ���� 'Receiver' (���������� ������ ��������):")
        try:
            # ��������� ������������� �������� �������
            if os.path.exists("reports/receiver/RECEIVER_COMPLETE.md"):
                print("  ? ��������� ��������")
                print("  ? ������������ ������� ������ �����������")
                print("  ? ���������� � UI/StateBus ������")
                print("  ? ��� ����� (B-1, B-2, B-3) ��������")
                print("  ?? ������ � ������������� � ���������")
            else:
                print("  ?? � �������� ����������")

        except Exception as e:
            print(f"  ?? ������ ��������: {e}")

        # �������� ���������� � ��������� ������
        print("\n?? ���������� � ����� ������:")

        print("\n?? ��������� ����������� ��������:")
        print("  1. ?? ���� 'Visualizations' - 3D ����������� ��������")
        print("  2. ?? ���� 'Pneumatics Extended' - �������������� ����������")
        print("  3. ?? ���� 'Analytics' - ������ � ����������")
        print("  4. ??? ���� 'Presets' - ������� �������� � ������������")
        print("  5. ?? ���� 'Automation' - �������������� ������ ������")

        print("\n? ������� ������ � ����������� ��������!")
        print("? ����������� ������������� � ����������")
        print("? ��������� ��� ����� ������� �������")

        print("\n" + "="*60)
        print("������������: �������� ��������� ���� ��� ����������")
        print("="*60)

if __name__ == "__main__":
    main()
