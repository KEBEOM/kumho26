#!/bin/bash
# 사용법: 터미널에서  bash 실행하기_mac_linux.sh
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
echo "앱을 켭니다. 스마트폰은 같은 Wi-Fi에서 http://PC-IP:8501"
(sleep 5; (command -v open >/dev/null && open http://localhost:8501) || xdg-open http://localhost:8501) >/dev/null 2>&1 &
streamlit run app.py --server.address 0.0.0.0
