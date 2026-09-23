@echo off
rem Cube Timer launcher - starts the timer with pythonw (no console window)
cd /d "%~dp0"

where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw "cube_timer.py"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    python "cube_timer.py"
    exit /b 0
)

echo.
echo Python not found. Please install Python 3.10+ with "Add python.exe to PATH".
echo Download: https://www.python.org/downloads/
echo.
pause