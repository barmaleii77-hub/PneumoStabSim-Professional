# GIT COMMIT INSTRUCTIONS - PROMPT #1 (60% Complete)

## ? FILES TO COMMIT

### Modified Files (3):
```bash
git add src/ui/main_window.py
git add src/ui/panels/panel_geometry.py
git add src/ui/panels/panel_pneumo.py
```

### New Reports (6):
```bash
git add reports/ui/STEP_1_COMPLETE.md
git add reports/ui/strings_changed_step1.csv
git add reports/ui/STEP_2_PANELS_COMPLETE.md
git add reports/ui/strings_changed_complete.csv
git add reports/ui/PROGRESS_UPDATE.md
git add reports/ui/FINAL_STATUS_REPORT.md
git add reports/ui/GIT_COMMIT_INSTRUCTIONS.md
```

---

## ?? COMMIT MESSAGE (Russian)

```
feat(ui): ����������� �������� ���� � ������� (60% ���������)

���������:
? ������� ���� (main_window.py):
  - ������������ �������� (����� ������, ������� �����)
  - ������� ������ ����� (QTabWidget)
  - ������ ����������� ����, �������, ������-����
  - 47 ����� UI ����������

? GeometryPanel (panel_geometry.py):
  - ��� ���������, ������, ������� �� �������
  - �������� QComboBox ��� ������ ��������
  - ��� ��������� ��������� �� �������
  - 35 ����� UI ����������

? PneumoPanel (panel_pneumo.py):
  - ��� ���������, ������, ������� �� �������
  - �������� QComboBox ��� ������ ������ ��������
  - ��� ��������� ��������� �� �������
  - 28 ����� UI ����������

�������:
- ������ ��������: 3
- ����� ����: ~390
- ����� UI ����������: 110+
- QComboBox ���������: 2
- ������ ����������: 0

����������:
? ������� ����� �� ��� ������
? ������ �� �������� ������
? ���������� ��� ������������
? ������� ���������
? ��� �����������
? ��������� ��������/��������
? ��������� ���������� ������ (QComboBox)

������: ������ � ������������

��. �����������: reports/ui/FINAL_STATUS_REPORT.md
```

---

## ?? EXECUTION COMMANDS

### 1. Stage all changes:
```bash
git add src/ui/main_window.py src/ui/panels/panel_geometry.py src/ui/panels/panel_pneumo.py
git add reports/ui/
```

### 2. Commit with detailed message:
```bash
git commit -F- <<EOF
feat(ui): ����������� �������� ���� � ������� (60% ���������)

���������:
? ������� ���� (main_window.py):
  - ������������ �������� (����� ������, ������� �����)
  - ������� ������ ����� (QTabWidget)
  - ������ ����������� ����, �������, ������-����
  - 47 ����� UI ����������

? GeometryPanel (panel_geometry.py):
  - ��� ���������, ������, ������� �� �������
  - �������� QComboBox ��� ������ ��������
  - ��� ��������� ��������� �� �������
  - 35 ����� UI ����������

? PneumoPanel (panel_pneumo.py):
  - ��� ���������, ������, ������� �� �������
  - �������� QComboBox ��� ������ ������ ��������
  - ��� ��������� ��������� �� �������
  - 28 ����� UI ����������

�������:
- ������ ��������: 3
- ����� ����: ~390
- ����� UI ����������: 110+
- QComboBox ���������: 2
- ������ ����������: 0

����������:
? ������� ����� �� ��� ������
? ������ �� �������� ������
? ���������� ��� ������������
? ������� ���������
? ��� �����������
? ��������� ��������/��������
? ��������� ���������� ������ (QComboBox)

������: ������ � ������������

��. �����������: reports/ui/FINAL_STATUS_REPORT.md
EOF
```

### 3. Push to repository:
```bash
git push origin master
```

---

## ?? VERIFICATION

### Before commit:
```bash
# Check status
git status

# Review changes
git diff src/ui/main_window.py
git diff src/ui/panels/panel_geometry.py
git diff src/ui/panels/panel_pneumo.py
```

### After commit:
```bash
# Verify commit
git log -1 --stat

# Verify push
git log origin/master..HEAD
```

---

## ?? ALTERNATIVE: Create branch first

If you want to experiment before merging to master:

```bash
# Create feature branch
git checkout -b feature/ui-russification

# Stage, commit, push
git add src/ui/ reports/ui/
git commit -m "feat(ui): ����������� �������� ���� � ������� (60%)"
git push -u origin feature/ui-russification

# Later, merge to master
git checkout master
git merge feature/ui-russification
git push origin master
```

---

## ? COMMIT CHECKLIST

- [ ] All files staged (`git status` shows correct files)
- [ ] No compilation errors (`get_errors` returned clean)
- [ ] Reports created and staged
- [ ] Commit message is clear and detailed
- [ ] Branch is up to date with remote
- [ ] Push successful

---

**Ready to commit:** ? YES
**Recommended action:** Commit to master OR create feature branch
**Next step after commit:** Create tests (`tests/ui/test_ui_layout.py`)
