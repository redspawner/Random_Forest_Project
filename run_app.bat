@echo off
REM Start the drag-and-drop app (Windows). Run install.bat once before.
cd /d "%~dp0"
.venv\Scripts\python run_app.py
pause
