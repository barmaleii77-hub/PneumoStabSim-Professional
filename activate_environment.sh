#!/bin/bash
# ============================================================================
# PneumoStabSim Professional - Environment Activation (Linux/macOS)
# Активация окружения в текущей bash сессии
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

PY_VERSION_OVERRIDE=""
QT_INSTALL="false"
QT_VERSION_OVERRIDE=""
QT_MODULES_OVERRIDE=""
QT_OUTPUT_OVERRIDE=""
HASH_FILE_OVERRIDE=""
HASH_LOG_OVERRIDE=""
RUN_SETUP="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
    --python-version)
  PY_VERSION_OVERRIDE="$2"
      shift 2
   ;;
    --install-qt)
  QT_INSTALL="true"
   shift
       ;;
   --qt-version)
   QT_VERSION_OVERRIDE="$2"
+  shift 2
       ;;
   --qt-modules)
   QT_MODULES_OVERRIDE="$2"
+  shift 2
   ;;
   --qt-output-dir)
   QT_OUTPUT_OVERRIDE="$2"
+  shift 2
       ;;
   --hash-file)
        HASH_FILE_OVERRIDE="$2"
+      shift 2
   ;;
    --hash-log-file)
   HASH_LOG_OVERRIDE="$2"
+      shift 2
   ;;
    --setup)
+ RUN_SETUP="true"
+  shift
   ;;
    --help|-h)
      cat <<'USAGE'
Usage: source activate_environment.sh [options]

Options:
  --python-version <ver>   Выбрать версию Python для setup_environment.py
  --install-qt   Установить Qt SDK перед активацией
  --qt-version <ver>  Версия Qt SDK
  --qt-modules <list>      Список модулей Qt (через запятую)
  --qt-output-dir <path>   Каталог установки Qt SDK
  --hash-file <path>   Файл зависимостей с хешами
  --hash-log-file <path>   Лог проверки хешей
  --setup   Запустить setup_environment.py с указанными опциями
  -h, --helpПоказать это сообщение
USAGE
   return 0 2>/dev/null || exit 0
   ;;
    *)
   echo "Неизвестный параметр: $1"
   return 1 2>/dev/null || exit 1
   ;;
    esac
done

if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading environment from .env..."

    # Export variables from .env file
    while IFS='=' read -r key value; do
   # Skip comments and empty lines
   if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]]; then
-   # Remove leading/trailing whitespace
-  key=$(echo "$key" | xargs)
-      value=$(echo "$value" | xargs)
+   # Remove leading/trailing whitespace
+ key=$(echo "$key" | xargs)
+       value=$(echo "$value" | xargs)

-    # Remove quotes if present
-value="${value%\"}"
-  value="${value#\"}"
+       # Remove quotes if present
+   value="${value%\"}"
+      value="${value#\"}"
    value="${value%\'}"
-   value="${value#\'}"
+ value="${value#\'}"

    export "$key=$value"
-    echo "  ✅ $key"
- fi
+      echo "  ✅ $key"
+  fi
     done < "$ENV_FILE"

     echo ""
     echo "✅ Environment activated!"
     echo "📦 PYTHONPATH: $PYTHONPATH"
     echo "🎨 QT Backend: $QSG_RHI_BACKEND"
 else
     echo "⚠️  .env file not found. Run ./setup_all_paths.sh first."
 fi

if [[ -n "$PY_VERSION_OVERRIDE" ]]; then
+    export PYTHON_VERSION="$PY_VERSION_OVERRIDE"
+    echo "🔁 PYTHON_VERSION overridden to $PY_VERSION_OVERRIDE"
+fi
+
+if [[ -n "$QT_VERSION_OVERRIDE" ]]; then
+    export QT_SDK_VERSION="$QT_VERSION_OVERRIDE"
+    echo "🎨 QT_SDK_VERSION overridden to $QT_VERSION_OVERRIDE"
+fi
+
+if [[ -n "$QT_MODULES_OVERRIDE" ]]; then
+    export QT_SDK_MODULES="$QT_MODULES_OVERRIDE"
+    echo "🎨 QT_SDK_MODULES overridden to $QT_MODULES_OVERRIDE"
+fi
+
+if [[ -n "$QT_OUTPUT_OVERRIDE" ]]; then
+    export QT_SDK_ROOT="$QT_OUTPUT_OVERRIDE"
+    echo "📁 QT_SDK_ROOT overridden to $QT_OUTPUT_OVERRIDE"
+fi
+
+if [[ -n "$HASH_FILE_OVERRIDE" ]]; then
+    export DEPENDENCIES_FILE="$HASH_FILE_OVERRIDE"
+    export DEPENDENCY_HASHES_ENABLED="true"
+    echo "🔐 DEPENDENCIES_FILE overridden to $HASH_FILE_OVERRIDE"
+fi
+
+if [[ -n "$HASH_LOG_OVERRIDE" ]]; then
+    export DEPENDENCY_HASH_LOG="$HASH_LOG_OVERRIDE"
+    echo "📝 DEPENDENCY_HASH_LOG overridden to $HASH_LOG_OVERRIDE"
+fi
+
+if [[ "$QT_INSTALL" == "true" ]]; then
+export INSTALL_QT_SDK="1"
+fi
+
+if [[ "$RUN_SETUP" == "true" ]]; then
+    PYTHON_BIN="$(command -v python3 || command -v python)"
+if [[ -z "$PYTHON_BIN" ]]; then
+        echo "❌ Python не найден для запуска setup_environment.py"
+        return 1 2>/dev/null || exit 1
+    fi
+
+    SETUP_ARGS=("$PYTHON_BIN" "$PROJECT_ROOT/setup_environment.py")
+    if [[ -n "$PY_VERSION_OVERRIDE" ]]; then
+   SETUP_ARGS+=("--python-version" "$PY_VERSION_OVERRIDE")
+    fi
+    if [[ "$QT_INSTALL" == "true" ]]; then
+        SETUP_ARGS+=("--install-qt")
+    fi
+if [[ -n "$QT_VERSION_OVERRIDE" ]]; then
+   SETUP_ARGS+=("--qt-version" "$QT_VERSION_OVERRIDE")
+    fi
+    if [[ -n "$QT_MODULES_OVERRIDE" ]]; then
+  SETUP_ARGS+=("--qt-modules" "$QT_MODULES_OVERRIDE")
+    fi
+    if [[ -n "$QT_OUTPUT_OVERRIDE" ]]; then
+    SETUP_ARGS+=("--qt-output-dir" "$QT_OUTPUT_OVERRIDE")
+    fi
+    if [[ -n "$HASH_FILE_OVERRIDE" ]]; then
+   SETUP_ARGS+=("--hash-file" "$HASH_FILE_OVERRIDE")
+    fi
+    if [[ -n "$HASH_LOG_OVERRIDE" ]]; then
+   SETUP_ARGS+=("--hash-log-file" "$HASH_LOG_OVERRIDE")
+    fi
+
+    echo "🚀 Running setup_environment.py with overrides..."
+    "${SETUP_ARGS[@]}"
+fi
