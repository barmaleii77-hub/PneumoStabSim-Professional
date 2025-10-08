#!/bin/bash

echo "================================================================"
echo " PneumoStabSim Professional - Virtual Environment Setup"
echo "================================================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
        echo -e "${RED}Please ensure Python 3 is installed and accessible${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
    echo
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}Installing project dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${YELLOW}WARNING: requirements.txt not found, installing basic packages...${NC}"
    pip install numpy scipy pyside6 matplotlib PyOpenGL PyOpenGL-accelerate
fi

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
export PYTHONPATH="$(pwd):$(pwd)/src"
export QSG_RHI_BACKEND="opengl"  # Use OpenGL on Linux/macOS
export QT_LOGGING_RULES="js.debug=true;qt.qml.debug=true"
export PYTHONOPTIMIZE="1"
export PYTHONUNBUFFERED="1"

echo
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN} Virtual Environment Ready!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo
echo -e "${CYAN}Environment: $VIRTUAL_ENV${NC}"
echo -e "${CYAN}Python Version:${NC}"
python --version
echo
echo -e "${YELLOW}Available commands:${NC}"
echo "  python app.py                    # Run main application"
echo "  python app.py --test-mode        # Test mode (auto-close 5s)"
echo "  python app.py --debug            # Debug mode"
echo "  python scripts/check_environment.py    # Environment check"
echo "  python scripts/comprehensive_test.py   # Full project test"
echo "  deactivate                       # Exit virtual environment"
echo
echo -e "${GREEN}================================================================${NC}"

# Keep the session active
exec "$SHELL"
