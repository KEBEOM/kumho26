@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo [1/3] Python check...
python --version || (echo Python is not installed. Install from https://www.python.org and check "Add to PATH". & pause & exit /b)
if not exist .venv (echo [2/3] Creating virtual env... & python -m venv .venv)
call .venv\Scripts\activate
echo [2/3] Installing packages (first run takes a few minutes)...
pip install -q -r requirements.txt
echo [3/3] Starting app. Phone: http://PC-IP:8501 (same Wi-Fi)
start "" cmd /c "timeout /t 5 > nul & start http://localhost:8501"
streamlit run app.py --server.address 0.0.0.0
pause
