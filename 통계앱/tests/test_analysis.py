"""검산 테스트: python -m pytest -q tests

교수자 기준결과(02_기준결과_검산표.md)와 앱 계산값이 일치하는지 자동으로 확인합니다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import pytest

import analysis as A

REF = pd.read_excel(ROOT / "data" / "기준데이터.xlsx")


def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def test_descriptive_statistics():
    out = A.descriptive_statistics(pd.DataFrame({"x": [1, 2, 3, None]}), ["x"])
    assert out.loc[0, "사용 사례 수(n)"] == 3
    assert out.loc[0, "결측 수"] == 1
    assert round(out.loc[0, "평균"], 6) == 2


def test_week1_descriptive():
    r = A.descriptive_statistics(REF, ["score"]).iloc[0]
    assert r["사용 사례 수(n)"] == 36
    assert close(r["평균"], 76.000, 1e-3) and close(r["표준편차"], 8.135, 1e-3)
    assert r["중앙값"] == 76 and r["최소값"] == 60 and r["최대값"] == 92


def test_week2_simple_regression():
    r = A.regression(REF, "score", ["study_time"])
    assert close(r["r2"], 0.0330, 1e-4)
    assert close(r["coef"]["B"][0], 72.4268, 1e-4)
    assert close(r["coef"]["B"][1], 1.1089, 1e-4)
    assert close(r["coef"]["p"][1], 0.288707, 1e-6)


def test_week3_multiple_regression():
    r = A.regression(REF, "score", ["study_time", "pre_score"])
    assert close(r["r2"], 0.9349, 1e-4) and close(r["adj_r2"], 0.9310, 1e-4)
    assert close(r["coef"]["B"][1], 0.0729, 1e-4) and close(r["coef"]["p"][1], 0.792724, 1e-6)
    assert close(r["coef"]["B"][2], 0.8912, 1e-4) and r["coef"]["p"][2] < 1e-6
    assert r["vif"] is not None and (r["vif"]["VIF"] < 10).all()


def test_week4_one_way_anova():
    r = A.one_way_anova(REF, "anova_score", "method")
    assert close(r["F"], 14.0291, 1e-4) and close(r["p"], 0.000039, 1e-6)
    assert [round(v, 3) for v in r["desc"]["평균"]] == [55.166, 58.193, 62.407]
    assert len(r["posthoc"]) == 3


def test_week5_two_way_anova():
    t = A.two_way_anova(REF, "anova_score", "method", "grade")["table"]
    assert close(t["F"][0], 266.3419, 1e-4)
    assert close(t["F"][1], 283.2311, 1e-4)
    assert close(t["F"][2], 8.2607, 1e-4) and close(t["p"][2], 0.000174, 1e-6)


def test_week6_mediation():
    r = A.mediation(REF, "med_x", "med_m", "med_y", n_boot=500)
    assert close(r["a"], 0.8027, 1e-4) and close(r["b"], 1.5300, 1e-4)
    assert close(r["c_prime"], 0.1383, 1e-4) and close(r["ab"], 1.2282, 1e-4)
    assert close(r["c"], r["c_prime"] + r["ab"], 1e-8)  # c = c' + ab (OLS 항등식)


def test_week7_moderation():
    r = A.moderation(REF, "mod_x", "mod_w", "mod_y")
    assert close(r["int_row"]["B"], 0.6786, 1e-4) and r["int_row"]["p"] < 1e-6
    assert close(r["r2"], 0.9743, 1e-4)
    c = A.moderation(REF, "mod_x", "mod_w", "mod_y", center=True)  # 중심화해도 상호작용·R² 동일
    assert close(c["int_row"]["B"], r["int_row"]["B"], 1e-9) and close(c["r2"], r["r2"], 1e-9)


def test_reference_check_all_match():
    chk = A.reference_check(REF)
    assert (chk["판정"] == "일치").all(), chk[chk["판정"] != "일치"]


@pytest.mark.parametrize("call", [
    lambda: A.regression(REF, "score", ["method"]),                 # 문자형 X
    lambda: A.regression(REF.head(2), "score", ["study_time"]),     # 표본 부족
    lambda: A.one_way_anova(REF.assign(g="한집단"), "score", "g"),   # 집단 1개
    lambda: A.mediation(REF, "med_x", "med_x", "med_y"),            # 같은 변수 중복
    lambda: A.regression(REF.assign(c=1), "score", ["c"]),          # 상수 변수
])
def test_friendly_errors(call):
    with pytest.raises(A.AnalysisError):
        call()
