"""추가 분석(정규성·상관·t검정·교차분석·신뢰도·APA·결측 대체) 검증.

scipy / pandas 의 독립 계산 결과와 앱 계산값을 비교합니다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import analysis as A

REF = pd.read_excel(ROOT / "data" / "reference_data.xlsx")
SURVEY = pd.read_excel(ROOT / "data" / "survey_sample.xlsx")
ITEMS = ["만족1", "만족2", "만족3", "만족4", "만족5"]


def test_normality_matches_scipy():
    t = A.normality(REF, ["score"])["table"].iloc[0]
    w, p = stats.shapiro(REF["score"])
    assert np.isclose(t["Shapiro-Wilk W"], w) and np.isclose(t["p"], p)


def test_correlation_matches_pandas():
    cols = ["score", "pre_score", "post_score", "study_time"]
    r = A.correlation(REF, cols)["r"].to_numpy()
    assert np.allclose(r, REF[cols].corr().to_numpy())
    rs = A.correlation(REF, cols, "spearman")["r"].to_numpy()
    assert np.allclose(rs, REF[cols].corr(method="spearman").to_numpy())


def test_independent_t_matches_scipy_and_cohen_d():
    res = A.t_test_independent(REF, "anova_score", "method", ["A", "C"])
    a = REF.loc[REF.method == "A", "anova_score"]
    c = REF.loc[REF.method == "C", "anova_score"]
    assert np.isclose(res["table"]["t"][0], stats.ttest_ind(a, c).statistic)
    assert np.isclose(res["table"]["t"][1], stats.ttest_ind(a, c, equal_var=False).statistic)
    sp = np.sqrt(((len(a) - 1) * a.var() + (len(c) - 1) * c.var()) / (len(a) + len(c) - 2))
    assert np.isclose(res["d"], (a.mean() - c.mean()) / sp)


def test_paired_and_one_sample_t():
    p = A.t_test_paired(REF, "pre_score", "post_score")
    assert np.isclose(p["table"]["t"][0], stats.ttest_rel(REF.post_score, REF.pre_score).statistic)
    o = A.t_test_one_sample(REF, "score", 75)
    assert np.isclose(o["table"]["t"][0], stats.ttest_1samp(REF.score, 75).statistic)


def test_chi_square_and_cramers_v():
    res = A.chi_square(SURVEY, "프로그램", "재참여의사")
    tab = pd.crosstab(SURVEY["프로그램"], SURVEY["재참여의사"])
    chi2, p, dof, _ = stats.chi2_contingency(tab, correction=False)
    assert np.isclose(res["chi2"], chi2) and np.isclose(res["p"], p) and res["df"] == dof
    assert np.isclose(res["cramers_v"], np.sqrt(chi2 / tab.to_numpy().sum()))
    assert res["fisher_p"] is not None  # 2x2 이면 Fisher 정확검정 제공


def test_cronbach_alpha_and_reverse_item():
    raw = A.cronbach_alpha(SURVEY, ITEMS)
    assert raw["negative"] == ["만족4"]  # 역문항 감지
    rev = A.reverse_items(SURVEY, ["만족4"], 1, 5)
    res = A.cronbach_alpha(rev, ITEMS)
    X = rev[ITEMS].dropna().to_numpy(float)
    C = np.cov(X, rowvar=False)
    k = len(ITEMS)
    assert np.isclose(res["alpha"], k / (k - 1) * (1 - np.trace(C) / C.sum()))  # 공분산 행렬 공식
    assert res["alpha"] > 0.8 and not res["negative"]


def test_apa_formatting():
    assert A.apa_p(0.0004) == "< .001"
    assert A.apa_p(0.027) == ".027"
    assert A.apa_num(0.456, 2, False) == ".46"
    assert A.apa_num(-0.456, 2, False) == "-.46"
    s = A.apa_regression(A.regression(REF, "score", ["study_time"]))
    assert s.startswith("R² = .033") and "F(1, 34)" in s


def test_mean_imputation():
    out, filled = A.impute_mean(SURVEY, ["사후점수", "주당학습시간"])
    assert filled == {"사후점수": 2, "주당학습시간": 1}
    assert out["사후점수"].isna().sum() == 0
    assert np.isclose(out["사후점수"].mean(), SURVEY["사후점수"].mean())


@pytest.mark.parametrize("call", [
    lambda: A.correlation(REF, ["score"]),                                   # 변수 1개
    lambda: A.t_test_independent(REF, "score", "method"),                    # 집단 3개인데 두 집단 미지정
    lambda: A.t_test_paired(REF, "score", "score"),                          # 같은 변수
    lambda: A.chi_square(REF.assign(k="하나"), "method", "k"),                # 범주 1개
    lambda: A.cronbach_alpha(SURVEY, ["만족1"]),                              # 문항 1개
    lambda: A.cronbach_alpha(SURVEY.assign(c=3), ["만족1", "c"]),             # 모든 응답이 같은 문항
])
def test_extra_friendly_errors(call):
    with pytest.raises(A.AnalysisError):
        call()
