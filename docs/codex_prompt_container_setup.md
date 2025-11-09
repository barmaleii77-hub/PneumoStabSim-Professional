# CODEX Tasking — Container automation & headless QA

This prompt guides CODEX GPT (or another automation agent) when preparing the
containerised build-and-test environment for the **`feature/hdr-assets-migration`
branch** of PneumoStabSim Professional. It focuses exclusively on tooling,
automation, and developer-experience assets; the simulator's runtime logic,
rendering code, physics, and shader implementations must stay untouched.

## System / tasking prompt
Paste the following block into the assistant's system message to brief CODEX:

```text
Ты работаешь в репозитории PneumoStabSim-Professional, ветка feature/hdr-assets-migration.
Цель — подготовить контейнерную среду и скрипты автозапуска, которые:

• Собирают и запускают приложение в контейнере (Linux, headless);
• Автоматически догружают недостающие библиотеки/модули;
• Прогоняют весь пайплайн качества и тестов (ruff, mypy, qmllint, валидация шейдеров, pytest);
• Делают смоук-ран приложения в двух RHI бэкендах (OpenGL/Vulkan) через Xvfb и собирают единый отчёт логов;
• Готовят VS/VS Code профиль запуска;
• Ничего не ломают в рендере/симе (не меняют физику/шейдеры/настройки проекта).

НЕ ИЗМЕНЯЙ бизнес-код симулятора, PBR/IBL и физику. Вся логика — только в Docker/скриптах/CI.

Технические требования
• Python 3.13.x, PySide6 6.10.0 / Qt 6.10.1 (как в логах запуска).
• Qt CLI-утилиты в контейнере: qmllint, qsb (через aqtinstall Qt 6.10.1).
• Headless рендер: Xvfb + Mesa (llvmpipe OpenGL), Lavapipe (Vulkan).
• Проверка шейдеров: нет BOM, #version первой строкой, профили GLSL валидные.
• Параметры запуска Qt: тесты в OpenGL и Vulkan (QSG_RHI_BACKEND=opengl / QSG_RHI_BACKEND=vulkan), QT_QUICK_CONTROLS_STYLE=Fusion, headless-профиль Qt (QT_QPA_PLATFORM=offscreen, QT_QUICK_BACKEND=software) при отсутствии DISPLAY и VK_ICD_FILENAMES для Lavapipe. Эти же дефолты прописаны в env.sample и применяются configure_qt_environment().
• Логи из logs/ и reports/ собрать в /workdir/reports (единый архив/папка артефактов).
• Не хардкодить рабочие параметры симулятора — читать из config/app_settings.json, тесты запускаются без HDR-ассетов.

План действий (выполняй последовательно)
1. Dockerfile (debian/bookworm devcontainer) с Xvfb, Mesa, Lavapipe, aqtinstall и Qt 6.10.1.
2. Скрипты: entrypoint, xvfb_wrapper, install_deps (умный bootstrap), shader_sanity, collect_logs, run_all.
3. Makefile цели: build, shell, test, test-opengl, test-vulkan, verify-all, analyze-logs.
4. Devcontainer профиль, VS Code launch.json, инструкции для Visual Studio.
5. GitHub Action (опционально) — build + scripts/run_all.sh.
6. Проверка: docker build, make verify-all, смоук-раны app.py --test-mode (OpenGL/Vulkan), отчёты собраны.
```

## Usage notes
- Keep the prompt colocated with infrastructure files (`Dockerfile`,
  `scripts/`, `tools/`, `.devcontainer/`, `.github/workflows/`).
- Cross-reference `docs/RENOVATION_PHASE_1_ENVIRONMENT_AND_CI_PLAN.md` for the
  broader CI rollout before expanding the automation surface.
- When updating the tooling scripts, maintain idempotency (re-running them must
  not corrupt the environment) and never mutate simulator settings or assets.

## Visual Studio & VS Code launch guidance
- **VS Code**: open the repository inside the provided devcontainer; launch the
  `PneumoStabSim (OpenGL, test-mode)` or `PneumoStabSim (Vulkan, test-mode)`
  configurations from `.vscode/launch.json`. Both set `QSG_RHI_BACKEND`,
  inherit `QT_QUICK_CONTROLS_STYLE=Fusion` и используют XCB-плагин для GUI.
- **Visual Studio (Windows)**: configure your Python debug profile to use
  Python 3.13, set `QSG_RHI_BACKEND=opengl` (or `vulkan` when the Lavapipe ICD
  is installed), add `QT_QPA_PLATFORM=windows`, and point the startup script to
  `app.py --test-mode`. Logs should continue to land in `logs/run.log`.

Document updated alongside the container automation assets to keep the agent
brief and the implemented tooling in sync.
