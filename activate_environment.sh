#!/bin/bash
# ============================================================================
# PneumoStabSim Professional - Environment Activation (Linux/macOS)
# Активация окружения в текущей bash сессии
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading environment from .env..."

    # Export variables from .env file
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]]; then
   # Remove leading/trailing whitespace
       key=$(echo "$key" | xargs)
          value=$(echo "$value" | xargs)

          # Remove quotes if present
    value="${value%\"}"
      value="${value#\"}"
            value="${value%\'}"
   value="${value#\'}"

            export "$key=$value"
    echo "  ✅ $key"
 fi
    done < "$ENV_FILE"

    echo ""
    echo "✅ Environment activated!"
    echo "📦 PYTHONPATH: $PYTHONPATH"
    echo "🎨 QT Backend: $QSG_RHI_BACKEND"
else
    echo "⚠️  .env file not found. Run ./setup_all_paths.sh first."
fi
