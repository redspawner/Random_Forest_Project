@echo off
REM Create a virtual environment, install the libraries and build the demo files (Windows).
cd /d "%~dp0"
py -3 -m venv .venv || python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python make_demo_data.py
.venv\Scripts\python train.py data\synthetic\synthetic_training_cohort.xlsx
echo.
echo Installation finished. Start the app by double-clicking run_app.bat
pause
