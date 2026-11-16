@echo off
chcp 65001 > nul
cd /d "%~dp0"
if exist ".venv-win\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 (python -m venv .venv-win) else (py -3 -m venv .venv-win)
if errorlevel 1 goto failed
:install
.venv-win\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo 브라우저에서 http://localhost:8501 을 여세요.
echo 스마트폰: 같은 Wi-Fi에서 http://PC-IP:8501
.venv-win\Scripts\python.exe -m streamlit run app.py --server.address 0.0.0.0
if errorlevel 1 goto failed
exit /b 0
:failed
echo Python 3.12 설치와 인터넷 연결을 확인하고 README를 참고하세요.
pause
exit /b 1
