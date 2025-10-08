@echo off
echo ================================================================
echo  Installing Development Dependencies
echo ================================================================
echo.

rem Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Virtual environment not activated. Activating...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else (
        echo Virtual environment not found. Please run activate_venv.bat first.
        pause
        exit /b 1
    )
)

echo Installing development dependencies...
pip install -r requirements-dev.txt

echo.
echo ================================================================
echo  Development Environment Ready!
echo ================================================================
echo.
echo Available development tools:
echo   pytest                          # Run tests
echo   pytest --cov                    # Run tests with coverage
echo   black .                         # Format code
echo   flake8                          # Check code style
echo   mypy src                        # Type checking
echo   pylint src                      # Code analysis
echo.
echo Available notebooks:
echo   jupyter notebook                # Start Jupyter
echo   jupyter lab                     # Start JupyterLab
echo.
echo Profile and benchmark:
echo   python -m memory_profiler app.py
echo   python -m line_profiler app.py
echo.
