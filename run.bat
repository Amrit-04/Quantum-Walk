@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo    Starting QuMa: Quantum Maze (Qiskit Simulation)
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while running the game.
    pause
)
