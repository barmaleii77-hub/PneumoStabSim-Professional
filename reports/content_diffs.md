# Контентный diff по ключевым файлам (текущая: `merge/best-of`)


## origin


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `e570895aeb17`

```diff

--- origin:app.py

+++ local:app.py

@@ -10,6 +10,7 @@

 import argparse
 import subprocess
 from pathlib import Path
+import json

 # =============================================================================
 # Накопление warnings/errors
@@ -113,15 +114,12 @@

 # =============================================================================


-def check_python_compatibility():
-    """Check Python version and warn about potential issues"""
+def check_python_compatibility() -> None:
+    """Проверка версии Python: проект таргетирует Python 3.13+"""
     version = sys.version_info
-
-    if version < (3, 8):
-        log_error("Python 3.8+ required. Please upgrade Python.")
+    if version < (3, 13):
+        log_error("Python 3.13+ required. Please upgrade Python.")
         sys.exit(1)
-    elif version >= (3, 12):
-        log_warning("Python 3.12+ detected. Some packages may have compatibility issues.")


 check_python_compatibility()
@@ -153,8 +151,8 @@


         try:
             major, minor = qt_version.split('.')[:2]
-            if int(major) == 6 and int(minor) < 8:
-                log_warning(f"Qt {qt_version} - ExtendedSceneEnvironment may be limited")
+            if int(major) == 6 and int(minor) < 10:
+                log_warning(f"Qt {qt_version} detected. Some 6.10+ features may be unavailable")
         except (ValueError, IndexError):
             log_warning(f"Could not parse Qt version: {qt_version}")

@@ -171,16 +169,18 @@

 # =============================================================================


-def setup_logging():
-    """Настройка логирования - ВСЕГДА активно"""
+def setup_logging(verbose_console: bool = False):
+    """Настройка логирования - ВСЕГДА активно
+
+    Args:
+        verbose_console: Включать ли вывод логов в консоль (аргумент --verbose)
+    """
     try:
         from src.common.logging_setup import init_logging, rotate_old_logs

         logs_dir = Path("logs")

-        # ✅ НОВОЕ: Ротация старых логов (оставляем только 10 последних)
-        # Политика проекта: всегда начинать с чистых логов
-        # Стираем старые логи на запуске (keep_count=0)
+        # Политика проекта: начинаем с чистых логов
         rotate_old_logs(logs_dir, keep_count=0)

         # Инициализируем логирование с ротацией
@@ -189,7 +189,7 @@

             logs_dir,
             max_bytes=10 * 1024 * 1024,  # 10 MB на файл
             backup_count=5,               # Держим 5 backup файлов
-            console_output=False          # НЕ выводим в консоль
+            console_output=bool(verbose_console)  # Включаем по запросу
         )

         logger.info("=" * 60)
@@ -201,6 +201,9 @@

         logger.info(f"Qt: {qVersion()}")
         logger.info(f"Platform: {sys.platform}")
         logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
+
+        if verbose_console:
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `5f3bddc89ca3`

```diff

--- origin:requirements.txt

+++ local:requirements.txt

@@ -1,5 +1,5 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.9-3.13 (рекомендуется 3.11-3.13)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
@@ -16,23 +16,22 @@

 pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=7.0.0            # Тестирование
-PyYAML>=6.0              # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
 # trimesh>=3.15.0         # 3D mesh обработка (опционально)
 # pyqtgraph>=0.12.0       # Быстрые графики (опционально)
-
-# Производительность
 # numba>=0.56.0           # JIT компиляция (опционально)
 # cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
 # - Windows 10/11 (Python 3.11-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.10-3.12)
-# - macOS 12+ (Python 3.11-3.12)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
 # 1. Требуется PySide6 6.10+ из-за использования Fog и dithering

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `b053bb28eaf9`

```diff

--- origin:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,6 +1,8 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
@@ -17,6 +19,8 @@

 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false

     // ===============================================================
     // 🚀 SIGNALS - ACK для Python после применения обновлений
@@ -202,12 +206,6 @@

     property real iblRotationDeg: 0
     property real iblIntensity: 1.3

-    // ❌ Больше НЕ связываем фон со включением IBL
-    // onIblEnabledChanged: {
-    //     iblLightingEnabled = iblEnabled
-    //     iblBackgroundEnabled = iblEnabled
-    // }
-
     property bool fogEnabled: true
     property color fogColor: "#b0c4d8"
     property real fogDensity: 0.12
@@ -557,10 +555,6 @@

     // ✅ COMPLETE BATCH UPDATE SYSTEM (All functions implemented)
     // ===============================================================

-    // ===============================================================
-    // ✅ ENHANCED BATCH UPDATE SYSTEM (Conflict Resolution)
-    // ===============================================================
-
     function applyBatchedUpdates(updates) {
         console.log("🚀 Applying batched updates with conflict resolution:", Object.keys(updates))

@@ -674,38 +668,38 @@

             if (params.key_light.color !== undefined) keyLightColor = params.key_light.color
             if (params.key_light.angle_x !== undefined) keyLightAngleX = params.key_light.angle_x
             if (params.key_light.angle_y !== undefined) keyLightAngleY = params.key_light.angle_y
-+            if (params.key_light.casts_shadow !== undefined) keyLightCastsShadow = !!params.key_light.casts_shadow
-+            if (params.key_light.bind_to_camera !== undefined) keyLightBindToCamera = !!params.key_light.bind_to_camera
-+            if (params.key_light.position_x !== undefined) keyLightPosX = Number(params.key_light.position_x)
-+            if (params.key_light.position_y !== undefined) keyLightPosY = Number(params.key_light.position_y)
+            if (params.key_light.casts_shadow !== undefined) keyLightCastsShadow = !!params.key_light.casts_shadow
+            if (params.key_light.bind_to_camera !== undefined) keyLightBindToCamera = !!params.key_light.bind_to_camera
+            if (params.key_light.position_x !== undefined) keyLightPosX = Number(params.key_light.position_x)
+            if (params.key_light.position_y !== undefined) keyLightPosY = Number(params.key_light.position_y)
         }
         if (params.fill_light) {
             if (params.fill_light.brightness !== undefined) fillLightBrightness = params.fill_light.brightness
             if (params.fill_light.color !== undefined) fillLightColor = params.fill_light.color
-+            if (params.fill_light.casts_shadow !== undefined) fillLightCastsShadow = !!params.fill_light.casts_shadow
-+            if (params.fill_light.bind_to_camera !== undefined) fillLightBindToCamera = !!params.fill_light.bind_to_camera
-+            if (params.fill_light.position_x !== undefined) fillLightPosX = Number(params.fill_light.position_x)
-+            if (params.fill_light.position_y !== undefined) fillLightPosY = Number(params.fill_light.position_y)
+            if (params.fill_light.casts_shadow !== undefined) fillLightCastsShadow = !!params.fill_light.casts_shadow
+            if (params.fill_light.bind_to_camera !== undefined) fillLightBindToCamera = !!params.fill_light.bind_to_camera
+            if (params.fill_light.position_x !== undefined) fillLightPosX = Number(params.fill_light.position_x)
+            if (params.fill_light.position_y !== undefined) fillLightPosY = Number(params.fill_light.position_y)
         }
         if (params.rim_light) {
             if (params.rim_light.brightness !== undefined) rimLightBrightness = params.rim_light.brightness
             if (params.rim_light.color !== undefined) rimLightColor = params.rim_light.color
-+            if (params.rim_light.casts_shadow !== undefined) rimLightCastsShadow = !!params.rim_light.casts_shadow
-+            if (params.rim_light.bind_to_camera !== undefined) rimLightBindToCamera = !!params.rim_light.bind_to_camera
-+            if (params.rim_light.position_x !== undefined) rimLightPosX = Number(params.rim_light.position_x)
-+            if (params.rim_light.position_y !== undefined) rimLightPosY = Number(params.rim_light.position_y)
+            if (params.rim_light.casts_shadow !== undefined) rimLightCastsShadow = !!params.rim_light.casts_shadow
+            if (params.rim_light.bind_to_camera !== undefined) rimLightBindToCamera = !!params.rim_light.bind_to_camera
+            if (params.rim_light.position_x !== undefined) rimLightPosX = Number(params.rim_light.position_x)
+            if (params.rim_light.position_y !== undefined) rimLightPosY = Number(params.rim_light.position_y)
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `d378637cb82c`

```diff

--- origin:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -14,17 +14,47 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
     property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
@@ -49,6 +79,12 @@

     }

     // Monitor texture status using Timer polling (Texture has no statusChanged signal!)
+<<<<<<< HEAD
+    property int _lastStatusA: -1
+    property int _lastStatusB: -1
+
+    // Polling-based status check for both textures
+=======
     property int _lastStatus: -1  // Начинаем с -1 вместо Texture.Null

     onProbeChanged: {
@@ -59,11 +95,53 @@

     }

     // Polling-based status check (since Texture doesn't emit statusChanged signal)
+>>>>>>> sync/remote-main
     Timer {
         interval: 100  // Check every 100ms
         running: true
         repeat: true
         onTriggered: {
+<<<<<<< HEAD
+            controller._checkStatusFor(texA, 0)
+            controller._checkStatusFor(texB, 1)
+        }
+    }
+    function _statusToString(s) {
+        return s === Texture.Null ? "Null" :
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `2117cc0e6ee9`

```diff

--- origin:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -466,18 +466,29 @@


     Args:
         log_dir: Директория с логами
+<<<<<<< HEAD
+        keep_count: Сколько последних файлов оставить
+=======
         keep_count: Сколько последних файлов оставить (0 = удалить все)
+>>>>>>> sync/remote-main
     """
     if not log_dir.exists():
         return

     # Находим все лог-файлы с timestamp
     log_files = sorted(
+<<<<<<< HEAD
+        log_dir.glob("PneumoStabSim_*.log"),
+=======
         list(log_dir.glob("PneumoStabSim_*.log")),
+>>>>>>> sync/remote-main
         key=lambda p: p.stat().st_mtime,
         reverse=True
     )

+<<<<<<< HEAD
+    # Удаляем старые
+=======
     # Если keep_count == 0 — удаляем все timestamp-логи
     if keep_count <= 0:
         for lf in log_files:
@@ -497,6 +508,7 @@

         return

     # Обычный режим: оставляем N последних
+>>>>>>> sync/remote-main
     for old_log in log_files[keep_count:]:
         try:
             old_log.unlink()

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `3c3fbc11a8a9`

```diff

--- origin:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -342,6 +342,15 @@

         """Найти пары Python→QML событий для анализа синхронизации"""
         pairs = []

+<<<<<<< HEAD
+        # Группируем по timestamp
+        for i, event in enumerate(self.events):
+            if event["event_type"] == "SIGNAL_EMIT":
+                # Ищем соответствующий SIGNAL_RECEIVED в QML
+                signal_name = event["action"].replace("emit_", "")
+
+                # Ищем в следующих 1000ms
+=======
         # Сопоставление signal → QML функции (apply*Updates)
         signal_to_qml = {
             "lighting_changed": "applyLightingUpdates",
@@ -360,6 +369,7 @@

                 signal_name = event["action"].replace("emit_", "")
                 expected_qml_func = signal_to_qml.get(signal_name)

+>>>>>>> sync/remote-main
                 emit_time = datetime.fromisoformat(event["timestamp"])

                 for j in range(i+1, len(self.events)):
@@ -369,6 +379,11 @@

                     if (recv_time - emit_time).total_seconds() > 1.0:
                         break  # Слишком поздно

+<<<<<<< HEAD
+                    if (next_event["event_type"] == "SIGNAL_RECEIVED" and
+                        signal_name in next_event["action"]):
+
+=======
                     # ✅ Вариант 1: QML подписался на сигнал (onXxxChanged)
                     if (
                         next_event["event_type"] == "SIGNAL_RECEIVED"
@@ -388,6 +403,7 @@

                         and expected_qml_func is not None
                         and next_event["action"] == expected_qml_func
                     ):
+>>>>>>> sync/remote-main
                         pairs.append({
                             "python_event": event,
                             "qml_event": next_event,

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `80efb0048d5a`

```diff

--- origin:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,7 +23,10 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
 from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

@@ -31,8 +34,11 @@

 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
 from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
 # ✅ НОВОЕ: EventLogger для логирования QML вызовов
 from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -48,7 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
-
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -89,10 +98,13 @@

         self.ibl_logger = get_ibl_logger()
         log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")

+<<<<<<< HEAD
+=======
         # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
         self.event_logger = get_event_logger()
         self.logger.info("EventLogger initialized in MainWindow")

+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -178,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
+    # UI Construction - НОВАЯ СТРУКТРАА!
+=======
     # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -268,12 +284,15 @@


             qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
             print(f"    📂 Полный путь: {qml_url.toString()}")
+<<<<<<< HEAD
+=======

             # ✅ Устанавливаем базовую директорию QML для разрешения относительных путей
             try:
                 self._qml_base_dir = qml_path.parent.resolve()
             except Exception:
                 self._qml_base_dir = None
+>>>>>>> sync/remote-main

             self._qquick_widget.setSource(qml_url)

@@ -297,6 +316,16 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `20c2769950c7`

```diff

--- origin:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -316,25 +316,50 @@


     def _connect_signals(self):
         """Connect widget signals"""
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
         # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main

         self.logger.debug("Connecting signals...")

         # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
         # Мгновенные обновления канвы
         self.wheelbase_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('wheelbase', v))

+>>>>>>> sync/remote-main
         self.track_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('track', v))
         self.track_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('track', v))

         # Suspension geometry
+        self.frame_to_pivot_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('frame_to_pivot', v))
         self.frame_to_pivot_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('frame_to_pivot', v))
+<<<<<<< HEAD
+
+        self.lever_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+        self.lever_length_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+
+        self.rod_position_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('rod_position', v))
+=======
         self.frame_to_pivot_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('frame_to_pivot', v))

@@ -343,14 +368,51 @@

         self.lever_length_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('lever_length', v))

+>>>>>>> sync/remote-main
         self.rod_position_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('rod_position', v))
         self.rod_position_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('rod_position', v))

         # Cylinder dimensions
+        self.cylinder_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cylinder_length', v))
         self.cylinder_length_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('cylinder_length', v))
+<<<<<<< HEAD
+
+        # МШ-1: Параметры цилиндра
+        self.cyl_diam_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+        self.cyl_diam_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+
+        self.stroke_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
+        self.stroke_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `d663270ffc02`

```diff

--- origin:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -6,15 +6,27 @@

 import logging
 from typing import Any, Dict
 from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
 from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -140,8 +152,12 @@

         row.setSpacing(6)
         layout.addLayout(row)

+<<<<<<< HEAD
+        self._slider = QSlider(Qt.Horizontal, self)
+=======
         # ✅ ИСПРАВЛЕНО: используем QtWidgets.QSlider, чтобы избежать NameError
         self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
+>>>>>>> sync/remote-main
         steps = max(1, int(round((self._max - self._min) / self._step)))
         self._slider.setRange(0, steps)

@@ -292,6 +308,16 @@

     def _build_defaults(self) -> Dict[str, Any]:
         return {
             "lighting": {
+<<<<<<< HEAD
+                # ✅ Добавлены флаги теней для каждого источника света
+                "key": {"brightness": 1.2, "color": "#ffffff", "angle_x": -35.0, "angle_y": -40.0, "casts_shadow": True},
+                "fill": {"brightness": 0.7, "color": "#dfe7ff", "casts_shadow": False},
+                "rim": {"brightness": 1.0, "color": "#ffe2b0", "casts_shadow": False},
+                "point": {"brightness": 1000.0, "color": "#ffffff", "height": 2200.0, "range": 3200.0, "casts_shadow": False},
+            },
+            "environment": {
+                "background_mode": "skybox",
+=======
                 # Добавлены: cast_shadow, bind_to_camera, position_x/position_y для каждого источника
                 "key": {
                     "brightness": 1.2,
@@ -331,11 +357,16 @@

             },
             "environment": {
                 "background_mode": "skybox",  # 'color' | 'skybox'
+>>>>>>> sync/remote-main
                 "background_color": "#1f242c",
                 "ibl_enabled": True,
                 "ibl_intensity": 1.3,
                 "ibl_source": "../hdr/studio.hdr",
+<<<<<<< HEAD
+                "ibl_fallback": "assets/studio_small_09_2k.hdr",
+=======
                 "ibl_fallback": "../hdr/studio_small_09_2k.hdr",  # ✅ ИСПРАВЛЕНО: корректный относительный путь
+>>>>>>> sync/remote-main
                 "skybox_blur": 0.08,
                 "fog_enabled": True,
                 "fog_color": "#b0c4d8",
@@ -388,8 +419,13 @@

                 "dof_blur": 4.0,
                 "motion_blur": False,
... (обрезано)

```


## origin/codex/analyze-latest-commit-for-graphics-improvements


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `b39659f93d9a`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:app.py

+++ local:app.py

@@ -1,67 +1,55 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# ОПТИМИЗАЦИЯ: Кэширование системной информации
-# =============================================================================
-
-_system_info_cache = {}
-
-def get_cached_system_info():
-    """Получить кэшированную системную информацию"""
-    global _system_info_cache
-
-    if not _system_info_cache:
-        _system_info_cache = {
-            'platform': sys.platform,
-            'python_version': sys.version_info,
-            'encoding': sys.getdefaultencoding(),
-            'terminal_encoding': locale.getpreferredencoding(),
-            'qtquick3d_setup': qtquick3d_setup_ok
-        }
-
-    return _system_info_cache
-
-# =============================================================================
-# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports) - ОПТИМИЗИРОВАННАЯ
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+

 def setup_qtquick3d_environment():
-    """Set up QtQuick3D environment variables before importing Qt - ОПТИМИЗИРОВАННАЯ"""
-
-    # Проверяем кэш переменных окружения
+    """Set up QtQuick3D environment variables before importing Qt"""
     required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
     if all(var in os.environ for var in required_vars):
-        print("[CACHE] QtQuick3D environment already configured")
         return True

     try:
-        # First, do a minimal import to get Qt paths
         import importlib.util
         spec = importlib.util.find_spec("PySide6.QtCore")
         if spec is None:
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `59ba489b399c`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,19 +1,59 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
- * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.0)
- * 🚀 ПОЛНАЯ ИНТЕРАЦИЯ: Все параметры GraphicsPanel реализованы
- * ✅ Коэффициент преломления, IBL, расширенные эффекты, тонемаппинг
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
-
-    // ===============================================================
-    // 🚀 PERFORMANCE OPTIMIZATION LAYER (preserved)
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

     // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
@@ -133,21 +173,39 @@

     property color keyLightColor: "#ffffff"
     property real keyLightAngleX: -35
     property real keyLightAngleY: -40
+    property bool keyLightCastsShadow: true
+    property bool keyLightBindToCamera: false
+    property real keyLightPosX: 0.0
+    property real keyLightPosY: 0.0
     property real fillLightBrightness: 0.7
     property color fillLightColor: "#dfe7ff"
+    property bool fillLightCastsShadow: false
+    property bool fillLightBindToCamera: false
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `12220691fa6b`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,35 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

-    /** Expose the probe for consumers. */
-    property Texture probe: Texture {
-        id: hdrProbe
-        source: controller.primarySource
+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
     }
+    Texture {
+        id: texB
+        source: ""
+=======
+    /** Expose the probe for consumers. */
+    property Texture probe: hdrProbe
+
+    Texture {
+        id: hdrProbe
+        source: controller.primarySource
+>>>>>>> sync/remote-main
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
+        // Отправляем в Python для записи в файл
+        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
+            window.logIblEvent(logEntry)
+        }
+
+        // Также выводим в консоль для отладки
+        if (level === "ERROR" || level === "WARN") {
+            console.warn(logEntry)
+        } else {
+            console.log(logEntry)
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `0dae95c3ae77`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,12 +23,22 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -44,6 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -80,6 +94,17 @@

         # Logging
         self.logger = logging.getLogger(self.__class__.__name__)

+        # ✅ НОВОЕ: Инициализация IBL Signal Logger
+        self.ibl_logger = get_ibl_logger()
+        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
+
+<<<<<<< HEAD
+=======
+        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
+        self.event_logger = get_event_logger()
+        self.logger.info("EventLogger initialized in MainWindow")
+
+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -165,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
     # UI Construction - НОВАЯ СТРУКТРАА!
+=======
+    # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -222,6 +251,12 @@

             # CRITICAL: Set up QML import paths BEFORE loading any QML
             engine = self._qquick_widget.engine()

+            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Устанавливаем контекст ДО загрузки QML!
+            context = engine.rootContext()
+            context.setContextProperty("window", self)  # Экспонируем MainWindow в QML
+            log_ibl_event("INFO", "MainWindow", "IBL Logger registered in QML context (BEFORE QML load)")
+            print("    ✅ IBL Logger context registered BEFORE QML load")
+
             # Add Qt's QML import path
             from PySide6.QtCore import QLibraryInfo
             qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
@@ -249,6 +284,15 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `29a4cae63dc6`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,30 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # Отправляем сигналы без проверки подписчиков (она не работает в PySide6)
-            print(f"  📡 Отправка geometry_changed...")
             self.geometry_changed.emit(initial_geometry)
-            print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-
-            print(f"  📡 Отправка geometry_updated...")
             self.geometry_updated.emit(self.parameters.copy())
-            print(f"  📡 geometry_updated отправлен")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -323,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
-        # Frame dimensions - ТОЛЬКО valueEdited
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
+        # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main
+
+        self.logger.debug("Connecting signals...")
+
+        # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
-
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
+        # Мгновенные обновления канвы
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `68276b0087da`

```diff

--- origin/codex/analyze-latest-commit-for-graphics-improvements:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -5,15 +5,28 @@

 import json
 import logging
 from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
     QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -26,6 +39,12 @@

     QWidget,
 )

+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType
+

 class ColorButton(QPushButton):
     """Small color preview button that streams changes from QColorDialog."""
@@ -37,6 +56,7 @@

         self.setFixedSize(42, 28)
         self._color = QColor(initial_color)
         self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
         self._update_swatch()
         self.clicked.connect(self._open_dialog)

@@ -44,6 +64,7 @@

         return self._color

     def set_color(self, color_str: str) -> None:
+        """Программное изменение цвета (без логирования)"""
         self._color = QColor(color_str)
         self._update_swatch()

@@ -59,6 +80,9 @@


     @Slot()
     def _open_dialog(self) -> None:
+        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
+        self._user_triggered = True
+
         if self._dialog:
             return

@@ -77,13 +101,17 @@

             return
         self._color = color
         self._update_swatch()
-        self.color_changed.emit(color.name())
+
+        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
+        if self._user_triggered:
+            self.color_changed.emit(color.name())

... (обрезано)

```


## origin/copilot/add-ibl-control-features


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `3dbee948dd0a`

```diff

--- origin/copilot/add-ibl-control-features:app.py

+++ local:app.py

@@ -1,75 +1,55 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# ОПТИМИЗАЦИЯ: Кэширование системной информации
-# =============================================================================
-
-_system_info_cache = {}
-
-def get_cached_system_info():
-    """Получить кэшированную системнюю информацию"""
-    global _system_info_cache
-
-    if not _system_info_cache:
-        # Импортируем qVersion для получения версии Qt
-        try:
-            from PySide6.QtCore import qVersion
-            qt_version = qVersion()
-        except:
-            qt_version = "unknown"
-
-        _system_info_cache = {
-            'platform': sys.platform,
-            'python_version': sys.version_info,
-            'encoding': sys.getdefaultencoding(),
-            'terminal_encoding': locale.getpreferredencoding(),
-            'qtquick3d_setup': qtquick3d_setup_ok,
-            'qt_version': qt_version
-        }
-
-    return _system_info_cache
-
-# =============================================================================
-# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports) - ОПТИМИЗИРОВАННАЯ
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+

 def setup_qtquick3d_environment():
-    """Set up QtQuick3D environment variables before importing Qt - ОПТИМИЗИРОВАННАЯ"""
-
-    # Проверяем кэш переменных окружения
+    """Set up QtQuick3D environment variables before importing Qt"""
     required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
     if all(var in os.environ for var in required_vars):
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/copilot/add-ibl-control-features:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/copilot/add-ibl-control-features:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/copilot/add-ibl-control-features:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/copilot/add-ibl-control-features:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `21a65fce29cf`

```diff

--- origin/copilot/add-ibl-control-features:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,24 +1,41 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
- * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.8)
- * 🚀 ИСПРАВЛЕНО: Туман через объект Fog (Qt 6.10+)
- * ✅ Все свойства соответствуют официальной документации Qt Quick 3D
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)

     // ===============================================================
     // 🚀 QT VERSION DETECTION (для условной активации возможностей)
     // ===============================================================

-    readonly property var qtVersionParts: Qt.version.split('.')
-    readonly property int qtMajor: parseInt(qtVersionParts[0])
-    readonly property int qtMinor: parseInt(qtVersionParts[1])
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
     readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10

     // ✅ Условная поддержка dithering (доступно с Qt 6.10)
@@ -26,7 +43,17 @@

     readonly property bool canUseDithering: supportsQtQuick3D610Features

     // ===============================================================
-    // 🚀 PERFORMANCE OPTIMIZATION LAYER (preserved)
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

     // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
@@ -146,24 +173,39 @@

     property color keyLightColor: "#ffffff"
     property real keyLightAngleX: -35
     property real keyLightAngleY: -40
+    property bool keyLightCastsShadow: true
+    property bool keyLightBindToCamera: false
+    property real keyLightPosX: 0.0
+    property real keyLightPosY: 0.0
     property real fillLightBrightness: 0.7
     property color fillLightColor: "#dfe7ff"
+    property bool fillLightCastsShadow: false
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `12220691fa6b`

```diff

--- origin/copilot/add-ibl-control-features:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,35 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

-    /** Expose the probe for consumers. */
-    property Texture probe: Texture {
-        id: hdrProbe
-        source: controller.primarySource
+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
     }
+    Texture {
+        id: texB
+        source: ""
+=======
+    /** Expose the probe for consumers. */
+    property Texture probe: hdrProbe
+
+    Texture {
+        id: hdrProbe
+        source: controller.primarySource
+>>>>>>> sync/remote-main
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
+        // Отправляем в Python для записи в файл
+        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
+            window.logIblEvent(logEntry)
+        }
+
+        // Также выводим в консоль для отладки
+        if (level === "ERROR" || level === "WARN") {
+            console.warn(logEntry)
+        } else {
+            console.log(logEntry)
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/copilot/add-ibl-control-features:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/copilot/add-ibl-control-features:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/copilot/add-ibl-control-features:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `0dae95c3ae77`

```diff

--- origin/copilot/add-ibl-control-features:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,12 +23,22 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -44,6 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -80,6 +94,17 @@

         # Logging
         self.logger = logging.getLogger(self.__class__.__name__)

+        # ✅ НОВОЕ: Инициализация IBL Signal Logger
+        self.ibl_logger = get_ibl_logger()
+        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
+
+<<<<<<< HEAD
+=======
+        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
+        self.event_logger = get_event_logger()
+        self.logger.info("EventLogger initialized in MainWindow")
+
+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -165,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
     # UI Construction - НОВАЯ СТРУКТРАА!
+=======
+    # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -222,6 +251,12 @@

             # CRITICAL: Set up QML import paths BEFORE loading any QML
             engine = self._qquick_widget.engine()

+            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Устанавливаем контекст ДО загрузки QML!
+            context = engine.rootContext()
+            context.setContextProperty("window", self)  # Экспонируем MainWindow в QML
+            log_ibl_event("INFO", "MainWindow", "IBL Logger registered in QML context (BEFORE QML load)")
+            print("    ✅ IBL Logger context registered BEFORE QML load")
+
             # Add Qt's QML import path
             from PySide6.QtCore import QLibraryInfo
             qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
@@ -249,6 +284,15 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `29a4cae63dc6`

```diff

--- origin/copilot/add-ibl-control-features:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,30 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # Отправляем сигналы без проверки подписчиков (она не работает в PySide6)
-            print(f"  📡 Отправка geometry_changed...")
             self.geometry_changed.emit(initial_geometry)
-            print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-
-            print(f"  📡 Отправка geometry_updated...")
             self.geometry_updated.emit(self.parameters.copy())
-            print(f"  📡 geometry_updated отправлен")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -323,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
-        # Frame dimensions - ТОЛЬКО valueEdited
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
+        # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main
+
+        self.logger.debug("Connecting signals...")
+
+        # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
-
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
+        # Мгновенные обновления канвы
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `001b2133a413`

```diff

--- origin/copilot/add-ibl-control-features:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -5,15 +5,28 @@

 import json
 import logging
 from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
     QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -26,6 +39,12 @@

     QWidget,
 )

+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType
+

 class ColorButton(QPushButton):
     """Small color preview button that streams changes from QColorDialog."""
@@ -37,6 +56,7 @@

         self.setFixedSize(42, 28)
         self._color = QColor(initial_color)
         self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
         self._update_swatch()
         self.clicked.connect(self._open_dialog)

@@ -44,6 +64,7 @@

         return self._color

     def set_color(self, color_str: str) -> None:
+        """Программное изменение цвета (без логирования)"""
         self._color = QColor(color_str)
         self._update_swatch()

@@ -59,6 +80,9 @@


     @Slot()
     def _open_dialog(self) -> None:
+        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
+        self._user_triggered = True
+
         if self._dialog:
             return

@@ -77,13 +101,17 @@

             return
         self._color = color
         self._update_swatch()
-        self.color_changed.emit(color.name())
+
+        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
+        if self._user_triggered:
+            self.color_changed.emit(color.name())

... (обрезано)

```


## origin/copilot/clone-repo-to-local-machine


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `b39659f93d9a`

```diff

--- origin/copilot/clone-repo-to-local-machine:app.py

+++ local:app.py

@@ -1,67 +1,55 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# ОПТИМИЗАЦИЯ: Кэширование системной информации
-# =============================================================================
-
-_system_info_cache = {}
-
-def get_cached_system_info():
-    """Получить кэшированную системную информацию"""
-    global _system_info_cache
-
-    if not _system_info_cache:
-        _system_info_cache = {
-            'platform': sys.platform,
-            'python_version': sys.version_info,
-            'encoding': sys.getdefaultencoding(),
-            'terminal_encoding': locale.getpreferredencoding(),
-            'qtquick3d_setup': qtquick3d_setup_ok
-        }
-
-    return _system_info_cache
-
-# =============================================================================
-# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports) - ОПТИМИЗИРОВАННАЯ
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+

 def setup_qtquick3d_environment():
-    """Set up QtQuick3D environment variables before importing Qt - ОПТИМИЗИРОВАННАЯ"""
-
-    # Проверяем кэш переменных окружения
+    """Set up QtQuick3D environment variables before importing Qt"""
     required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
     if all(var in os.environ for var in required_vars):
-        print("[CACHE] QtQuick3D environment already configured")
         return True

     try:
-        # First, do a minimal import to get Qt paths
         import importlib.util
         spec = importlib.util.find_spec("PySide6.QtCore")
         if spec is None:
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/copilot/clone-repo-to-local-machine:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/copilot/clone-repo-to-local-machine:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/copilot/clone-repo-to-local-machine:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/copilot/clone-repo-to-local-machine:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `e8cb342cb248`

```diff

--- origin/copilot/clone-repo-to-local-machine:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1 +1,1769 @@

-import QtQuick 2.15; Item { anchors.fill: parent; Text { anchors.centerIn: parent; text: 'QML OK'; color: 'white' } }
+import QtQuick
+import QtQuick3D
+import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
+import "components"
+
+/*
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
+ */
+Item {
+    id: root
+    anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
+    // ===============================================================
+
+    // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
+    QtObject {
+        id: animationCache
+
+        // Базовые значения (вычисляются 1 раз за фрейм вместо 4х)
+        property real basePhase: animationTime * userFrequency * 2 * Math.PI
+        property real globalPhaseRad: userPhaseGlobal * Math.PI / 180
+
+        // Предварительно вычисленные фазы для каждого угла
+        property real flPhaseRad: globalPhaseRad + userPhaseFL * Math.PI / 180
+        property real frPhaseRad: globalPhaseRad + userPhaseFR * Math.PI / 180
+        property real rlPhaseRad: globalPhaseRad + userPhaseRL * Math.PI / 180
+        property real rrPhaseRad: globalPhaseRad + userPhaseRR * Math.PI / 180
+
+        // Кэшированные синусы (4 sin() вызова → 4 кэшированных значения)
+        property real flSin: Math.sin(basePhase + flPhaseRad)
+        property real frSin: Math.sin(basePhase + frPhaseRad)
+        property real rlSin: Math.sin(basePhase + rlPhaseRad)
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `12220691fa6b`

```diff

--- origin/copilot/clone-repo-to-local-machine:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,35 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

-    /** Expose the probe for consumers. */
-    property Texture probe: Texture {
-        id: hdrProbe
-        source: controller.primarySource
+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
     }
+    Texture {
+        id: texB
+        source: ""
+=======
+    /** Expose the probe for consumers. */
+    property Texture probe: hdrProbe
+
+    Texture {
+        id: hdrProbe
+        source: controller.primarySource
+>>>>>>> sync/remote-main
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
+        // Отправляем в Python для записи в файл
+        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
+            window.logIblEvent(logEntry)
+        }
+
+        // Также выводим в консоль для отладки
+        if (level === "ERROR" || level === "WARN") {
+            console.warn(logEntry)
+        } else {
+            console.log(logEntry)
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `fbcf361cb9ac`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -15,8 +15,6 @@

     QSettings,
     QUrl,
     QFileInfo,
-    QMetaObject,
-    Q_ARG,
     QByteArray,
 )
 from PySide6.QtGui import QAction, QKeySequence
@@ -25,12 +23,22 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -46,6 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -82,6 +94,17 @@

         # Logging
         self.logger = logging.getLogger(self.__class__.__name__)

+        # ✅ НОВОЕ: Инициализация IBL Signal Logger
+        self.ibl_logger = get_ibl_logger()
+        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
+
+<<<<<<< HEAD
+=======
+        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
+        self.event_logger = get_event_logger()
+        self.logger.info("EventLogger initialized in MainWindow")
+
+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -96,9 +119,11 @@


         # QML update system
         self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
+        self._qml_method_support: Dict[tuple[str, bool], bool] = {}
         self._qml_flush_timer = QTimer()
         self._qml_flush_timer.setSingleShot(True)
         self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
+        self._qml_pending_property_supported: Optional[bool] = None

         # State tracking
         self.current_snapshot: Optional[StateSnapshot] = None
@@ -126,6 +151,7 @@

         # Qt Quick 3D view reference
         self._qquick_widget: Optional[QQuickWidget] = None
         self._qml_root_object = None
+        self._qml_base_dir: Optional[Path] = None
... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `29a4cae63dc6`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,30 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # Отправляем сигналы без проверки подписчиков (она не работает в PySide6)
-            print(f"  📡 Отправка geometry_changed...")
             self.geometry_changed.emit(initial_geometry)
-            print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-
-            print(f"  📡 Отправка geometry_updated...")
             self.geometry_updated.emit(self.parameters.copy())
-            print(f"  📡 geometry_updated отправлен")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -323,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
-        # Frame dimensions - ТОЛЬКО valueEdited
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
+        # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main
+
+        self.logger.debug("Connecting signals...")
+
+        # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
-
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
+        # Мгновенные обновления канвы
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `68276b0087da`

```diff

--- origin/copilot/clone-repo-to-local-machine:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -5,15 +5,28 @@

 import json
 import logging
 from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
     QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -26,6 +39,12 @@

     QWidget,
 )

+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType
+

 class ColorButton(QPushButton):
     """Small color preview button that streams changes from QColorDialog."""
@@ -37,6 +56,7 @@

         self.setFixedSize(42, 28)
         self._color = QColor(initial_color)
         self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
         self._update_swatch()
         self.clicked.connect(self._open_dialog)

@@ -44,6 +64,7 @@

         return self._color

     def set_color(self, color_str: str) -> None:
+        """Программное изменение цвета (без логирования)"""
         self._color = QColor(color_str)
         self._update_swatch()

@@ -59,6 +80,9 @@


     @Slot()
     def _open_dialog(self) -> None:
+        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
+        self._user_triggered = True
+
         if self._dialog:
             return

@@ -77,13 +101,17 @@

             return
         self._color = color
         self._update_swatch()
-        self.color_changed.emit(color.name())
+
+        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
+        if self._user_triggered:
+            self.color_changed.emit(color.name())

... (обрезано)

```


## origin/feature/hdr-assets-migration


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `e570895aeb17`

```diff

--- origin/feature/hdr-assets-migration:app.py

+++ local:app.py

@@ -10,6 +10,7 @@

 import argparse
 import subprocess
 from pathlib import Path
+import json

 # =============================================================================
 # Накопление warnings/errors
@@ -113,15 +114,12 @@

 # =============================================================================


-def check_python_compatibility():
-    """Check Python version and warn about potential issues"""
+def check_python_compatibility() -> None:
+    """Проверка версии Python: проект таргетирует Python 3.13+"""
     version = sys.version_info
-
-    if version < (3, 8):
-        log_error("Python 3.8+ required. Please upgrade Python.")
+    if version < (3, 13):
+        log_error("Python 3.13+ required. Please upgrade Python.")
         sys.exit(1)
-    elif version >= (3, 12):
-        log_warning("Python 3.12+ detected. Some packages may have compatibility issues.")


 check_python_compatibility()
@@ -153,8 +151,8 @@


         try:
             major, minor = qt_version.split('.')[:2]
-            if int(major) == 6 and int(minor) < 8:
-                log_warning(f"Qt {qt_version} - ExtendedSceneEnvironment may be limited")
+            if int(major) == 6 and int(minor) < 10:
+                log_warning(f"Qt {qt_version} detected. Some 6.10+ features may be unavailable")
         except (ValueError, IndexError):
             log_warning(f"Could not parse Qt version: {qt_version}")

@@ -171,16 +169,18 @@

 # =============================================================================


-def setup_logging():
-    """Настройка логирования - ВСЕГДА активно"""
+def setup_logging(verbose_console: bool = False):
+    """Настройка логирования - ВСЕГДА активно
+
+    Args:
+        verbose_console: Включать ли вывод логов в консоль (аргумент --verbose)
+    """
     try:
         from src.common.logging_setup import init_logging, rotate_old_logs

         logs_dir = Path("logs")

-        # ✅ НОВОЕ: Ротация старых логов (оставляем только 10 последних)
-        # Политика проекта: всегда начинать с чистых логов
-        # Стираем старые логи на запуске (keep_count=0)
+        # Политика проекта: начинаем с чистых логов
         rotate_old_logs(logs_dir, keep_count=0)

         # Инициализируем логирование с ротацией
@@ -189,7 +189,7 @@

             logs_dir,
             max_bytes=10 * 1024 * 1024,  # 10 MB на файл
             backup_count=5,               # Держим 5 backup файлов
-            console_output=False          # НЕ выводим в консоль
+            console_output=bool(verbose_console)  # Включаем по запросу
         )

         logger.info("=" * 60)
@@ -201,6 +201,9 @@

         logger.info(f"Qt: {qVersion()}")
         logger.info(f"Platform: {sys.platform}")
         logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
+
+        if verbose_console:
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `5f3bddc89ca3`

```diff

--- origin/feature/hdr-assets-migration:requirements.txt

+++ local:requirements.txt

@@ -1,5 +1,5 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.9-3.13 (рекомендуется 3.11-3.13)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
@@ -16,23 +16,22 @@

 pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=7.0.0            # Тестирование
-PyYAML>=6.0              # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
 # trimesh>=3.15.0         # 3D mesh обработка (опционально)
 # pyqtgraph>=0.12.0       # Быстрые графики (опционально)
-
-# Производительность
 # numba>=0.56.0           # JIT компиляция (опционально)
 # cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
 # - Windows 10/11 (Python 3.11-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.10-3.12)
-# - macOS 12+ (Python 3.11-3.12)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
 # 1. Требуется PySide6 6.10+ из-за использования Fog и dithering

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/feature/hdr-assets-migration:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/feature/hdr-assets-migration:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/feature/hdr-assets-migration:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `35e346183374`

```diff

--- origin/feature/hdr-assets-migration:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,6 +1,8 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
@@ -17,6 +19,8 @@

 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false

     // ===============================================================
     // 🚀 SIGNALS - ACK для Python после применения обновлений
@@ -202,12 +206,6 @@

     property real iblRotationDeg: 0
     property real iblIntensity: 1.3

-    // ❌ Больше НЕ связываем фон со включением IBL
-    // onIblEnabledChanged: {
-    //     iblLightingEnabled = iblEnabled
-    //     iblBackgroundEnabled = iblEnabled
-    // }
-
     property bool fogEnabled: true
     property color fogColor: "#b0c4d8"
     property real fogDensity: 0.12
@@ -557,10 +555,6 @@

     // ✅ COMPLETE BATCH UPDATE SYSTEM (All functions implemented)
     // ===============================================================

-    // ===============================================================
-    // ✅ ENHANCED BATCH UPDATE SYSTEM (Conflict Resolution)
-    // ===============================================================
-
     function applyBatchedUpdates(updates) {
         console.log("🚀 Applying batched updates with conflict resolution:", Object.keys(updates))

@@ -699,13 +693,13 @@

             if (params.point_light.brightness !== undefined) pointLightBrightness = params.point_light.brightness
             if (params.point_light.color !== undefined) pointLightColor = params.point_light.color
             if (params.point_light.position_x !== undefined) pointLightX = Number(params.point_light.position_x)
-             if (params.point_light.position_y !== undefined) pointLightY = params.point_light.position_y
-             if (params.point_light.range !== undefined) pointLightRange = Math.max(1, params.point_light.range)
-             if (params.point_light.casts_shadow !== undefined) pointLightCastsShadow = !!params.point_light.casts_shadow
-             if (params.point_light.bind_to_camera !== undefined) pointLightBindToCamera = !!params.point_light.bind_to_camera
-         }
-         console.log("  ✅ Lighting updated successfully")
-     }
+            if (params.point_light.position_y !== undefined) pointLightY = params.point_light.position_y
+            if (params.point_light.range !== undefined) pointLightRange = Math.max(1, params.point_light.range)
+            if (params.point_light.casts_shadow !== undefined) pointLightCastsShadow = !!params.point_light.casts_shadow
+            if (params.point_light.bind_to_camera !== undefined) pointLightBindToCamera = !!params.point_light.bind_to_camera
+        }
+        console.log("  ✅ Lighting updated successfully")
+    }

     function applyMaterialUpdates(params) {
         console.log("🎨 main.qml: applyMaterialUpdates() called")
@@ -787,10 +781,7 @@

                     console.log("  🌟 IBL fallback:", iblFallbackSource)
                 }
             }
-            if (params.ibl.offset_x !== undefined) environmentOffsetX = Number(params.ibl.offset_x)
-            if (params.ibl.offset_y !== undefined) environmentOffsetY = Number(params.ibl.offset_y)
-            if (params.ibl.bind_to_camera !== undefined) environmentBindToCamera = !!params.ibl.bind_to_camera
-         }
+        }

         if (params.fog) {
             if (params.fog.enabled !== undefined) fogEnabled = params.fog.enabled
@@ -920,13 +911,8 @@

             // ✅ ПРОБА НУЖНА ДЛЯ ФОНА И/ИЛИ ОСВЕЩЕНИЯ
             lightProbe: (root.iblReady && (root.iblLightingEnabled || (root.backgroundMode === "skybox" && root.iblBackgroundEnabled))) ? iblLoader.probe : null
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `d378637cb82c`

```diff

--- origin/feature/hdr-assets-migration:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -14,17 +14,47 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
     property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
@@ -49,6 +79,12 @@

     }

     // Monitor texture status using Timer polling (Texture has no statusChanged signal!)
+<<<<<<< HEAD
+    property int _lastStatusA: -1
+    property int _lastStatusB: -1
+
+    // Polling-based status check for both textures
+=======
     property int _lastStatus: -1  // Начинаем с -1 вместо Texture.Null

     onProbeChanged: {
@@ -59,11 +95,53 @@

     }

     // Polling-based status check (since Texture doesn't emit statusChanged signal)
+>>>>>>> sync/remote-main
     Timer {
         interval: 100  // Check every 100ms
         running: true
         repeat: true
         onTriggered: {
+<<<<<<< HEAD
+            controller._checkStatusFor(texA, 0)
+            controller._checkStatusFor(texB, 1)
+        }
+    }
+    function _statusToString(s) {
+        return s === Texture.Null ? "Null" :
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `2117cc0e6ee9`

```diff

--- origin/feature/hdr-assets-migration:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -466,18 +466,29 @@


     Args:
         log_dir: Директория с логами
+<<<<<<< HEAD
+        keep_count: Сколько последних файлов оставить
+=======
         keep_count: Сколько последних файлов оставить (0 = удалить все)
+>>>>>>> sync/remote-main
     """
     if not log_dir.exists():
         return

     # Находим все лог-файлы с timestamp
     log_files = sorted(
+<<<<<<< HEAD
+        log_dir.glob("PneumoStabSim_*.log"),
+=======
         list(log_dir.glob("PneumoStabSim_*.log")),
+>>>>>>> sync/remote-main
         key=lambda p: p.stat().st_mtime,
         reverse=True
     )

+<<<<<<< HEAD
+    # Удаляем старые
+=======
     # Если keep_count == 0 — удаляем все timestamp-логи
     if keep_count <= 0:
         for lf in log_files:
@@ -497,6 +508,7 @@

         return

     # Обычный режим: оставляем N последних
+>>>>>>> sync/remote-main
     for old_log in log_files[keep_count:]:
         try:
             old_log.unlink()

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `3c3fbc11a8a9`

```diff

--- origin/feature/hdr-assets-migration:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -342,6 +342,15 @@

         """Найти пары Python→QML событий для анализа синхронизации"""
         pairs = []

+<<<<<<< HEAD
+        # Группируем по timestamp
+        for i, event in enumerate(self.events):
+            if event["event_type"] == "SIGNAL_EMIT":
+                # Ищем соответствующий SIGNAL_RECEIVED в QML
+                signal_name = event["action"].replace("emit_", "")
+
+                # Ищем в следующих 1000ms
+=======
         # Сопоставление signal → QML функции (apply*Updates)
         signal_to_qml = {
             "lighting_changed": "applyLightingUpdates",
@@ -360,6 +369,7 @@

                 signal_name = event["action"].replace("emit_", "")
                 expected_qml_func = signal_to_qml.get(signal_name)

+>>>>>>> sync/remote-main
                 emit_time = datetime.fromisoformat(event["timestamp"])

                 for j in range(i+1, len(self.events)):
@@ -369,6 +379,11 @@

                     if (recv_time - emit_time).total_seconds() > 1.0:
                         break  # Слишком поздно

+<<<<<<< HEAD
+                    if (next_event["event_type"] == "SIGNAL_RECEIVED" and
+                        signal_name in next_event["action"]):
+
+=======
                     # ✅ Вариант 1: QML подписался на сигнал (onXxxChanged)
                     if (
                         next_event["event_type"] == "SIGNAL_RECEIVED"
@@ -388,6 +403,7 @@

                         and expected_qml_func is not None
                         and next_event["action"] == expected_qml_func
                     ):
+>>>>>>> sync/remote-main
                         pairs.append({
                             "python_event": event,
                             "qml_event": next_event,

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `3fbd68bcfb6c`

```diff

--- origin/feature/hdr-assets-migration:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -51,11 +51,6 @@

     def add_recommendation(self, message: str):
         """Добавляет рекомендацию"""
         self.recommendations.append(message)
-    # --- NEW helpers for structured errors ---
-    def add_collapsed_errors(self, errors: List[str]):
-        """Добавляет набор конкретных ошибок (уникализируя по сообщению)."""
-        for e in errors:
-            self.add_error(e)


 class UnifiedLogAnalyzer:
@@ -106,25 +101,9 @@

             result.add_metric('warnings', len(warnings))

             if errors:
-                # Полный разбор ошибок с группировкой одинаковых сообщений без таймстемпов
-                norm_errors: Dict[str, List[str]] = defaultdict(list)
-                ts_re = re.compile(r'^\s*\d{4}-\d{2}-\d{2}[^ ]*\s+')
-                for line in errors:
-                    base = ts_re.sub('', line).strip()
-                    # Урезаем путь внутри traceback строк до последнего сегмента для агрегирования
-                    base_short = re.sub(r'File "([^"]+)"', lambda m: f"File '{Path(m.group(1)).name}'", base)
-                    norm_errors[base_short].append(line.strip())
-
-                # Добавляем агрегированную строку
-                result.add_error(f"Обнаружено {len(errors)} ошибок в run.log (уникальных: {len(norm_errors)})")
-                # Сортируем по количеству вхождений
-                for msg, lines_same in sorted(norm_errors.items(), key=lambda x: len(x[1]), reverse=True):
-                    count = len(lines_same)
-                    prefix = 'CRITICAL' if 'CRITICAL' in msg or 'FATAL' in msg else 'ERROR'
-                    result.add_error(f"[{prefix}] {count}× {msg}")
-                # Добавляем короткий совет если много разных типов
-                if len(norm_errors) > 5:
-                    result.add_recommendation("Слишком много разных типов ошибок — начните с первой по количеству повторов.")
+                result.add_error(f"Обнаружено {len(errors)} ошибок в run.log")
+                for error in errors[:3]:  # Первые 3
+                    result.add_error(f"  → {error.strip()}")

             if warnings:
                 result.add_warning(f"Обнаружено {len(warnings)} предупреждений")
@@ -218,17 +197,6 @@

             if categories:
                 result.add_info(f"Категории изменений: {dict(categories)}")

-            # Конкретные ошибки QML sync (error поля)
-            error_events = [e for e in events if e.get('error')]
-            if error_events:
-                grouped = defaultdict(list)
-                for ev in error_events:
-                    key = ev.get('error')
-                    grouped[key].append(ev)
-                for msg, group_list in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
-                    result.add_error(f"GRAPHICS_SYNC {len(group_list)}× {msg}")
-                result.add_recommendation("Проверьте соответствие payload ↔ apply*Updates обработчиков")
-
         except Exception as e:
             result.add_error(f"Ошибка анализа graphics логов: {e}")

@@ -265,15 +233,10 @@

             result.add_metric('ibl_success', len(success))

             if errors:
-                # Группируем одинаковые сообщения
-                norm = defaultdict(list)
-                for line in errors:
-                    msg = re.sub(r'\s+', ' ', line.strip())
-                    norm[msg].append(line)
-                result.add_error(f"IBL ошибки: {len(errors)} (уникальных: {len(norm)})")
-                for msg, lines_same in sorted(norm.items(), key=lambda x: len(x[1]), reverse=True):
-                    result.add_error(f"[IBL] {len(lines_same)}× {msg}")
-                result.add_recommendation("Проверьте пути к HDR / права доступа / наличие файлов")
+                result.add_error(f"IBL ошибки: {len(errors)}")
+                for error in errors[:2]:
+                    result.add_error(f"  → {error.strip()}")
+                result.add_recommendation("Проверьте пути к HDR файлам")

             if success:
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `8c959481995d`

```diff

--- origin/feature/hdr-assets-migration:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,7 +23,10 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
 from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

@@ -31,8 +34,11 @@

 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
 from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
 # ✅ НОВОЕ: EventLogger для логирования QML вызовов
 from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -48,7 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
-
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -89,10 +98,13 @@

         self.ibl_logger = get_ibl_logger()
         log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")

+<<<<<<< HEAD
+=======
         # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
         self.event_logger = get_event_logger()
         self.logger.info("EventLogger initialized in MainWindow")

+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -178,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
+    # UI Construction - НОВАЯ СТРУКТРАА!
+=======
     # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -268,12 +284,15 @@


             qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
             print(f"    📂 Полный путь: {qml_url.toString()}")
+<<<<<<< HEAD
+=======

             # ✅ Устанавливаем базовую директорию QML для разрешения относительных путей
             try:
                 self._qml_base_dir = qml_path.parent.resolve()
             except Exception:
                 self._qml_base_dir = None
+>>>>>>> sync/remote-main

             self._qquick_widget.setSource(qml_url)

@@ -297,6 +316,16 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `20c2769950c7`

```diff

--- origin/feature/hdr-assets-migration:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -316,25 +316,50 @@


     def _connect_signals(self):
         """Connect widget signals"""
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
         # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main

         self.logger.debug("Connecting signals...")

         # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
         # Мгновенные обновления канвы
         self.wheelbase_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('wheelbase', v))

+>>>>>>> sync/remote-main
         self.track_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('track', v))
         self.track_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('track', v))

         # Suspension geometry
+        self.frame_to_pivot_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('frame_to_pivot', v))
         self.frame_to_pivot_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('frame_to_pivot', v))
+<<<<<<< HEAD
+
+        self.lever_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+        self.lever_length_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+
+        self.rod_position_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('rod_position', v))
+=======
         self.frame_to_pivot_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('frame_to_pivot', v))

@@ -343,14 +368,51 @@

         self.lever_length_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('lever_length', v))

+>>>>>>> sync/remote-main
         self.rod_position_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('rod_position', v))
         self.rod_position_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('rod_position', v))

         # Cylinder dimensions
+        self.cylinder_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cylinder_length', v))
         self.cylinder_length_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('cylinder_length', v))
+<<<<<<< HEAD
+
+        # МШ-1: Параметры цилиндра
+        self.cyl_diam_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+        self.cyl_diam_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+
+        self.stroke_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
+        self.stroke_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `11142a074257`

```diff

--- origin/feature/hdr-assets-migration:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -6,15 +6,27 @@

 import logging
 from typing import Any, Dict
 from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
 from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -140,8 +152,12 @@

         row.setSpacing(6)
         layout.addLayout(row)

+<<<<<<< HEAD
+        self._slider = QSlider(Qt.Horizontal, self)
+=======
         # ✅ ИСПРАВЛЕНО: используем QtWidgets.QSlider, чтобы избежать NameError
         self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
+>>>>>>> sync/remote-main
         steps = max(1, int(round((self._max - self._min) / self._step)))
         self._slider.setRange(0, steps)

@@ -292,6 +308,16 @@

     def _build_defaults(self) -> Dict[str, Any]:
         return {
             "lighting": {
+<<<<<<< HEAD
+                # ✅ Добавлены флаги теней для каждого источника света
+                "key": {"brightness": 1.2, "color": "#ffffff", "angle_x": -35.0, "angle_y": -40.0, "casts_shadow": True},
+                "fill": {"brightness": 0.7, "color": "#dfe7ff", "casts_shadow": False},
+                "rim": {"brightness": 1.0, "color": "#ffe2b0", "casts_shadow": False},
+                "point": {"brightness": 1000.0, "color": "#ffffff", "height": 2200.0, "range": 3200.0, "casts_shadow": False},
+            },
+            "environment": {
+                "background_mode": "skybox",
+=======
                 # Добавлены: cast_shadow, bind_to_camera, position_x/position_y для каждого источника
                 "key": {
                     "brightness": 1.2,
@@ -331,11 +357,16 @@

             },
             "environment": {
                 "background_mode": "skybox",  # 'color' | 'skybox'
+>>>>>>> sync/remote-main
                 "background_color": "#1f242c",
                 "ibl_enabled": True,
                 "ibl_intensity": 1.3,
                 "ibl_source": "../hdr/studio.hdr",
+<<<<<<< HEAD
+                "ibl_fallback": "assets/studio_small_09_2k.hdr",
+=======
                 "ibl_fallback": "../hdr/studio_small_09_2k.hdr",  # ✅ ИСПРАВЛЕНО: корректный относительный путь
+>>>>>>> sync/remote-main
                 "skybox_blur": 0.08,
                 "fog_enabled": True,
                 "fog_color": "#b0c4d8",
@@ -388,8 +419,13 @@

                 "dof_blur": 4.0,
                 "motion_blur": False,
... (обрезано)

```


## origin/feature/ibl-rotation-and-cylinder-geometry


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `3dbee948dd0a`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:app.py

+++ local:app.py

@@ -1,75 +1,55 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# ОПТИМИЗАЦИЯ: Кэширование системной информации
-# =============================================================================
-
-_system_info_cache = {}
-
-def get_cached_system_info():
-    """Получить кэшированную системнюю информацию"""
-    global _system_info_cache
-
-    if not _system_info_cache:
-        # Импортируем qVersion для получения версии Qt
-        try:
-            from PySide6.QtCore import qVersion
-            qt_version = qVersion()
-        except:
-            qt_version = "unknown"
-
-        _system_info_cache = {
-            'platform': sys.platform,
-            'python_version': sys.version_info,
-            'encoding': sys.getdefaultencoding(),
-            'terminal_encoding': locale.getpreferredencoding(),
-            'qtquick3d_setup': qtquick3d_setup_ok,
-            'qt_version': qt_version
-        }
-
-    return _system_info_cache
-
-# =============================================================================
-# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports) - ОПТИМИЗИРОВАННАЯ
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+

 def setup_qtquick3d_environment():
-    """Set up QtQuick3D environment variables before importing Qt - ОПТИМИЗИРОВАННАЯ"""
-
-    # Проверяем кэш переменных окружения
+    """Set up QtQuick3D environment variables before importing Qt"""
     required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
     if all(var in os.environ for var in required_vars):
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `feca631ea77c`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,24 +1,41 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
- * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.8)
- * 🚀 ИСПРАВЛЕНО: Туман через объект Fog (Qt 6.10+)
- * ✅ Все свойства соответствуют официальной документации Qt Quick 3D
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)

     // ===============================================================
     // 🚀 QT VERSION DETECTION (для условной активации возможностей)
     // ===============================================================

-    readonly property var qtVersionParts: Qt.version.split('.')
-    readonly property int qtMajor: parseInt(qtVersionParts[0])
-    readonly property int qtMinor: parseInt(qtVersionParts[1])
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
     readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10

     // ✅ Условная поддержка dithering (доступно с Qt 6.10)
@@ -26,7 +43,17 @@

     readonly property bool canUseDithering: supportsQtQuick3D610Features

     // ===============================================================
-    // 🚀 PERFORMANCE OPTIMIZATION LAYER (preserved)
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

     // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
@@ -146,21 +173,39 @@

     property color keyLightColor: "#ffffff"
     property real keyLightAngleX: -35
     property real keyLightAngleY: -40
+    property bool keyLightCastsShadow: true
+    property bool keyLightBindToCamera: false
+    property real keyLightPosX: 0.0
+    property real keyLightPosY: 0.0
     property real fillLightBrightness: 0.7
     property color fillLightColor: "#dfe7ff"
+    property bool fillLightCastsShadow: false
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `12220691fa6b`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,35 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

-    /** Expose the probe for consumers. */
-    property Texture probe: Texture {
-        id: hdrProbe
-        source: controller.primarySource
+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
     }
+    Texture {
+        id: texB
+        source: ""
+=======
+    /** Expose the probe for consumers. */
+    property Texture probe: hdrProbe
+
+    Texture {
+        id: hdrProbe
+        source: controller.primarySource
+>>>>>>> sync/remote-main
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
+        // Отправляем в Python для записи в файл
+        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
+            window.logIblEvent(logEntry)
+        }
+
+        // Также выводим в консоль для отладки
+        if (level === "ERROR" || level === "WARN") {
+            console.warn(logEntry)
+        } else {
+            console.log(logEntry)
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `0dae95c3ae77`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,12 +23,22 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -44,6 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -80,6 +94,17 @@

         # Logging
         self.logger = logging.getLogger(self.__class__.__name__)

+        # ✅ НОВОЕ: Инициализация IBL Signal Logger
+        self.ibl_logger = get_ibl_logger()
+        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
+
+<<<<<<< HEAD
+=======
+        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
+        self.event_logger = get_event_logger()
+        self.logger.info("EventLogger initialized in MainWindow")
+
+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -165,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
     # UI Construction - НОВАЯ СТРУКТРАА!
+=======
+    # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -222,6 +251,12 @@

             # CRITICAL: Set up QML import paths BEFORE loading any QML
             engine = self._qquick_widget.engine()

+            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Устанавливаем контекст ДО загрузки QML!
+            context = engine.rootContext()
+            context.setContextProperty("window", self)  # Экспонируем MainWindow в QML
+            log_ibl_event("INFO", "MainWindow", "IBL Logger registered in QML context (BEFORE QML load)")
+            print("    ✅ IBL Logger context registered BEFORE QML load")
+
             # Add Qt's QML import path
             from PySide6.QtCore import QLibraryInfo
             qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
@@ -249,6 +284,15 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `29a4cae63dc6`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,30 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # Отправляем сигналы без проверки подписчиков (она не работает в PySide6)
-            print(f"  📡 Отправка geometry_changed...")
             self.geometry_changed.emit(initial_geometry)
-            print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-
-            print(f"  📡 Отправка geometry_updated...")
             self.geometry_updated.emit(self.parameters.copy())
-            print(f"  📡 geometry_updated отправлен")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -323,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
-        # Frame dimensions - ТОЛЬКО valueEdited
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
+        # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main
+
+        self.logger.debug("Connecting signals...")
+
+        # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
-
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
+        # Мгновенные обновления канвы
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `68276b0087da`

```diff

--- origin/feature/ibl-rotation-and-cylinder-geometry:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -5,15 +5,28 @@

 import json
 import logging
 from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
     QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -26,6 +39,12 @@

     QWidget,
 )

+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType
+

 class ColorButton(QPushButton):
     """Small color preview button that streams changes from QColorDialog."""
@@ -37,6 +56,7 @@

         self.setFixedSize(42, 28)
         self._color = QColor(initial_color)
         self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
         self._update_swatch()
         self.clicked.connect(self._open_dialog)

@@ -44,6 +64,7 @@

         return self._color

     def set_color(self, color_str: str) -> None:
+        """Программное изменение цвета (без логирования)"""
         self._color = QColor(color_str)
         self._update_swatch()

@@ -59,6 +80,9 @@


     @Slot()
     def _open_dialog(self) -> None:
+        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
+        self._user_triggered = True
+
         if self._dialog:
             return

@@ -77,13 +101,17 @@

             return
         self._color = color
         self._update_swatch()
-        self.color_changed.emit(color.name())
+
+        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
+        if self._user_triggered:
+            self.color_changed.emit(color.name())

... (обрезано)

```


## origin/latest-main


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `d91092a9920a`

```diff

--- origin/latest-main:app.py

+++ local:app.py

@@ -1,154 +1,233 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# CRITICAL: Terminal and Encoding Configuration
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+
+
+def setup_qtquick3d_environment():
+    """Set up QtQuick3D environment variables before importing Qt"""
+    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
+    if all(var in os.environ for var in required_vars):
+        return True
+
+    try:
+        import importlib.util
+        spec = importlib.util.find_spec("PySide6.QtCore")
+        if spec is None:
+            log_error("PySide6 not found!")
+            return False
+
+        from PySide6.QtCore import QLibraryInfo
+
+        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
+        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
+
+        qtquick3d_env = {
+            "QML2_IMPORT_PATH": str(qml_path),
+            "QML_IMPORT_PATH": str(qml_path),
+            "QT_PLUGIN_PATH": str(plugins_path),
+            "QT_QML_IMPORT_PATH": str(qml_path),
+        }
+
+        for var, value in qtquick3d_env.items():
+            os.environ[var] = value
+
+        return True
+
+    except Exception as e:
+        log_error(f"QtQuick3D setup failed: {e}")
+        return False
+
+
+qtquick3d_setup_ok = setup_qtquick3d_environment()
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/latest-main:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/latest-main:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `4646db540136`

```diff

--- origin/latest-main:.env

+++ local:.env

@@ -1,23 +1,17 @@

-# PneumoStabSim Professional Environment (Автоматически обновлено)
-PYTHONPATH=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/src;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/tests;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/scripts
+# PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
 PYTHONIOENCODING=utf-8
-PYTHONDONTWRITEBYTECODE=1
-
-# Qt Configuration
-QSG_RHI_BACKEND=d3d11
-QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
-QSG_INFO=1
-
-# Project Paths
-PROJECT_ROOT=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional
-SOURCE_DIR=src
-TEST_DIR=tests
-SCRIPT_DIR=scripts
-
-# Development Mode
-DEVELOPMENT_MODE=true
-DEBUG_ENABLED=true
-
-# Russian Localization
-LANG=ru_RU.UTF-8
-COPILOT_LANGUAGE=ru
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/latest-main:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `30282a0fe558`

```diff

--- origin/latest-main:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,23 +1,62 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
+import "components"

 /*
- * PneumoStabSim - Unified Optimized 3D View v3.0
- * ✅ Объединяет лучшие части main.qml и main_optimized.qml
- * ✅ Убрано дублирование примитивов
- * ✅ Оптимизированные вычисления с кэшированием
- * ✅ Один файл вместо двух
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему

     // ===============================================================
     // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

-    // Кэширование анимационных вычислений
+    // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
     QtObject {
         id: animationCache

@@ -38,7 +77,7 @@

         property real rrSin: Math.sin(basePhase + rrPhaseRad)
     }

-    // Геометрический калькулятор с кэшированием
+    // ✅ ОПТИМИЗАЦИЯ #2: Геометрический калькулятор
     QtObject {
         id: geometryCache

... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `819d0431be2c`

```diff

--- origin/latest-main:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,34 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
-    readonly property alias probe: hdrProbe
-
-    /** Simple ready flag to avoid binding against an invalid texture. */
-    readonly property bool ready: hdrProbe.status === Texture.Ready
+    property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
-
-        onStatusChanged: {
-            if (status === Texture.Error && !controller._fallbackTried) {
-                controller._fallbackTried = true
-                console.warn("⚠️ HDR probe not found at", source, "— falling back to", controller.fallbackSource)
-                source = controller.fallbackSource
-            } else if (status === Texture.Ready) {
-                console.log("✅ HDR probe ready:", source)
-            } else if (status === Texture.Error && controller._fallbackTried) {
-                console.warn("❌ Both HDR probes failed to load, IBL will be disabled")
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/latest-main:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/latest-main:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/latest-main:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `2a22b7b60828`

```diff

--- origin/latest-main:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -6,20 +6,39 @@

 from PySide6.QtWidgets import (
     QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
     QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter,
-    QTabWidget, QScrollArea  # NEW: For tabs and scrolling
+    QTabWidget, QScrollArea
 )
-from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
+from PySide6.QtCore import (
+    Qt,
+    QTimer,
+    Slot,
+    QSettings,
+    QUrl,
+    QFileInfo,
+    QByteArray,
+)
 from PySide6.QtGui import QAction, QKeySequence
 from PySide6.QtQuickWidgets import QQuickWidget
 import logging
 import json
 import numpy as np
+import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
-from typing import Optional, Dict
+from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -32,10 +51,32 @@

     SETTINGS_APP = "PneumoStabSimApp"
     SETTINGS_GEOMETRY = "MainWindow/Geometry"
     SETTINGS_STATE = "MainWindow/State"
-    SETTINGS_SPLITTER = "MainWindow/Splitter"  # NEW: Save splitter position
-    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"  # NEW: Save horizontal splitter position
-    SETTINGS_LAST_TAB = "MainWindow/LastTab"    # NEW: Save selected tab
+    SETTINGS_SPLITTER = "MainWindow/Splitter"
+    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
+    SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"
+
+    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
+        "geometry": ("applyGeometryUpdates", "updateGeometry"),
+        "animation": ("applyAnimationUpdates", "updateAnimation"),
+        "lighting": ("applyLightingUpdates", "updateLighting"),
+        "materials": ("applyMaterialUpdates", "updateMaterials"),
+        "environment": ("applyEnvironmentUpdates", "updateEnvironment"),
+        "quality": ("applyQualityUpdates", "updateQuality"),
+        "camera": ("applyCameraUpdates", "updateCamera"),
+        "effects": ("applyEffectsUpdates", "updateEffects"),
+    }
+
+    WHEEL_KEY_MAP = {
+        "LP": "fl",
+        "PP": "fr",
+        "LZ": "rl",
+        "PZ": "rr",
+    }

     def __init__(self, use_qml_3d: bool = True):
... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `44252a10df56`

```diff

--- origin/latest-main:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,50 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # ДИАГНОСТИКА: Проверяем подписчиков перед отправкой
-            try:
-                geom_changed_receivers = self.geometry_changed.receivers()
-                geom_updated_receivers = self.geometry_updated.receivers()
-
-                print(f"  📊 Подписчиков на geometry_changed: {geom_changed_receivers}")
-                print(f"  📊 Подписчиков на geometry_updated: {geom_updated_receivers}")
-
-                if geom_changed_receivers > 0:
-                    print(f"  ✅ Есть подписчики, отправляем geometry_changed...")
-                    self.geometry_changed.emit(initial_geometry)
-                    print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_changed, возможно главное окно еще не готово")
-
-                if geom_updated_receivers > 0:
-                    print(f"  ✅ Отправляем geometry_updated...")
-                    self.geometry_updated.emit(self.parameters.copy())
-                    print(f"  📡 geometry_updated отправлен")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_updated")
-
-            except Exception as e:
-                print(f"  ❌ Ошибка проверки подписчиков: {e}")
-                # Отправляем в любом случае
-                self.geometry_changed.emit(initial_geometry)
-                self.geometry_updated.emit(self.parameters.copy())
-                print(f"  📡 Сигналы отправлены без проверки подписчиков")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.geometry_changed.emit(initial_geometry)
+            self.geometry_updated.emit(self.parameters.copy())
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -343,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `58e7e5155772`

```diff

--- origin/latest-main:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -1,1626 +1,3053 @@

-"""
-GraphicsPanel - панель настроек графики и визуализации (РАСШИРЕННАЯ ВЕРСИЯ)
-Graphics Panel - comprehensive graphics and visualization settings panel
-РУССКИЙ ИНТЕРФЕЙС (Russian UI) + ПОЛНЫЙ НАБОР ПАРАМЕТРОВ
-"""
+"""Graphics panel providing exhaustive Qt Quick 3D controls."""
+from __future__ import annotations
+
+import copy
+import json
+import logging
+from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
-    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
-    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
-    QColorDialog, QFrame, QSizePolicy, QScrollArea, QTabWidget, QFileDialog, QMessageBox
+    QCheckBox,
+    QColorDialog,
+    QComboBox,
+    QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
+    QGridLayout,
+    QGroupBox,
+    QHBoxLayout,
+    QLabel,
+    QPushButton,
+    QScrollArea,
+    QSlider,
+    QTabWidget,
+    QVBoxLayout,
+    QWidget,
 )
-from PySide6.QtCore import Qt, Signal, Slot, QSettings
-from PySide6.QtGui import QColor, QPalette
-import logging
-from typing import Dict, Any
-import json
+
+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType


 class ColorButton(QPushButton):
-    """Кнопка выбора цвета с предварительным просмотром"""
+    """Small color preview button that streams changes from QColorDialog."""
+
+    color_changed = Signal(str)
+
+    def __init__(self, initial_color: str = "#ffffff", parent: QWidget | None = None) -> None:
+        super().__init__(parent)
+        self.setFixedSize(42, 28)
+        self._color = QColor(initial_color)
+        self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
+        self._update_swatch()
+        self.clicked.connect(self._open_dialog)
+
+    def color(self) -> QColor:
... (обрезано)

```


## origin/main


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `e570895aeb17`

```diff

--- origin/main:app.py

+++ local:app.py

@@ -10,6 +10,7 @@

 import argparse
 import subprocess
 from pathlib import Path
+import json

 # =============================================================================
 # Накопление warnings/errors
@@ -113,15 +114,12 @@

 # =============================================================================


-def check_python_compatibility():
-    """Check Python version and warn about potential issues"""
+def check_python_compatibility() -> None:
+    """Проверка версии Python: проект таргетирует Python 3.13+"""
     version = sys.version_info
-
-    if version < (3, 8):
-        log_error("Python 3.8+ required. Please upgrade Python.")
+    if version < (3, 13):
+        log_error("Python 3.13+ required. Please upgrade Python.")
         sys.exit(1)
-    elif version >= (3, 12):
-        log_warning("Python 3.12+ detected. Some packages may have compatibility issues.")


 check_python_compatibility()
@@ -153,8 +151,8 @@


         try:
             major, minor = qt_version.split('.')[:2]
-            if int(major) == 6 and int(minor) < 8:
-                log_warning(f"Qt {qt_version} - ExtendedSceneEnvironment may be limited")
+            if int(major) == 6 and int(minor) < 10:
+                log_warning(f"Qt {qt_version} detected. Some 6.10+ features may be unavailable")
         except (ValueError, IndexError):
             log_warning(f"Could not parse Qt version: {qt_version}")

@@ -171,16 +169,18 @@

 # =============================================================================


-def setup_logging():
-    """Настройка логирования - ВСЕГДА активно"""
+def setup_logging(verbose_console: bool = False):
+    """Настройка логирования - ВСЕГДА активно
+
+    Args:
+        verbose_console: Включать ли вывод логов в консоль (аргумент --verbose)
+    """
     try:
         from src.common.logging_setup import init_logging, rotate_old_logs

         logs_dir = Path("logs")

-        # ✅ НОВОЕ: Ротация старых логов (оставляем только 10 последних)
-        # Политика проекта: всегда начинать с чистых логов
-        # Стираем старые логи на запуске (keep_count=0)
+        # Политика проекта: начинаем с чистых логов
         rotate_old_logs(logs_dir, keep_count=0)

         # Инициализируем логирование с ротацией
@@ -189,7 +189,7 @@

             logs_dir,
             max_bytes=10 * 1024 * 1024,  # 10 MB на файл
             backup_count=5,               # Держим 5 backup файлов
-            console_output=False          # НЕ выводим в консоль
+            console_output=bool(verbose_console)  # Включаем по запросу
         )

         logger.info("=" * 60)
@@ -201,6 +201,9 @@

         logger.info(f"Qt: {qVersion()}")
         logger.info(f"Platform: {sys.platform}")
         logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
+
+        if verbose_console:
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `5f3bddc89ca3`

```diff

--- origin/main:requirements.txt

+++ local:requirements.txt

@@ -1,5 +1,5 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.9-3.13 (рекомендуется 3.11-3.13)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
@@ -16,23 +16,22 @@

 pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=7.0.0            # Тестирование
-PyYAML>=6.0              # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
 # trimesh>=3.15.0         # 3D mesh обработка (опционально)
 # pyqtgraph>=0.12.0       # Быстрые графики (опционально)
-
-# Производительность
 # numba>=0.56.0           # JIT компиляция (опционально)
 # cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
 # - Windows 10/11 (Python 3.11-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.10-3.12)
-# - macOS 12+ (Python 3.11-3.12)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
 # 1. Требуется PySide6 6.10+ из-за использования Fog и dithering

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/main:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `75e5b07d8fd9`

```diff

--- origin/main:.env

+++ local:.env

@@ -1 +1,17 @@

 # PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/main:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `b053bb28eaf9`

```diff

--- origin/main:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,6 +1,8 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
@@ -17,6 +19,8 @@

 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false

     // ===============================================================
     // 🚀 SIGNALS - ACK для Python после применения обновлений
@@ -202,12 +206,6 @@

     property real iblRotationDeg: 0
     property real iblIntensity: 1.3

-    // ❌ Больше НЕ связываем фон со включением IBL
-    // onIblEnabledChanged: {
-    //     iblLightingEnabled = iblEnabled
-    //     iblBackgroundEnabled = iblEnabled
-    // }
-
     property bool fogEnabled: true
     property color fogColor: "#b0c4d8"
     property real fogDensity: 0.12
@@ -557,10 +555,6 @@

     // ✅ COMPLETE BATCH UPDATE SYSTEM (All functions implemented)
     // ===============================================================

-    // ===============================================================
-    // ✅ ENHANCED BATCH UPDATE SYSTEM (Conflict Resolution)
-    // ===============================================================
-
     function applyBatchedUpdates(updates) {
         console.log("🚀 Applying batched updates with conflict resolution:", Object.keys(updates))

@@ -674,38 +668,38 @@

             if (params.key_light.color !== undefined) keyLightColor = params.key_light.color
             if (params.key_light.angle_x !== undefined) keyLightAngleX = params.key_light.angle_x
             if (params.key_light.angle_y !== undefined) keyLightAngleY = params.key_light.angle_y
-+            if (params.key_light.casts_shadow !== undefined) keyLightCastsShadow = !!params.key_light.casts_shadow
-+            if (params.key_light.bind_to_camera !== undefined) keyLightBindToCamera = !!params.key_light.bind_to_camera
-+            if (params.key_light.position_x !== undefined) keyLightPosX = Number(params.key_light.position_x)
-+            if (params.key_light.position_y !== undefined) keyLightPosY = Number(params.key_light.position_y)
+            if (params.key_light.casts_shadow !== undefined) keyLightCastsShadow = !!params.key_light.casts_shadow
+            if (params.key_light.bind_to_camera !== undefined) keyLightBindToCamera = !!params.key_light.bind_to_camera
+            if (params.key_light.position_x !== undefined) keyLightPosX = Number(params.key_light.position_x)
+            if (params.key_light.position_y !== undefined) keyLightPosY = Number(params.key_light.position_y)
         }
         if (params.fill_light) {
             if (params.fill_light.brightness !== undefined) fillLightBrightness = params.fill_light.brightness
             if (params.fill_light.color !== undefined) fillLightColor = params.fill_light.color
-+            if (params.fill_light.casts_shadow !== undefined) fillLightCastsShadow = !!params.fill_light.casts_shadow
-+            if (params.fill_light.bind_to_camera !== undefined) fillLightBindToCamera = !!params.fill_light.bind_to_camera
-+            if (params.fill_light.position_x !== undefined) fillLightPosX = Number(params.fill_light.position_x)
-+            if (params.fill_light.position_y !== undefined) fillLightPosY = Number(params.fill_light.position_y)
+            if (params.fill_light.casts_shadow !== undefined) fillLightCastsShadow = !!params.fill_light.casts_shadow
+            if (params.fill_light.bind_to_camera !== undefined) fillLightBindToCamera = !!params.fill_light.bind_to_camera
+            if (params.fill_light.position_x !== undefined) fillLightPosX = Number(params.fill_light.position_x)
+            if (params.fill_light.position_y !== undefined) fillLightPosY = Number(params.fill_light.position_y)
         }
         if (params.rim_light) {
             if (params.rim_light.brightness !== undefined) rimLightBrightness = params.rim_light.brightness
             if (params.rim_light.color !== undefined) rimLightColor = params.rim_light.color
-+            if (params.rim_light.casts_shadow !== undefined) rimLightCastsShadow = !!params.rim_light.casts_shadow
-+            if (params.rim_light.bind_to_camera !== undefined) rimLightBindToCamera = !!params.rim_light.bind_to_camera
-+            if (params.rim_light.position_x !== undefined) rimLightPosX = Number(params.rim_light.position_x)
-+            if (params.rim_light.position_y !== undefined) rimLightPosY = Number(params.rim_light.position_y)
+            if (params.rim_light.casts_shadow !== undefined) rimLightCastsShadow = !!params.rim_light.casts_shadow
+            if (params.rim_light.bind_to_camera !== undefined) rimLightBindToCamera = !!params.rim_light.bind_to_camera
+            if (params.rim_light.position_x !== undefined) rimLightPosX = Number(params.rim_light.position_x)
+            if (params.rim_light.position_y !== undefined) rimLightPosY = Number(params.rim_light.position_y)
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `d378637cb82c`

```diff

--- origin/main:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -14,17 +14,47 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
     property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
@@ -49,6 +79,12 @@

     }

     // Monitor texture status using Timer polling (Texture has no statusChanged signal!)
+<<<<<<< HEAD
+    property int _lastStatusA: -1
+    property int _lastStatusB: -1
+
+    // Polling-based status check for both textures
+=======
     property int _lastStatus: -1  // Начинаем с -1 вместо Texture.Null

     onProbeChanged: {
@@ -59,11 +95,53 @@

     }

     // Polling-based status check (since Texture doesn't emit statusChanged signal)
+>>>>>>> sync/remote-main
     Timer {
         interval: 100  // Check every 100ms
         running: true
         repeat: true
         onTriggered: {
+<<<<<<< HEAD
+            controller._checkStatusFor(texA, 0)
+            controller._checkStatusFor(texB, 1)
+        }
+    }
+    function _statusToString(s) {
+        return s === Texture.Null ? "Null" :
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `2117cc0e6ee9`

```diff

--- origin/main:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -466,18 +466,29 @@


     Args:
         log_dir: Директория с логами
+<<<<<<< HEAD
+        keep_count: Сколько последних файлов оставить
+=======
         keep_count: Сколько последних файлов оставить (0 = удалить все)
+>>>>>>> sync/remote-main
     """
     if not log_dir.exists():
         return

     # Находим все лог-файлы с timestamp
     log_files = sorted(
+<<<<<<< HEAD
+        log_dir.glob("PneumoStabSim_*.log"),
+=======
         list(log_dir.glob("PneumoStabSim_*.log")),
+>>>>>>> sync/remote-main
         key=lambda p: p.stat().st_mtime,
         reverse=True
     )

+<<<<<<< HEAD
+    # Удаляем старые
+=======
     # Если keep_count == 0 — удаляем все timestamp-логи
     if keep_count <= 0:
         for lf in log_files:
@@ -497,6 +508,7 @@

         return

     # Обычный режим: оставляем N последних
+>>>>>>> sync/remote-main
     for old_log in log_files[keep_count:]:
         try:
             old_log.unlink()

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `3c3fbc11a8a9`

```diff

--- origin/main:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -342,6 +342,15 @@

         """Найти пары Python→QML событий для анализа синхронизации"""
         pairs = []

+<<<<<<< HEAD
+        # Группируем по timestamp
+        for i, event in enumerate(self.events):
+            if event["event_type"] == "SIGNAL_EMIT":
+                # Ищем соответствующий SIGNAL_RECEIVED в QML
+                signal_name = event["action"].replace("emit_", "")
+
+                # Ищем в следующих 1000ms
+=======
         # Сопоставление signal → QML функции (apply*Updates)
         signal_to_qml = {
             "lighting_changed": "applyLightingUpdates",
@@ -360,6 +369,7 @@

                 signal_name = event["action"].replace("emit_", "")
                 expected_qml_func = signal_to_qml.get(signal_name)

+>>>>>>> sync/remote-main
                 emit_time = datetime.fromisoformat(event["timestamp"])

                 for j in range(i+1, len(self.events)):
@@ -369,6 +379,11 @@

                     if (recv_time - emit_time).total_seconds() > 1.0:
                         break  # Слишком поздно

+<<<<<<< HEAD
+                    if (next_event["event_type"] == "SIGNAL_RECEIVED" and
+                        signal_name in next_event["action"]):
+
+=======
                     # ✅ Вариант 1: QML подписался на сигнал (onXxxChanged)
                     if (
                         next_event["event_type"] == "SIGNAL_RECEIVED"
@@ -388,6 +403,7 @@

                         and expected_qml_func is not None
                         and next_event["action"] == expected_qml_func
                     ):
+>>>>>>> sync/remote-main
                         pairs.append({
                             "python_event": event,
                             "qml_event": next_event,

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `80efb0048d5a`

```diff

--- origin/main:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -23,7 +23,10 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
 from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

@@ -31,8 +34,11 @@

 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
 from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
 # ✅ НОВОЕ: EventLogger для логирования QML вызовов
 from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -48,7 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
-
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -89,10 +98,13 @@

         self.ibl_logger = get_ibl_logger()
         log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")

+<<<<<<< HEAD
+=======
         # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
         self.event_logger = get_event_logger()
         self.logger.info("EventLogger initialized in MainWindow")

+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -178,7 +190,11 @@

         print("✅ MainWindow.__init__() завершён")

     # ------------------------------------------------------------------
+<<<<<<< HEAD
+    # UI Construction - НОВАЯ СТРУКТРАА!
+=======
     # UI Construction - НОВАЯ СТРУКРАА!
+>>>>>>> sync/remote-main
     # ------------------------------------------------------------------
     def _setup_central(self):
         """Создать центральный вид с горизонтальным и вертикальным сплиттерами
@@ -268,12 +284,15 @@


             qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
             print(f"    📂 Полный путь: {qml_url.toString()}")
+<<<<<<< HEAD
+=======

             # ✅ Устанавливаем базовую директорию QML для разрешения относительных путей
             try:
                 self._qml_base_dir = qml_path.parent.resolve()
             except Exception:
                 self._qml_base_dir = None
+>>>>>>> sync/remote-main

             self._qquick_widget.setSource(qml_url)

@@ -297,6 +316,16 @@

... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `20c2769950c7`

```diff

--- origin/main:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -316,25 +316,50 @@


     def _connect_signals(self):
         """Connect widget signals"""
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
         # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main

         self.logger.debug("Connecting signals...")

         # Frame dimensions
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
         self.wheelbase_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
+<<<<<<< HEAD
+
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('track', v))
+=======
         # Мгновенные обновления канвы
         self.wheelbase_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('wheelbase', v))

+>>>>>>> sync/remote-main
         self.track_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('track', v))
         self.track_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('track', v))

         # Suspension geometry
+        self.frame_to_pivot_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('frame_to_pivot', v))
         self.frame_to_pivot_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('frame_to_pivot', v))
+<<<<<<< HEAD
+
+        self.lever_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+        self.lever_length_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('lever_length', v))
+
+        self.rod_position_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('rod_position', v))
+=======
         self.frame_to_pivot_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('frame_to_pivot', v))

@@ -343,14 +368,51 @@

         self.lever_length_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('lever_length', v))

+>>>>>>> sync/remote-main
         self.rod_position_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('rod_position', v))
         self.rod_position_slider.valueChanged.connect(
             lambda v: self._on_parameter_live_change('rod_position', v))

         # Cylinder dimensions
+        self.cylinder_length_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cylinder_length', v))
         self.cylinder_length_slider.valueEdited.connect(
             lambda v: self._on_parameter_changed('cylinder_length', v))
+<<<<<<< HEAD
+
+        # МШ-1: Параметры цилиндра
+        self.cyl_diam_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+        self.cyl_diam_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('cyl_diam_m', v))
+
+        self.stroke_m_slider.valueChanged.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
+        self.stroke_m_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('stroke_m', v))
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `d663270ffc02`

```diff

--- origin/main:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -6,15 +6,27 @@

 import logging
 from typing import Any, Dict
 from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
 from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -140,8 +152,12 @@

         row.setSpacing(6)
         layout.addLayout(row)

+<<<<<<< HEAD
+        self._slider = QSlider(Qt.Horizontal, self)
+=======
         # ✅ ИСПРАВЛЕНО: используем QtWidgets.QSlider, чтобы избежать NameError
         self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
+>>>>>>> sync/remote-main
         steps = max(1, int(round((self._max - self._min) / self._step)))
         self._slider.setRange(0, steps)

@@ -292,6 +308,16 @@

     def _build_defaults(self) -> Dict[str, Any]:
         return {
             "lighting": {
+<<<<<<< HEAD
+                # ✅ Добавлены флаги теней для каждого источника света
+                "key": {"brightness": 1.2, "color": "#ffffff", "angle_x": -35.0, "angle_y": -40.0, "casts_shadow": True},
+                "fill": {"brightness": 0.7, "color": "#dfe7ff", "casts_shadow": False},
+                "rim": {"brightness": 1.0, "color": "#ffe2b0", "casts_shadow": False},
+                "point": {"brightness": 1000.0, "color": "#ffffff", "height": 2200.0, "range": 3200.0, "casts_shadow": False},
+            },
+            "environment": {
+                "background_mode": "skybox",
+=======
                 # Добавлены: cast_shadow, bind_to_camera, position_x/position_y для каждого источника
                 "key": {
                     "brightness": 1.2,
@@ -331,11 +357,16 @@

             },
             "environment": {
                 "background_mode": "skybox",  # 'color' | 'skybox'
+>>>>>>> sync/remote-main
                 "background_color": "#1f242c",
                 "ibl_enabled": True,
                 "ibl_intensity": 1.3,
                 "ibl_source": "../hdr/studio.hdr",
+<<<<<<< HEAD
+                "ibl_fallback": "assets/studio_small_09_2k.hdr",
+=======
                 "ibl_fallback": "../hdr/studio_small_09_2k.hdr",  # ✅ ИСПРАВЛЕНО: корректный относительный путь
+>>>>>>> sync/remote-main
                 "skybox_blur": 0.08,
                 "fog_enabled": True,
                 "fog_color": "#b0c4d8",
@@ -388,8 +419,13 @@

                 "dof_blur": 4.0,
                 "motion_blur": False,
... (обрезано)

```


## origin/main-3b8da9a


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `dde5ca9c5fb1`

```diff

--- origin/main-3b8da9a:app.py

+++ local:app.py

@@ -1,154 +1,233 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# CRITICAL: Terminal and Encoding Configuration
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+
+
+def setup_qtquick3d_environment():
+    """Set up QtQuick3D environment variables before importing Qt"""
+    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
+    if all(var in os.environ for var in required_vars):
+        return True
+
+    try:
+        import importlib.util
+        spec = importlib.util.find_spec("PySide6.QtCore")
+        if spec is None:
+            log_error("PySide6 not found!")
+            return False
+
+        from PySide6.QtCore import QLibraryInfo
+
+        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
+        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
+
+        qtquick3d_env = {
+            "QML2_IMPORT_PATH": str(qml_path),
+            "QML_IMPORT_PATH": str(qml_path),
+            "QT_PLUGIN_PATH": str(plugins_path),
+            "QT_QML_IMPORT_PATH": str(qml_path),
+        }
+
+        for var, value in qtquick3d_env.items():
+            os.environ[var] = value
+
+        return True
+
+    except Exception as e:
+        log_error(f"QtQuick3D setup failed: {e}")
+        return False
+
+
+qtquick3d_setup_ok = setup_qtquick3d_environment()
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `bb145213d68b`

```diff

--- origin/main-3b8da9a:requirements.txt

+++ local:requirements.txt

@@ -1,6 +1,39 @@

-numpy==2.3.3
-scipy==1.16.2
-pyside6==6.9.3
-PyOpenGL==3.1.10
-PyOpenGL-accelerate==3.1.10
-matplotlib==3.10.6
+# PneumoStabSim Professional - Production Dependencies
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)
+
+# === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
+# Qt Framework - основа GUI и 3D рендеринга
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator
+
+# Numerical computing - основа физических расчетов
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver
+
+# === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
+# Visualization и анализ данных
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур
+
+# Testing и development
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг
+
+# === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)
+
+# === СОВМЕСТИМОСТЬ ===
+# Проверено на:
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)
+
+# Примечания:
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/main-3b8da9a:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `4887cd38dcfd`

```diff

--- origin/main-3b8da9a:.env

+++ local:.env

@@ -1,29 +1,17 @@

-# PneumoStabSim Professional - Environment Variables
-# These variables will be automatically loaded by the IDE and scripts
+# PneumoStabSim Professional Environment Configuration

-# Python path configuration
+# Python module paths
 PYTHONPATH=.;src

-# Qt configuration for optimal performance
+# Qt/QtQuick options
 QSG_RHI_BACKEND=d3d11
-QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
 QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1

-# Python optimization
-PYTHONOPTIMIZE=1
+# Python I/O and encoding
+PYTHONIOENCODING=utf-8
 PYTHONUNBUFFERED=1
-
-# Development settings
-PNEUMOSTAB_DEBUG=1
-PNEUMOSTAB_LOG_LEVEL=INFO
-PNEUMOSTAB_CACHE_DIR=cache
-PNEUMOSTAB_EXPORT_DIR=exports
-
-# Performance tuning
-QT_QUICK_CONTROLS_STYLE=Material
-QT_QUICK_CONTROLS_MATERIAL_THEME=Dark
-QML_DISABLE_DISK_CACHE=1
-
-# Graphics settings (Windows)
-QT_OPENGL=angle
-QT_ANGLE_PLATFORM=d3d11

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/main-3b8da9a:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `5523e5f4cae1`

```diff

--- origin/main-3b8da9a:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,37 +1,149 @@

 import QtQuick
 import QtQuick3D
-import QtQuick3D.Helpers  // ИСПРАВЛЕНО: Правильный импорт для ExtendedSceneEnvironment
+import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
+import "components"

 /*
- * PneumoStabSim - Main 3D View (Enhanced Realism v2.1)
- * ИСПРАВЛЕНО: ExtendedSceneEnvironment с Qt 6.9.3 совместимостью
- * УЛУЧШЕНО: Орбитальная камера с фиксированным pivot в центре нижней балки
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
-
-    // ===============================================================
-    // CAMERA SYSTEM - Improved Orbital Camera with Fixed Pivot
-    // ===============================================================
-
-    // Фиксированный pivot - всегда центр нижней балки рамы
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
+    // ===============================================================
+
+    // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
+    QtObject {
+        id: animationCache
+
+        // Базовые значения (вычисляются 1 раз за фрейм вместо 4х)
+        property real basePhase: animationTime * userFrequency * 2 * Math.PI
+        property real globalPhaseRad: userPhaseGlobal * Math.PI / 180
+
+        // Предварительно вычисленные фазы для каждого угла
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `<missing>`

```diff

--- origin/main-3b8da9a:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -0,0 +1,228 @@

+import QtQuick
+import QtQuick3D
+
+Item {
+    id: controller
+
+    /**
+      * Primary HDR environment map used for IBL/skybox lighting.
+      * Defaults to the studio lighting provided with the project.
+      */
+    property url primarySource: Qt.resolvedUrl("../../hdr/studio.hdr")
+
+    /**
+      * Optional fallback map that is tried automatically when the primary
+      * asset is missing (useful for developer setups without HDR packages).
+      */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
+    property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main
+
+    /** Internal flag preventing infinite fallback recursion. */
+    property bool _fallbackTried: false
+
+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
+    /** Expose the probe for consumers. */
+    property Texture probe: hdrProbe
+
+    Texture {
+        id: hdrProbe
+        source: controller.primarySource
+>>>>>>> sync/remote-main
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
+        // Отправляем в Python для записи в файл
+        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
+            window.logIblEvent(logEntry)
+        }
+
+        // Также выводим в консоль для отладки
+        if (level === "ERROR" || level === "WARN") {
+            console.warn(logEntry)
+        } else {
+            console.log(logEntry)
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/main-3b8da9a:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/main-3b8da9a:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/main-3b8da9a:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `26fa99f229a8`

```diff

--- origin/main-3b8da9a:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -6,20 +6,39 @@

 from PySide6.QtWidgets import (
     QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
     QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter,
-    QTabWidget, QScrollArea  # NEW: For tabs and scrolling
+    QTabWidget, QScrollArea
 )
-from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
+from PySide6.QtCore import (
+    Qt,
+    QTimer,
+    Slot,
+    QSettings,
+    QUrl,
+    QFileInfo,
+    QByteArray,
+)
 from PySide6.QtGui import QAction, QKeySequence
 from PySide6.QtQuickWidgets import QQuickWidget
 import logging
 import json
 import numpy as np
+import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
-from typing import Optional, Dict
-
-from .charts import ChartWidget
-from .panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
+from typing import Optional, Dict, Any
+
+from src.ui.charts import ChartWidget
+from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -32,10 +51,32 @@

     SETTINGS_APP = "PneumoStabSimApp"
     SETTINGS_GEOMETRY = "MainWindow/Geometry"
     SETTINGS_STATE = "MainWindow/State"
-    SETTINGS_SPLITTER = "MainWindow/Splitter"  # NEW: Save splitter position
-    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"  # NEW: Save horizontal splitter position
-    SETTINGS_LAST_TAB = "MainWindow/LastTab"    # NEW: Save selected tab
+    SETTINGS_SPLITTER = "MainWindow/Splitter"
+    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
+    SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"
+
+    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
+        "geometry": ("applyGeometryUpdates", "updateGeometry"),
+        "animation": ("applyAnimationUpdates", "updateAnimation"),
+        "lighting": ("applyLightingUpdates", "updateLighting"),
+        "materials": ("applyMaterialUpdates", "updateMaterials"),
+        "environment": ("applyEnvironmentUpdates", "updateEnvironment"),
+        "quality": ("applyQualityUpdates", "updateQuality"),
+        "camera": ("applyCameraUpdates", "updateCamera"),
+        "effects": ("applyEffectsUpdates", "updateEffects"),
+    }
+
+    WHEEL_KEY_MAP = {
+        "LP": "fl",
+        "PP": "fr",
+        "LZ": "rl",
+        "PZ": "rr",
... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `008a10f30b83`

```diff

--- origin/main-3b8da9a:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,21 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Отправка начальных параметров геометрии...")
-
-        # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
-        initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer
+
         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
+            self.logger.info("Sending initial geometry to QML...")
+            initial_geometry = self._get_fast_geometry_update("init", 0.0)
             self.geometry_changed.emit(initial_geometry)
             self.geometry_updated.emit(self.parameters.copy())
-            print(f"  ✅ Начальная геометрия отправлена: rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-
-        QTimer.singleShot(100, send_initial_geometry)  # Отправить через 100мс
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -314,88 +316,158 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # Frame dimensions - МГНОВЕННОЕ ОБНОВЛЕНИЕ во время движения
+<<<<<<< HEAD
+        # Реал-тайм: valueChanged для мгновенных обновлений геометрии
+        # Финальное подтверждение: valueEdited
+=======
+        # Используем ТОЛЬКО valueEdited для избежания дублирования событий
+>>>>>>> sync/remote-main
+
+        self.logger.debug("Connecting signals...")
+
+        # Frame dimensions
         self.wheelbase_slider.valueChanged.connect(
             lambda v: self._on_parameter_changed('wheelbase', v))
+        self.wheelbase_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('wheelbase', v))
+<<<<<<< HEAD
+
         self.track_slider.valueChanged.connect(
             lambda v: self._on_parameter_changed('track', v))
-
-        # Suspension geometry - МГНОВЕННОЕ ОБНОВЛЕНИЕ во время движения
+=======
+        # Мгновенные обновления канвы
+        self.wheelbase_slider.valueChanged.connect(
+            lambda v: self._on_parameter_live_change('wheelbase', v))
+
+>>>>>>> sync/remote-main
+        self.track_slider.valueEdited.connect(
+            lambda v: self._on_parameter_changed('track', v))
+        self.track_slider.valueChanged.connect(
+            lambda v: self._on_parameter_live_change('track', v))
+
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `58e7e5155772`

```diff

--- origin/main-3b8da9a:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -1,1626 +1,3053 @@

-"""
-GraphicsPanel - панель настроек графики и визуализации (РАСШИРЕННАЯ ВЕРСИЯ)
-Graphics Panel - comprehensive graphics and visualization settings panel
-РУССКИЙ ИНТЕРФЕЙС (Russian UI) + ПОЛНЫЙ НАБОР ПАРАМЕТРОВ
-"""
+"""Graphics panel providing exhaustive Qt Quick 3D controls."""
+from __future__ import annotations
+
+import copy
+import json
+import logging
+from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
-    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
-    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
-    QColorDialog, QFrame, QSizePolicy, QScrollArea, QTabWidget, QFileDialog, QMessageBox
+    QCheckBox,
+    QColorDialog,
+    QComboBox,
+    QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
+    QGridLayout,
+    QGroupBox,
+    QHBoxLayout,
+    QLabel,
+    QPushButton,
+    QScrollArea,
+    QSlider,
+    QTabWidget,
+    QVBoxLayout,
+    QWidget,
 )
-from PySide6.QtCore import Qt, Signal, Slot, QSettings
-from PySide6.QtGui import QColor, QPalette
-import logging
-from typing import Dict, Any
-import json
+
+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType


 class ColorButton(QPushButton):
-    """Кнопка выбора цвета с предварительным просмотром"""
+    """Small color preview button that streams changes from QColorDialog."""
+
+    color_changed = Signal(str)
+
+    def __init__(self, initial_color: str = "#ffffff", parent: QWidget | None = None) -> None:
+        super().__init__(parent)
+        self.setFixedSize(42, 28)
+        self._color = QColor(initial_color)
+        self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
+        self._update_swatch()
+        self.clicked.connect(self._open_dialog)
+
+    def color(self) -> QColor:
... (обрезано)

```


## origin/merge-latest-remote


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `1129cdb275bb`

```diff

--- origin/merge-latest-remote:app.py

+++ local:app.py

@@ -1,154 +1,233 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# CRITICAL: Terminal and Encoding Configuration
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+
+
+def setup_qtquick3d_environment():
+    """Set up QtQuick3D environment variables before importing Qt"""
+    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
+    if all(var in os.environ for var in required_vars):
+        return True
+
+    try:
+        import importlib.util
+        spec = importlib.util.find_spec("PySide6.QtCore")
+        if spec is None:
+            log_error("PySide6 not found!")
+            return False
+
+        from PySide6.QtCore import QLibraryInfo
+
+        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
+        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
+
+        qtquick3d_env = {
+            "QML2_IMPORT_PATH": str(qml_path),
+            "QML_IMPORT_PATH": str(qml_path),
+            "QT_PLUGIN_PATH": str(plugins_path),
+            "QT_QML_IMPORT_PATH": str(qml_path),
+        }
+
+        for var, value in qtquick3d_env.items():
+            os.environ[var] = value
+
+        return True
+
+    except Exception as e:
+        log_error(f"QtQuick3D setup failed: {e}")
+        return False
+
+
+qtquick3d_setup_ok = setup_qtquick3d_environment()
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/merge-latest-remote:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/merge-latest-remote:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `4646db540136`

```diff

--- origin/merge-latest-remote:.env

+++ local:.env

@@ -1,23 +1,17 @@

-# PneumoStabSim Professional Environment (Автоматически обновлено)
-PYTHONPATH=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/src;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/tests;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/scripts
+# PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
 PYTHONIOENCODING=utf-8
-PYTHONDONTWRITEBYTECODE=1
-
-# Qt Configuration
-QSG_RHI_BACKEND=d3d11
-QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
-QSG_INFO=1
-
-# Project Paths
-PROJECT_ROOT=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional
-SOURCE_DIR=src
-TEST_DIR=tests
-SCRIPT_DIR=scripts
-
-# Development Mode
-DEVELOPMENT_MODE=true
-DEBUG_ENABLED=true
-
-# Russian Localization
-LANG=ru_RU.UTF-8
-COPILOT_LANGUAGE=ru
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/merge-latest-remote:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `30282a0fe558`

```diff

--- origin/merge-latest-remote:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,23 +1,62 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
+import "components"

 /*
- * PneumoStabSim - Unified Optimized 3D View v3.0
- * ✅ Объединяет лучшие части main.qml и main_optimized.qml
- * ✅ Убрано дублирование примитивов
- * ✅ Оптимизированные вычисления с кэшированием
- * ✅ Один файл вместо двух
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему

     // ===============================================================
     // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

-    // Кэширование анимационных вычислений
+    // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
     QtObject {
         id: animationCache

@@ -38,7 +77,7 @@

         property real rrSin: Math.sin(basePhase + rrPhaseRad)
     }

-    // Геометрический калькулятор с кэшированием
+    // ✅ ОПТИМИЗАЦИЯ #2: Геометрический калькулятор
     QtObject {
         id: geometryCache

... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `819d0431be2c`

```diff

--- origin/merge-latest-remote:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,34 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
-    readonly property alias probe: hdrProbe
-
-    /** Simple ready flag to avoid binding against an invalid texture. */
-    readonly property bool ready: hdrProbe.status === Texture.Ready
+    property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
-
-        onStatusChanged: {
-            if (status === Texture.Error && !controller._fallbackTried) {
-                controller._fallbackTried = true
-                console.warn("⚠️ HDR probe not found at", source, "— falling back to", controller.fallbackSource)
-                source = controller.fallbackSource
-            } else if (status === Texture.Ready) {
-                console.log("✅ HDR probe ready:", source)
-            } else if (status === Texture.Error && controller._fallbackTried) {
-                console.warn("❌ Both HDR probes failed to load, IBL will be disabled")
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/merge-latest-remote:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/merge-latest-remote:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/merge-latest-remote:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `e23d5b025dbc`

```diff

--- origin/merge-latest-remote:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -6,20 +6,39 @@

 from PySide6.QtWidgets import (
     QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
     QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter,
-    QTabWidget, QScrollArea  # NEW: For tabs and scrolling
+    QTabWidget, QScrollArea
 )
-from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
+from PySide6.QtCore import (
+    Qt,
+    QTimer,
+    Slot,
+    QSettings,
+    QUrl,
+    QFileInfo,
+    QByteArray,
+)
 from PySide6.QtGui import QAction, QKeySequence
 from PySide6.QtQuickWidgets import QQuickWidget
 import logging
 import json
 import numpy as np
+import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
-from typing import Optional, Dict
+from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -32,51 +51,84 @@

     SETTINGS_APP = "PneumoStabSimApp"
     SETTINGS_GEOMETRY = "MainWindow/Geometry"
     SETTINGS_STATE = "MainWindow/State"
-    SETTINGS_SPLITTER = "MainWindow/Splitter"  # NEW: Save splitter position
-    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"  # NEW: Save horizontal splitter position
-    SETTINGS_LAST_TAB = "MainWindow/LastTab"    # NEW: Save selected tab
+    SETTINGS_SPLITTER = "MainWindow/Splitter"
+    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
+    SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

-    def __init__(self, use_qml_3d: bool = True, force_optimized: bool = False):
+    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
+        "geometry": ("applyGeometryUpdates", "updateGeometry"),
+        "animation": ("applyAnimationUpdates", "updateAnimation"),
+        "lighting": ("applyLightingUpdates", "updateLighting"),
+        "materials": ("applyMaterialUpdates", "updateMaterials"),
+        "environment": ("applyEnvironmentUpdates", "updateEnvironment"),
+        "quality": ("applyQualityUpdates", "updateQuality"),
+        "camera": ("applyCameraUpdates", "updateCamera"),
+        "effects": ("applyEffectsUpdates", "updateEffects"),
+    }
+
+    WHEEL_KEY_MAP = {
+        "LP": "fl",
+        "PP": "fr",
+        "LZ": "rl",
+        "PZ": "rr",
+    }
+
... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `44252a10df56`

```diff

--- origin/merge-latest-remote:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,50 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # ДИАГНОСТИКА: Проверяем подписчиков перед отправкой
-            try:
-                geom_changed_receivers = self.geometry_changed.receivers()
-                geom_updated_receivers = self.geometry_updated.receivers()
-
-                print(f"  📊 Подписчиков на geometry_changed: {geom_changed_receivers}")
-                print(f"  📊 Подписчиков на geometry_updated: {geom_updated_receivers}")
-
-                if geom_changed_receivers > 0:
-                    print(f"  ✅ Есть подписчики, отправляем geometry_changed...")
-                    self.geometry_changed.emit(initial_geometry)
-                    print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_changed, возможно главное окно еще не готово")
-
-                if geom_updated_receivers > 0:
-                    print(f"  ✅ Отправляем geometry_updated...")
-                    self.geometry_updated.emit(self.parameters.copy())
-                    print(f"  📡 geometry_updated отправлен")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_updated")
-
-            except Exception as e:
-                print(f"  ❌ Ошибка проверки подписчиков: {e}")
-                # Отправляем в любом случае
-                self.geometry_changed.emit(initial_geometry)
-                self.geometry_updated.emit(self.parameters.copy())
-                print(f"  📡 Сигналы отправлены без проверки подписчиков")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.geometry_changed.emit(initial_geometry)
+            self.geometry_updated.emit(self.parameters.copy())
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -343,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `58e7e5155772`

```diff

--- origin/merge-latest-remote:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -1,1626 +1,3053 @@

-"""
-GraphicsPanel - панель настроек графики и визуализации (РАСШИРЕННАЯ ВЕРСИЯ)
-Graphics Panel - comprehensive graphics and visualization settings panel
-РУССКИЙ ИНТЕРФЕЙС (Russian UI) + ПОЛНЫЙ НАБОР ПАРАМЕТРОВ
-"""
+"""Graphics panel providing exhaustive Qt Quick 3D controls."""
+from __future__ import annotations
+
+import copy
+import json
+import logging
+from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
-    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
-    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
-    QColorDialog, QFrame, QSizePolicy, QScrollArea, QTabWidget, QFileDialog, QMessageBox
+    QCheckBox,
+    QColorDialog,
+    QComboBox,
+    QDoubleSpinBox,
+<<<<<<< HEAD
+    QFileDialog,
+=======
+>>>>>>> sync/remote-main
+    QGridLayout,
+    QGroupBox,
+    QHBoxLayout,
+    QLabel,
+    QPushButton,
+    QScrollArea,
+    QSlider,
+    QTabWidget,
+    QVBoxLayout,
+    QWidget,
 )
-from PySide6.QtCore import Qt, Signal, Slot, QSettings
-from PySide6.QtGui import QColor, QPalette
-import logging
-from typing import Dict, Any
-import json
+
+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType


 class ColorButton(QPushButton):
-    """Кнопка выбора цвета с предварительным просмотром"""
+    """Small color preview button that streams changes from QColorDialog."""
+
+    color_changed = Signal(str)
+
+    def __init__(self, initial_color: str = "#ffffff", parent: QWidget | None = None) -> None:
+        super().__init__(parent)
+        self.setFixedSize(42, 28)
+        self._color = QColor(initial_color)
+        self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
+        self._update_swatch()
+        self.clicked.connect(self._open_dialog)
+
+    def color(self) -> QColor:
... (обрезано)

```


## origin/qml-method-fixes


### `app.py`

- local sha: `8affdccf5c95` | remote sha: `09057f16e635`

```diff

--- origin/qml-method-fixes:app.py

+++ local:app.py

@@ -1,154 +1,233 @@

 # -*- coding: utf-8 -*-
 """
 PneumoStabSim - Pneumatic Stabilizer Simulator
-Main application entry point with enhanced encoding and terminal support
+Main application entry point - CLEAN TERMINAL VERSION
 """
 import sys
 import os
 import locale
-import logging
 import signal
 import argparse
-import time
+import subprocess
 from pathlib import Path
-
-# =============================================================================
-# CRITICAL: Terminal and Encoding Configuration
-# =============================================================================
+import json
+
+# =============================================================================
+# Накопление warnings/errors
+# =============================================================================
+
+_warnings_errors = []
+
+def log_warning(msg: str):
+    """Накапливает warning для вывода в конце"""
+    _warnings_errors.append(("WARNING", msg))
+
+
+def log_error(msg: str):
+    """Накапливает error для вывода в конце"""
+    _warnings_errors.append(("ERROR", msg))
+
+# =============================================================================
+# QtQuick3D Environment Setup
+# =============================================================================
+
+
+def setup_qtquick3d_environment():
+    """Set up QtQuick3D environment variables before importing Qt"""
+    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
+    if all(var in os.environ for var in required_vars):
+        return True
+
+    try:
+        import importlib.util
+        spec = importlib.util.find_spec("PySide6.QtCore")
+        if spec is None:
+            log_error("PySide6 not found!")
+            return False
+
+        from PySide6.QtCore import QLibraryInfo
+
+        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
+        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
+
+        qtquick3d_env = {
+            "QML2_IMPORT_PATH": str(qml_path),
+            "QML_IMPORT_PATH": str(qml_path),
+            "QT_PLUGIN_PATH": str(plugins_path),
+            "QT_QML_IMPORT_PATH": str(qml_path),
+        }
+
+        for var, value in qtquick3d_env.items():
+            os.environ[var] = value
+
+        return True
+
+    except Exception as e:
+        log_error(f"QtQuick3D setup failed: {e}")
+        return False
+
+
+qtquick3d_setup_ok = setup_qtquick3d_environment()
... (обрезано)

```


### `requirements.txt`

- local sha: `e3bca8ad2c67` | remote sha: `686253a1b300`

```diff

--- origin/qml-method-fixes:requirements.txt

+++ local:requirements.txt

@@ -1,40 +1,39 @@

 # PneumoStabSim Professional - Production Dependencies
-# Проверено для Python 3.8-3.13 (рекомендуется 3.9-3.11)
+# Проверено для Python 3.11-3.13 (рекомендуется 3.13)

 # === КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ===
 # Qt Framework - основа GUI и 3D рендеринга
-PySide6>=6.5.0,<7.0.0    # Qt6 framework для GUI и 3D
-shiboken6                # Qt6 bindings generator
+PySide6>=6.10.0,<7.0.0   # Qt6.10+ (ExtendedSceneEnvironment, Fog, dithering)
+shiboken6                 # Qt6 bindings generator

 # Numerical computing - основа физических расчетов
-numpy>=1.21.0,<3.0.0     # Векторные вычисления
-scipy>=1.7.0,<2.0.0      # Научные вычисления и ODE solver
+numpy>=1.24.0,<3.0.0      # Векторные вычисления
+scipy>=1.10.0,<2.0.0      # Научные вычисления и ODE solver

 # === ДОПОЛНИТЕЛЬНЫЕ ПАКЕТЫ ===
 # Visualization и анализ данных
-matplotlib>=3.5.0        # Графики и чарты
-pillow>=9.0.0            # Обработка изображений для HDR текстур
+matplotlib>=3.5.0         # Графики и чарты
+pillow>=9.0.0             # Обработка изображений для HDR текстур

 # Testing и development
-pytest>=6.0.0           # Тестирование
-PyYAML>=6.0             # Конфигурационные файлы
+pytest>=7.0.0             # Тестирование
+PyYAML>=6.0               # Конфигурационные файлы
+python-dotenv>=1.0.0      # Переменные окружения из .env
+psutil>=5.8.0             # Мониторинг

 # === ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ ===
-# 3D геометрия и визуализация
-# trimesh>=3.15.0        # 3D mesh обработка (опционально)
-# pyqtgraph>=0.12.0      # Быстрые графики (опционально)
-
-# Производительность
-# numba>=0.56.0          # JIT компиляция (опционально)
-# cython>=0.29.0         # C расширения (опционально)
+# trimesh>=3.15.0         # 3D mesh обработка (опционально)
+# pyqtgraph>=0.12.0       # Быстрые графики (опционально)
+# numba>=0.56.0           # JIT компиляция (опционально)
+# cython>=0.29.0          # C расширения (опционально)

 # === СОВМЕСТИМОСТЬ ===
 # Проверено на:
-# - Windows 10/11 (Python 3.9-3.13)
-# - Ubuntu 20.04/22.04 (Python 3.8-3.11)
-# - macOS 11+ (Python 3.9-3.11)
+# - Windows 10/11 (Python 3.11-3.13)
+# - Ubuntu 22.04/24.04 (Python 3.11-3.12)
+# - macOS 13+ (Python 3.11-3.12)

 # Примечания:
-# 1. PySide6 6.9.3+ рекомендуется для ExtendedSceneEnvironment
-# 2. NumPy 2.0+ совместим, но может требовать обновления других пакетов
-# 3. Python 3.13+ - экспериментальная поддержка
+# 1. Требуется PySide6 6.10+ из-за использования Fog и dithering
+# 2. NumPy 2.0+ совместим, но требует обновления других пакетов
+# 3. Python 3.13 поддерживается

```


### `activate_venv.bat`

- local sha: `52cfdc1ad447` | remote sha: `016b78d35fe3`

```diff

--- origin/qml-method-fixes:activate_venv.bat

+++ local:activate_venv.bat

@@ -13,39 +13,43 @@

 echo ================================================================
 echo.

+rem Prefer Python 3.13 if available via py launcher
+set "PYTHON_CMD="
+py -3.13 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
+
+rem Fallback chain
+if not defined PYTHON_CMD (
+    py -3.12 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.12"
+)
+if not defined PYTHON_CMD (
+    py -3.11 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3.11"
+)
+if not defined PYTHON_CMD (
+    py -3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=py -3"
+)
+if not defined PYTHON_CMD (
+    python -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python"
+)
+if not defined PYTHON_CMD (
+    python3 -c "import sys" >nul 2>&1 && set "PYTHON_CMD=python3"
+)
+if not defined PYTHON_CMD (
+    echo ERROR: Python not found or not working
+    echo Please install Python 3.13 and ensure it's in PATH (winget install Python.Python.3.13)
+    pause
+    exit /b 1
+)
+
 rem Check if virtual environment exists
 if not exist "venv\Scripts\activate.bat" (
     echo Creating virtual environment...
-
-    rem Try different Python commands for compatibility
-    python -c "import sys; exit(0)" >nul 2>&1
+
+    rem Warn if version is outside supported range (3.8 - 3.13), continue anyway
+    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 13) else 1)"
     if errorlevel 1 (
-        echo Trying python3...
-        python3 -c "import sys; exit(0)" >nul 2>&1
-        if errorlevel 1 (
-            echo ERROR: Python not found or not working
-            echo Please install Python 3.8-3.11 and ensure it's in PATH
-            pause
-            exit /b 1
-        )
-        set PYTHON_CMD=python3
-    ) else (
-        set PYTHON_CMD=python
+        echo WARNING: Python version may not be fully compatible (recommended 3.13). Continuing...
     )
-
-    rem Check Python version before creating venv
-    %PYTHON_CMD% -c "import sys; major, minor = sys.version_info[:2]; print(f'Using Python {major}.{minor}'); exit(0 if (3, 8) <= (major, minor) <= (3, 12) else 1)"
-    if errorlevel 1 (
-        echo WARNING: Python version may not be fully compatible
-        echo Recommended: Python 3.8 - 3.11
-        echo Continue anyway? (Y/N)
-        set /p choice=
-        if /i not "%choice%"=="Y" if /i not "%choice%"=="y" (
-            echo Setup cancelled by user
-            exit /b 1
-        )
-    )
-
+
     %PYTHON_CMD% -m venv venv --clear
     if errorlevel 1 (
         echo ERROR: Failed to create virtual environment
@@ -79,45 +83,37 @@

 echo Installing project dependencies...
 if exist "requirements.txt" (
     echo Installing from requirements.txt...
-
-    rem First try normal installation
... (обрезано)

```


### `.env`

- local sha: `b3668501ebd9` | remote sha: `4646db540136`

```diff

--- origin/qml-method-fixes:.env

+++ local:.env

@@ -1,23 +1,17 @@

-# PneumoStabSim Professional Environment (Автоматически обновлено)
-PYTHONPATH=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/src;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/tests;C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional/scripts
+# PneumoStabSim Professional Environment Configuration
+
+# Python module paths
+PYTHONPATH=.;src
+
+# Qt/QtQuick options
+QSG_RHI_BACKEND=d3d11
+QSG_INFO=0
+QT_LOGGING_RULES=*.debug=false;*.info=false
+QT_ASSUME_STDERR_HAS_CONSOLE=1
+QT_AUTO_SCREEN_SCALE_FACTOR=1
+QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
+QT_ENABLE_HIGHDPI_SCALING=1
+
+# Python I/O and encoding
 PYTHONIOENCODING=utf-8
-PYTHONDONTWRITEBYTECODE=1
-
-# Qt Configuration
-QSG_RHI_BACKEND=d3d11
-QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
-QSG_INFO=1
-
-# Project Paths
-PROJECT_ROOT=C:\Users\User.GPC-01\source\repos\barmaleii77-hub\PneumoStabSim-Professional
-SOURCE_DIR=src
-TEST_DIR=tests
-SCRIPT_DIR=scripts
-
-# Development Mode
-DEVELOPMENT_MODE=true
-DEBUG_ENABLED=true
-
-# Russian Localization
-LANG=ru_RU.UTF-8
-COPILOT_LANGUAGE=ru
+PYTHONUNBUFFERED=1

```


### `.vscode/launch.json`

- local sha: `2de7d0bea620` | remote sha: `<missing>`

```diff

--- origin/qml-method-fixes:.vscode/launch.json

+++ local:.vscode/launch.json

@@ -0,0 +1,121 @@

+{
+    "version": "0.2.0",
+    "configurations": [
+        {
+            "name": "F5: PneumoStabSim (Главный)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": [],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose (подробные логи)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "main",
+                "order": 2
+            }
+        },
+        {
+            "name": "F5: Test Mode (автозакрытие 5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 1
+            }
+        },
+        {
+            "name": "F5: Verbose + Test (5с)",
+            "type": "python",
+            "request": "launch",
+            "program": "${workspaceFolder}/app.py",
+            "args": ["--verbose", "--test-mode"],
+            "console": "integratedTerminal",
+            "cwd": "${workspaceFolder}",
+            "envFile": "${workspaceFolder}/.env",
+            "env": {
+                "PYTHONPATH": "${workspaceFolder}/src"
+            },
+            "justMyCode": false,
+            "stopOnEntry": false,
+            "presentation": {
+                "group": "test",
+                "order": 2
... (обрезано)

```


### `assets/qml/main.qml`

- local sha: `eec5f339b64a` | remote sha: `e850c61087b9`

```diff

--- origin/qml-method-fixes:assets/qml/main.qml

+++ local:assets/qml/main.qml

@@ -1,19 +1,59 @@

 import QtQuick
 import QtQuick3D
 import QtQuick3D.Helpers
+import QtQuick.Controls
+import Qt.labs.folderlistmodel
 import "components"

 /*
- * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.0)
- * 🚀 ПОЛНАЯ ИНТЕРАЦИЯ: Все параметры GraphicsPanel реализованы
- * ✅ Коэффициент преломления, IBL, расширенные эффекты, тонемаппинг
+ * PneumoStabSim - COMPLETE Graphics Parameters Main 3D View (v4.9.4 SKYBOX FIX)
+ * 🚀 ENHANCED: Separate IBL lighting/background controls + procedural geometry quality
+ * ✅ All properties match official Qt Quick 3D documentation
+ * 🐛 FIXED: Removed skyBoxBlurAmount (not exposed by Qt Quick 3D API)
+ * 🐛 CRITICAL FIX v4.9.4: Skybox rotation with continuous angle accumulation
+ *    - Added envYaw for continuous angle tracking (NO flips at 0°/180°)
+ *    - probeOrientation uses accumulated envYaw instead of direct cameraYaw
+ *    - Background is stable regardless of camera rotation
+ * 🐛 FIXED: emissiveVector typo → emissiveVector
  */
 Item {
     id: root
     anchors.fill: parent
-
-    // ===============================================================
-    // 🚀 PERFORMANCE OPTIMIZATION LAYER (preserved)
+    // Toggle to show/hide in-canvas UI controls (to avoid duplication with external GraphicsPanel)
+    property bool showOverlayControls: false
+
+    // ===============================================================
+    // 🚀 SIGNALS - ACK для Python после применения обновлений
+    // ===============================================================
+
+    signal batchUpdatesApplied(var summary)
+
+    // ===============================================================
+    // 🚀 QT VERSION DETECTION (для условной активации возможностей)
+    // ===============================================================
+
+    readonly property string qtVersionString: typeof Qt.version !== "undefined" ? Qt.version : "6.0.0"
+    readonly property var qtVersionParts: qtVersionString.split('.')
+    readonly property int qtMajor: qtVersionParts.length > 0 ? parseInt(qtVersionParts[0]) : 6
+    readonly property int qtMinor: qtVersionParts.length > 1 ? parseInt(qtVersionParts[1]) : 0
+    readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
+
+    // ✅ Условная поддержка dithering (доступно с Qt 6.10)
+    property bool ditheringEnabled: true  // Управляется из GraphicsPanel
+    readonly property bool canUseDithering: supportsQtQuick3D610Features
+
+    // ===============================================================
+    // 🚀 CRITICAL FIX v4.9.4: SKYBOX ROTATION - INDEPENDENT FROM CAMERA
+    // ===============================================================
+
+    // ✅ ПРАВИЛЬНО: Skybox вращается ТОЛЬКО от пользовательского iblRotationDeg
+    // Камера НЕ влияет на skybox вообще!
+
+    // ❌ УДАЛЕНО: envYaw, _prevCameraYaw, updateCameraYaw() - это было НЕПРАВИЛЬНО
+    // Эти переменные СВЯЗЫВАЛИ фон с камерой, что вызывало проблему
+
+    // ===============================================================
+    // 🚀 PERFORMANCE OPTIMIZATION LAYER
     // ===============================================================

     // ✅ ОПТИМИЗАЦИЯ #1: Кэширование анимационных вычислений
@@ -133,21 +173,39 @@

     property color keyLightColor: "#ffffff"
     property real keyLightAngleX: -35
     property real keyLightAngleY: -40
+    property bool keyLightCastsShadow: true
+    property bool keyLightBindToCamera: false
+    property real keyLightPosX: 0.0
+    property real keyLightPosY: 0.0
     property real fillLightBrightness: 0.7
     property color fillLightColor: "#dfe7ff"
+    property bool fillLightCastsShadow: false
+    property bool fillLightBindToCamera: false
... (обрезано)

```


### `assets/qml/components/IblProbeLoader.qml`

- local sha: `d9f926d7d97b` | remote sha: `819d0431be2c`

```diff

--- origin/qml-method-fixes:assets/qml/components/IblProbeLoader.qml

+++ local:assets/qml/components/IblProbeLoader.qml

@@ -1,7 +1,7 @@

 import QtQuick
 import QtQuick3D

-QtObject {
+Item {
     id: controller

     /**
@@ -14,34 +14,215 @@

       * Optional fallback map that is tried automatically when the primary
       * asset is missing (useful for developer setups without HDR packages).
       */
+<<<<<<< HEAD
+    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
+    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")
+=======
     property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")
+>>>>>>> sync/remote-main

     /** Internal flag preventing infinite fallback recursion. */
     property bool _fallbackTried: false

+<<<<<<< HEAD
+    /**
+      * Double-buffered textures to prevent flicker when switching HDRs.
+      * We keep the last ready texture active while the new one loads.
+      */
+    property int activeIndex: 0         // 0 → texA active, 1 → texB active
+    property int loadingIndex: -1       // index currently loading, -1 if none
+    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
+    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA
+
+    /** Expose the currently active probe for consumers (always Ready if available). */
+    property Texture probe: _activeTex
+
+    Texture {
+        id: texA
+        source: ""
+        minFilter: Texture.Linear
+        magFilter: Texture.Linear
+        generateMipmaps: true
+    }
+    Texture {
+        id: texB
+        source: ""
+=======
     /** Expose the probe for consumers. */
-    readonly property alias probe: hdrProbe
-
-    /** Simple ready flag to avoid binding against an invalid texture. */
-    readonly property bool ready: hdrProbe.status === Texture.Ready
+    property Texture probe: hdrProbe

     Texture {
         id: hdrProbe
         source: controller.primarySource
+>>>>>>> sync/remote-main
         minFilter: Texture.Linear
         magFilter: Texture.Linear
         generateMipmaps: true
-
-        onStatusChanged: {
-            if (status === Texture.Error && !controller._fallbackTried) {
-                controller._fallbackTried = true
-                console.warn("⚠️ HDR probe not found at", source, "— falling back to", controller.fallbackSource)
-                source = controller.fallbackSource
-            } else if (status === Texture.Ready) {
-                console.log("✅ HDR probe ready:", source)
-            } else if (status === Texture.Error && controller._fallbackTried) {
-                console.warn("❌ Both HDR probes failed to load, IBL will be disabled")
+    }
+
+    // ✅ FILE LOGGING SYSTEM для анализа сигналов
+    function writeLog(level, message) {
+        var timestamp = new Date().toISOString()
+        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
+
... (обрезано)

```


### `src/common/logging_setup.py`

- local sha: `cab8f61ae0f7` | remote sha: `5d17b5d0dbe6`

```diff

--- origin/qml-method-fixes:src/common/logging_setup.py

+++ local:src/common/logging_setup.py

@@ -1,6 +1,7 @@

 """
 Logging setup with QueueHandler for non-blocking logging
 Overwrites log file on each run, ensures proper cleanup
+УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
 """

 import logging
@@ -11,27 +12,79 @@

 import os
 import platform
 from pathlib import Path
-from typing import Optional
+from typing import Optional, Dict, Any
 from datetime import datetime
+import traceback


 # Global queue listener for cleanup
 _queue_listener: Optional[logging.handlers.QueueListener] = None
-
-
-def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
+_logger_registry: Dict[str, logging.Logger] = {}
+
+
+class ContextualFilter(logging.Filter):
+    """Добавляет контекстную информацию к логам"""
+
+    def __init__(self, context: Dict[str, Any] = None):
+        super().__init__()
+        self.context = context or {}
+
+    def filter(self, record):
+        # Добавляем контекст к каждому record
+        for key, value in self.context.items():
+            setattr(record, key, value)
+        return True
+
+
+class ColoredFormatter(logging.Formatter):
+    """Форматтер с цветами для консоли (опционально)"""
+
+    COLORS = {
+        'DEBUG': '\033[36m',     # Cyan
+        'INFO': '\033[32m',      # Green
+        'WARNING': '\033[33m',   # Yellow
+        'ERROR': '\033[31m',     # Red
+        'CRITICAL': '\033[35m',  # Magenta
+        'RESET': '\033[0m'
+    }
+
+    def format(self, record):
+        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
+            levelname = record.levelname
+            if levelname in self.COLORS:
+                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
+        return super().format(record)
+
+
+def init_logging(
+    app_name: str,
+    log_dir: Path,
+    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
+    backup_count: int = 5,
+    console_output: bool = False
+) -> logging.Logger:
     """Initialize application logging with non-blocking queue handler

+    УЛУЧШЕНИЯ v4.9.5:
+    - Ротация логов (max_bytes, backup_count)
+    - Опциональный вывод в консоль
+    - Цветной вывод для консоли
+    - Контекстные фильтры
+
     Features:
-    - Overwrites log file on each run (mode='w')
+    - Log rotation with configurable size/count
... (обрезано)

```


### `src/common/event_logger.py`

- local sha: `9b25feb1dfbc` | remote sha: `<missing>`

```diff

--- origin/qml-method-fixes:src/common/event_logger.py

+++ local:src/common/event_logger.py

@@ -0,0 +1,465 @@

+"""
+Unified Event Logger for Python↔QML sync analysis
+Tracks ALL events that should affect scene rendering
+"""
+from __future__ import annotations
+
+import json
+import logging
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, Optional
+from enum import Enum, auto
+
+
+class EventType(Enum):
+    """Типы событий для трекинга"""
+    # Python events
+    USER_CLICK = auto()          # Клик пользователя на UI элемент
+    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
+    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
+    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
+    STATE_CHANGE = auto()        # Изменение state в Python
+    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
+    QML_INVOKE = auto()          # QMetaObject.invokeMethod
+
+    # QML events
+    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
+    FUNCTION_CALLED = auto()     # QML функция вызвана
+    PROPERTY_CHANGED = auto()    # QML property изменилось
+
+    # ✅ НОВОЕ: Mouse events in QML
+    MOUSE_PRESS = auto()         # Нажатие мыши на канве
+    MOUSE_DRAG = auto()          # Перетаскивание
+    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
+    MOUSE_RELEASE = auto()       # Отпускание мыши
+
+    # Errors
+    PYTHON_ERROR = auto()        # Ошибка в Python
+    QML_ERROR = auto()           # Ошибка в QML
+
+
+class EventLogger:
+    """Singleton логгер для отслеживания Python↔QML событий"""
+
+    _instance: Optional['EventLogger'] = None
+    _initialized: bool = False
+
+    def __new__(cls):
+        if cls._instance is None:
+            cls._instance = super().__new__(cls)
+        return cls._instance
+
+    def __init__(self):
+        if EventLogger._initialized:
+            return
+
+        self.logger = logging.getLogger("EventLogger")
+        self.events: list[Dict[str, Any]] = []
+        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
+        EventLogger._initialized = True
+
+    def log_event(
+        self,
+        event_type: EventType,
+        component: str,
+        action: str,
+        *,
+        old_value: Any = None,
+        new_value: Any = None,
+        metadata: Optional[Dict[str, Any]] = None,
+        source: str = "python"
+    ) -> None:
+        """
+        Логирование события
+
+        Args:
+            event_type: Тип события
... (обрезано)

```


### `src/common/log_analyzer.py`

- local sha: `0a5958dc756b` | remote sha: `<missing>`

```diff

--- origin/qml-method-fixes:src/common/log_analyzer.py

+++ local:src/common/log_analyzer.py

@@ -0,0 +1,447 @@

+# -*- coding: utf-8 -*-
+"""
+Комплексный анализатор логов PneumoStabSim
+Объединяет все типы анализов в единую систему
+"""
+
+from pathlib import Path
+from typing import Dict, List, Optional, Tuple
+from datetime import datetime
+import json
+import re
+from collections import defaultdict, Counter
+
+
+class LogAnalysisResult:
+    """Результат анализа логов"""
+
+    def __init__(self):
+        self.errors: List[str] = []
+        self.warnings: List[str] = []
+        self.info: List[str] = []
+        self.metrics: Dict[str, float] = {}
+        self.recommendations: List[str] = []
+        self.status: str = "unknown"  # ok, warning, error
+
+    def is_ok(self) -> bool:
+        """Проверяет, всё ли в порядке"""
+        return len(self.errors) == 0 and self.status != "error"
+
+    def add_error(self, message: str):
+        """Добавляет ошибку"""
+        self.errors.append(message)
+        self.status = "error"
+
+    def add_warning(self, message: str):
+        """Добавляет предупреждение"""
+        self.warnings.append(message)
+        if self.status != "error":
+            self.status = "warning"
+
+    def add_info(self, message: str):
+        """Добавляет информацию"""
+        self.info.append(message)
+        if self.status == "unknown":
+            self.status = "ok"
+
+    def add_metric(self, name: str, value: float):
+        """Добавляет метрику"""
+        self.metrics[name] = value
+
+    def add_recommendation(self, message: str):
+        """Добавляет рекомендацию"""
+        self.recommendations.append(message)
+
+
+class UnifiedLogAnalyzer:
+    """Объединенный анализатор всех типов логов"""
+
+    def __init__(self, logs_dir: Path = Path("logs")):
+        self.logs_dir = logs_dir
+        self.results: Dict[str, LogAnalysisResult] = {}
+
+    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
+        """Запускает полный анализ всех логов"""
+
+        # Основной лог
+        self.results['main'] = self._analyze_main_log()
+
+        # Graphics логи
+        self.results['graphics'] = self._analyze_graphics_logs()
+
+        # IBL логи
+        self.results['ibl'] = self._analyze_ibl_logs()
+
+        # Event логи (Python↔QML)
+        self.results['events'] = self._analyze_event_logs()
+
... (обрезано)

```


### `src/ui/main_window.py`

- local sha: `1cc46fb1468e` | remote sha: `3e59abc4c8ba`

```diff

--- origin/qml-method-fixes:src/ui/main_window.py

+++ local:src/ui/main_window.py

@@ -15,8 +15,6 @@

     QSettings,
     QUrl,
     QFileInfo,
-    QMetaObject,
-    Q_ARG,
     QByteArray,
 )
 from PySide6.QtGui import QAction, QKeySequence
@@ -25,12 +23,22 @@

 import json
 import numpy as np
 import time
+<<<<<<< HEAD
+=======
+from datetime import datetime
+>>>>>>> sync/remote-main
 from pathlib import Path
 from typing import Optional, Dict, Any

 from src.ui.charts import ChartWidget
 from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
 from ..runtime import SimulationManager, StateSnapshot
+from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
+<<<<<<< HEAD
+=======
+# ✅ НОВОЕ: EventLogger для логирования QML вызовов
+from src.common.event_logger import get_event_logger
+>>>>>>> sync/remote-main


 class MainWindow(QMainWindow):
@@ -46,6 +54,10 @@

     SETTINGS_SPLITTER = "MainWindow/Splitter"
     SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
     SETTINGS_LAST_TAB = "MainWindow/LastTab"
+<<<<<<< HEAD
+=======
+
+>>>>>>> sync/remote-main
     SETTINGS_LAST_PRESET = "Presets/LastPath"

     QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
@@ -72,7 +84,7 @@

         # Store visualization backend choice
         self.use_qml_3d = use_qml_3d

-        backend_name = "Qt Quick 3D (Enhanced v5.0)" if use_qml_3d else "Legacy OpenGL"
+        backend_name = "Qt Quick 3D (main.qml v4.3)" if use_qml_3d else "Legacy OpenGL"
         self.setWindowTitle(f"PneumoStabSim - {backend_name}")

         self.resize(1400, 900)
@@ -82,6 +94,17 @@

         # Logging
         self.logger = logging.getLogger(self.__class__.__name__)

+        # ✅ НОВОЕ: Инициализация IBL Signal Logger
+        self.ibl_logger = get_ibl_logger()
+        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
+
+<<<<<<< HEAD
+=======
+        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
+        self.event_logger = get_event_logger()
+        self.logger.info("EventLogger initialized in MainWindow")
+
+>>>>>>> sync/remote-main
         print("MainWindow: Создание SimulationManager...")

         # Simulation manager
@@ -100,6 +123,7 @@

         self._qml_flush_timer = QTimer()
         self._qml_flush_timer.setSingleShot(True)
         self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
+        self._qml_pending_property_supported: Optional[bool] = None

         # State tracking
         self.current_snapshot: Optional[StateSnapshot] = None
... (обрезано)

```


### `src/ui/panels/panel_geometry.py`

- local sha: `409af7b488c8` | remote sha: `44252a10df56`

```diff

--- origin/qml-method-fixes:src/ui/panels/panel_geometry.py

+++ local:src/ui/panels/panel_geometry.py

@@ -40,6 +40,11 @@

         # Dependency resolution state
         self._resolving_conflict = False

+        # Logger
+        from src.common import get_category_logger
+        self.logger = get_category_logger("GeometryPanel")
+        self.logger.info("GeometryPanel initializing...")
+
         # Setup UI
         self._setup_ui()

@@ -52,50 +57,18 @@

         # Size policy
         self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

-        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
-        print("🔧 GeometryPanel: Планируем отправку начальных параметров геометрии...")
-
-        # Используем QTimer для отложенной отправки после полной инициализации UI
+        # Отправляем начальные параметры геометрии в QML
         from PySide6.QtCore import QTimer

         def send_initial_geometry():
-            print("⏰ QTimer: Отправка начальной геометрии...")
-
-            # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
+            self.logger.info("Sending initial geometry to QML...")
             initial_geometry = self._get_fast_geometry_update("init", 0.0)
-
-            # ДИАГНОСТИКА: Проверяем подписчиков перед отправкой
-            try:
-                geom_changed_receivers = self.geometry_changed.receivers()
-                geom_updated_receivers = self.geometry_updated.receivers()
-
-                print(f"  📊 Подписчиков на geometry_changed: {geom_changed_receivers}")
-                print(f"  📊 Подписчиков на geometry_updated: {geom_updated_receivers}")
-
-                if geom_changed_receivers > 0:
-                    print(f"  ✅ Есть подписчики, отправляем geometry_changed...")
-                    self.geometry_changed.emit(initial_geometry)
-                    print(f"  📡 geometry_changed отправлен с rodPosition = {initial_geometry.get('rodPosition', 'НЕ НАЙДЕН')}")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_changed, возможно главное окно еще не готово")
-
-                if geom_updated_receivers > 0:
-                    print(f"  ✅ Отправляем geometry_updated...")
-                    self.geometry_updated.emit(self.parameters.copy())
-                    print(f"  📡 geometry_updated отправлен")
-                else:
-                    print(f"  ⚠️ Нет подписчиков на geometry_updated")
-
-            except Exception as e:
-                print(f"  ❌ Ошибка проверки подписчиков: {e}")
-                # Отправляем в любом случае
-                self.geometry_changed.emit(initial_geometry)
-                self.geometry_updated.emit(self.parameters.copy())
-                print(f"  📡 Сигналы отправлены без проверки подписчиков")
-
-        # УВЕЛИЧИВАЕМ задержку для гарантии готовности главного окна
-        QTimer.singleShot(500, send_initial_geometry)  # Было 100мс, стало 500мс
-        print("  ⏰ Таймер установлен на 500мс для отправки начальной геометрии")
+            self.geometry_changed.emit(initial_geometry)
+            self.geometry_updated.emit(self.parameters.copy())
+            self.logger.info("Initial geometry sent successfully")
+
+        QTimer.singleShot(500, send_initial_geometry)
+        self.logger.info("GeometryPanel initialized successfully")

     def _setup_ui(self):
         """Настроить интерфейс / Setup user interface"""
@@ -343,54 +316,143 @@


     def _connect_signals(self):
         """Connect widget signals"""
-        # ИСПРАВЛЕНО: Используем ТОЛЬКО valueEdited для избежания дублирования событий
-        # valueChanged срабатывает слишком часто (при каждом движении), valueEdited - только при завершении редактирования
-
... (обрезано)

```


### `src/ui/panels/panel_graphics.py`

- local sha: `63ddf98b45ab` | remote sha: `68276b0087da`

```diff

--- origin/qml-method-fixes:src/ui/panels/panel_graphics.py

+++ local:src/ui/panels/panel_graphics.py

@@ -5,15 +5,28 @@

 import json
 import logging
 from typing import Any, Dict
+from pathlib import Path
+<<<<<<< HEAD
+from urllib.parse import urlparse
+from pathlib import PurePosixPath

 from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
 from PySide6.QtGui import QColor, QStandardItem
+=======
+
+from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
+from PySide6.QtGui import QColor, QStandardItem
+from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
+>>>>>>> sync/remote-main
 from PySide6.QtWidgets import (
     QCheckBox,
     QColorDialog,
     QComboBox,
     QDoubleSpinBox,
+<<<<<<< HEAD
     QFileDialog,
+=======
+>>>>>>> sync/remote-main
     QGridLayout,
     QGroupBox,
     QHBoxLayout,
@@ -26,6 +39,12 @@

     QWidget,
 )

+# Импортируем логгер графических изменений
+from .graphics_logger import get_graphics_logger
+
+# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
+from src.common.event_logger import get_event_logger, EventType
+

 class ColorButton(QPushButton):
     """Small color preview button that streams changes from QColorDialog."""
@@ -37,6 +56,7 @@

         self.setFixedSize(42, 28)
         self._color = QColor(initial_color)
         self._dialog = None
+        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
         self._update_swatch()
         self.clicked.connect(self._open_dialog)

@@ -44,6 +64,7 @@

         return self._color

     def set_color(self, color_str: str) -> None:
+        """Программное изменение цвета (без логирования)"""
         self._color = QColor(color_str)
         self._update_swatch()

@@ -59,6 +80,9 @@


     @Slot()
     def _open_dialog(self) -> None:
+        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
+        self._user_triggered = True
+
         if self._dialog:
             return

@@ -77,13 +101,17 @@

             return
         self._color = color
         self._update_swatch()
-        self.color_changed.emit(color.name())
+
+        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
+        if self._user_triggered:
+            self.color_changed.emit(color.name())

... (обрезано)

```
