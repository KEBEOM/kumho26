#!/bin/bash
cd "$(dirname "$0")" || exit 1
bash run_mac_linux.sh
status=$?
if [ "$status" -ne 0 ]; then
  echo '실행에 실패했습니다. 위 오류와 README의 해결 방법을 확인하세요.'
  read -r -p 'Enter를 누르면 닫힙니다.'
fi
exit "$status"
