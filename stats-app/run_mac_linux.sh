#!/bin/bash
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo 'Python 3.12를 먼저 설치하세요.'; exit 1; }
ENV_DIR=".venv-unix"
if [ ! -x "$ENV_DIR/bin/python" ]; then
  python3 -m venv "$ENV_DIR"
fi
"$ENV_DIR/bin/python" -m pip install -r requirements.txt
printf '%s\n' '브라우저에서 http://localhost:8501 을 여세요.' '스마트폰: 같은 Wi-Fi에서 http://PC-IP:8501'
"$ENV_DIR/bin/python" -m streamlit run app.py --server.address 0.0.0.0
