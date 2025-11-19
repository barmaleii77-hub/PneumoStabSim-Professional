#!/bin/bash
# ============================================================================
# PneumoStabSim Professional - PATH Setup (Linux/macOS)
# Быстрая настройка окружения для Unix-подобных систем
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_PATH="$PROJECT_ROOT/src"
TESTS_PATH="$PROJECT_ROOT/tests"
SCRIPTS_PATH="$PROJECT_ROOT/scripts"
ASSETS_PATH="$PROJECT_ROOT/assets"
CONFIG_PATH="$PROJECT_ROOT/config"
LOGS_PATH="$PROJECT_ROOT/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_section() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Cached state for tooling detection
PYTHON_CMD=""
QT_PLUGIN_PATH_VALUE=""
QML_IMPORT_PATH_VALUE=""
QML2_IMPORT_PATH_VALUE=""

# Find Python once per session to avoid repeated PATH scans
find_python() {
    if [ -n "$PYTHON_CMD" ]; then
        echo "$PYTHON_CMD"
        return 0
    fi

    for cmd in py python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            VERSION=$($cmd --version 2>&1)
            echo_success "Found Python: $cmd ($VERSION)"
            PYTHON_CMD="$cmd"
            echo "$PYTHON_CMD"
            return 0
        fi
    done

    echo_error "Python not found in PATH"
    return 1
}

detect_qt_paths() {
    local python_cmd
    python_cmd=$(find_python) || return 1

    local result
    if ! result=$($python_cmd <<'PY' 2>/dev/null); then
from PySide6.QtCore import QLibraryInfo

paths = {
    "QML2_IMPORT_PATH": QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath),
    "QML_IMPORT_PATH": QLibraryInfo.path(QLibraryInfo.LibraryPath.ImportsPath),
    "QT_PLUGIN_PATH": QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath),
}

for key, value in paths.items():
    if value:
        print(f"{key}={value}")
PY
        echo_warning "PySide6 is not available — Qt paths will not be exported"
        return 1
    fi

    if [ -z "$result" ]; then
        echo_warning "Qt paths were not detected by PySide6"
        return 1
    fi

    echo "$result"
}

apply_qt_paths() {
    local qt_info
    if ! qt_info=$(detect_qt_paths); then
        return 1
    fi

    while IFS='=' read -r key value; do
        case "$key" in
            QML2_IMPORT_PATH)
                export QML2_IMPORT_PATH="$value"
                QML2_IMPORT_PATH_VALUE="$value"
                ;;
            QML_IMPORT_PATH)
                export QML_IMPORT_PATH="$value"
                QML_IMPORT_PATH_VALUE="$value"
                ;;
            QT_PLUGIN_PATH)
                export QT_PLUGIN_PATH="$value"
                QT_PLUGIN_PATH_VALUE="$value"
                ;;
        esac
    done <<< "$qt_info"

    echo_success "Qt import/plugin paths configured"
    return 0
}

# Setup environment
setup_environment() {
    echo_section "Setting Up Environment"

    # PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT:$SRC_PATH:$TESTS_PATH:$SCRIPTS_PATH"
    echo_success "PYTHONPATH configured"

    # Python settings
    export PYTHONIOENCODING="utf-8"
    export PYTHONUNBUFFERED="1"
  export PYTHONOPTIMIZE="1"
    export PYTHONDONTWRITEBYTECODE="1"
  echo_success "Python settings configured"

    # Qt settings (headless-friendly defaults)
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
    export QSG_RHI_BACKEND="${QSG_RHI_BACKEND:-opengl}"
    export QT_QUICK_BACKEND="${QT_QUICK_BACKEND:-software}"
    export QT_QUICK_CONTROLS_STYLE="${QT_QUICK_CONTROLS_STYLE:-Basic}"
    export QT_AUTO_SCREEN_SCALE_FACTOR="${QT_AUTO_SCREEN_SCALE_FACTOR:-1}"
    export QT_ENABLE_HIGHDPI_SCALING="1"
    export QT_SCALE_FACTOR_ROUNDING_POLICY="PassThrough"
    export QT_LOGGING_RULES="${QT_LOGGING_RULES:-*.debug=false;qt.scenegraph.general=false}"
    export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
    export QSG_INFO="0"
    apply_qt_paths || echo_warning "Continuing without explicit Qt import paths"
    echo_success "Qt settings configured"

    # Project paths
    export PROJECT_ROOT="$PROJECT_ROOT"
    export SOURCE_DIR="$SRC_PATH"
    export TESTS_DIR="$TESTS_PATH"
    export SCRIPTS_DIR="$SCRIPTS_PATH"
    export ASSETS_DIR="$ASSETS_PATH"
 export CONFIG_DIR="$CONFIG_PATH"
    export LOGS_DIR="$LOGS_PATH"
    echo_success "Project paths configured"

    # Locale
    export LANG="ru_RU.UTF-8"
    export LC_ALL="ru_RU.UTF-8"
    export COPILOT_LANGUAGE="ru"
 echo_success "Locale configured"

    # Development mode
    export DEVELOPMENT_MODE="true"
    export DEBUG_ENABLED="true"
echo_success "Development mode enabled"
}

# Create .env file
create_env_file() {
    echo_section "Creating .env File"

    local env_file="$PROJECT_ROOT/.env"

    cat > "$env_file" << EOF
# PneumoStabSim Professional Environment
# Auto-generated by setup_all_paths.sh
# Last updated: $(date '+%Y-%m-%d %H:%M:%S')

# ============================================================================
# PYTHON PATHS
# ============================================================================
PYTHONPATH=$PROJECT_ROOT:$SRC_PATH:$TESTS_PATH:$SCRIPTS_PATH
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONOPTIMIZE=1
PYTHONDONTWRITEBYTECODE=1

# ============================================================================
# QT CONFIGURATION
# ============================================================================
QT_QPA_PLATFORM=${QT_QPA_PLATFORM}
QSG_RHI_BACKEND=${QSG_RHI_BACKEND}
QT_QUICK_BACKEND=${QT_QUICK_BACKEND}
QT_QUICK_CONTROLS_STYLE=${QT_QUICK_CONTROLS_STYLE}
QT_AUTO_SCREEN_SCALE_FACTOR=${QT_AUTO_SCREEN_SCALE_FACTOR}
QT_ENABLE_HIGHDPI_SCALING=1
QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
QT_LOGGING_RULES=${QT_LOGGING_RULES}
QSG_INFO=${QSG_INFO}
LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE}

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT=$PROJECT_ROOT
SOURCE_DIR=$SRC_PATH
TESTS_DIR=$TESTS_PATH
SCRIPTS_DIR=$SCRIPTS_PATH
ASSETS_DIR=$ASSETS_PATH
CONFIG_DIR=$CONFIG_PATH
LOGS_DIR=$LOGS_PATH

# ============================================================================
# LOCALE
# ============================================================================
LANG=ru_RU.UTF-8
LC_ALL=ru_RU.UTF-8
COPILOT_LANGUAGE=ru

# ============================================================================
# DEVELOPMENT
# ============================================================================
DEVELOPMENT_MODE=true
DEBUG_ENABLED=true

EOF

    if [ -n "${QML2_IMPORT_PATH_VALUE}${QML_IMPORT_PATH_VALUE}${QT_PLUGIN_PATH_VALUE}" ]; then
        cat >> "$env_file" << EOF
# ============================================================================
# DETECTED QT PATHS
# ============================================================================
QML2_IMPORT_PATH=${QML2_IMPORT_PATH_VALUE}
QML_IMPORT_PATH=${QML_IMPORT_PATH_VALUE}
QT_PLUGIN_PATH=${QT_PLUGIN_PATH_VALUE}

EOF
    else
        cat >> "$env_file" << 'EOF'
# Qt import paths were not detected automatically. Re-run setup_all_paths.sh
# after installing PySide6 to capture them here.

EOF
    fi

    echo_success ".env file created"
}

# Verify installation
verify_installation() {
    echo_section "Verifying Installation"

    PYTHON_CMD=$(find_python) || exit 1

    # Test imports
    echo_info "Testing Python imports..."

  for module in PySide6.QtCore PySide6.QtWidgets PySide6.QtQuick3D numpy scipy; do
        if $PYTHON_CMD -c "import $module" 2>/dev/null; then
echo_success "$module"
        else
            echo_warning "$module (not found)"
        fi
    done

    # Check project structure
  echo_info "Checking project structure..."

    for path in "$SRC_PATH" "$ASSETS_PATH" "$CONFIG_PATH"; do
        if [ -d "$path" ]; then
         echo_success "$(basename $path) directory exists"
     else
   echo_warning "$(basename $path) directory not found"
        fi
    done
}

# Main execution
main() {
    echo -e "${CYAN}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║       ║
║ PneumoStabSim Professional - PATH Setup Tool (Unix)        ║
║         ║
║        Комплексная настройка всех путей проекта      ║
║           ║
╚════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    setup_environment
    create_env_file
    verify_installation

    echo_section "Setup Complete!"

    echo_info ""
    echo_info "To activate in current shell:"
    echo -e "  ${GREEN}source ./activate_environment.sh${NC}"
    echo_info ""
  echo_info "To run the application:"
    echo -e "  ${GREEN}python3 app.py${NC}"
    echo_info ""
}

main "$@"
