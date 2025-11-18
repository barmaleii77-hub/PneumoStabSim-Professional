# Release Playbooks

Place packaging guides, release checklists, and distribution workflows here.

## Current Coordination Notes (2025-11-24 Refresh)
- **Branch state**: локальная ветка `work` не имеет настроенного upstream; перед
  подготовкой релизных артефактов требуется назначить целевой бранч и повторить
  сверку конфликтов.
- **Test gate**: после каждого обновления расписания запускайте
  `python scripts/testing_entrypoint.py`, чтобы подтвердить, что окружение,
  зависящее от PySide6/Qt, остаётся в рабочем состоянии на Linux контейнерах.
- **Communication**: ссылайтесь на недельные вехи в
  `docs/operations/milestones.md` (включая добавленную неделю 53) и фиксируйте
  прогресс в заметках для релизного брифинга команды.
