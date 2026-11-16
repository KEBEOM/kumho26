"""앱 화면 테스트 (Streamlit AppTest): 모든 메뉴가 오류 없이 열리는지 확인.

streamlit 이 설치된 환경(PC, GitHub Actions)에서만 실행되고, 없으면 건너뜁니다.
"""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")
MENUS = [
    "0. 데이터 확인", "1. 기초통계", "2. 정규성 검정", "3. 상관분석", "4. t검정",
    "5. 교차분석 (카이제곱)", "6. 신뢰도 (Cronbach α)", "7. 단순회귀", "8. 다중회귀",
    "9. 일원분산분석", "10. 이원분산분석", "11. 매개효과 (X→M→Y)", "12. 조절효과 (X×W→Y)",
    "13. 기준값 검산", "14. 보고서 내려받기",
]
DATASETS = ["기준데이터 (교수자 검산용, 36행)", "설문 예제 (가상 설문, 120명)", "sample.xlsx (연습용, 12행)"]


def _by_label(widgets, label):
    for w in widgets:
        if w.label == label:
            return w
    raise AssertionError(f"'{label}' 위젯을 찾지 못했습니다.")


def test_start_screen():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("파일을 올리거나" in i.value for i in at.info)


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("menu", MENUS)
def test_every_menu_runs(menu, dataset):
    at = AppTest.from_file(APP, default_timeout=60).run()
    _by_label(at.radio, "데이터 선택").set_value("예제 데이터 사용").run()
    _by_label(at.selectbox, "예제 파일").set_value(dataset).run()
    _by_label(at.selectbox, "분석 메뉴").set_value(menu).run()
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]


def test_reference_menu_all_match():
    at = AppTest.from_file(APP, default_timeout=60).run()
    _by_label(at.radio, "데이터 선택").set_value("예제 데이터 사용").run()
    _by_label(at.selectbox, "분석 메뉴").set_value("13. 기준값 검산").run()
    values = [m.value for m in at.metric]
    assert "27 / 27" in values, values


def test_credit_shown():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert any("빅데이터 8조" in m.value for m in at.markdown)


def test_report_flow():
    at = AppTest.from_file(APP, default_timeout=60).run()
    _by_label(at.radio, "데이터 선택").set_value("예제 데이터 사용").run()
    _by_label(at.selectbox, "분석 메뉴").set_value("7. 단순회귀").run()
    _by_label(at.button, "보고서에 담기").click().run()
    assert len(at.session_state["report"]) == 1
    _by_label(at.selectbox, "분석 메뉴").set_value("14. 보고서 내려받기").run()
    assert not at.exception
