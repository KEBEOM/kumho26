"""통계 계산 모듈.

화면(app.py)과 계산(analysis.py)을 분리했습니다.
모든 계산은 numpy / pandas / scipy 만 사용합니다 (설치 실패 가능성을 줄이기 위해).
문제가 생기면 AnalysisError 에 쉬운 한국어 안내를 담아 올려 보냅니다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

MIN_N_PER_PARAM = 2  # 추정할 계수 1개당 최소 몇 행이 더 필요할지(여유분)


class AnalysisError(Exception):
    """사용자에게 그대로 보여 줄 한국어 오류."""


# ---------------------------------------------------------------------------
# 공통 도우미
# ---------------------------------------------------------------------------
def numeric_columns(df: pd.DataFrame, min_ratio: float = 0.8) -> list[str]:
    """숫자로 바꿀 수 있는 값이 min_ratio 이상인 열 목록."""
    cols = []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_bool_dtype(s):
            continue
        conv = pd.to_numeric(s, errors="coerce")
        nonmissing = s.notna().sum()
        if nonmissing and conv.notna().sum() / nonmissing >= min_ratio:
            cols.append(c)
    return cols


def categorical_columns(df: pd.DataFrame, max_levels: int = 20) -> list[str]:
    """집단변수로 쓸 수 있는 열(수준 2~max_levels 개).

    이름·ID처럼 행마다 값이 다른 열은 제외하고, 문자형 열을 앞에 둡니다.
    """
    text, num = [], []
    for c in df.columns:
        s = df[c].dropna()
        k = s.nunique()
        if not (2 <= k <= max_levels) or k > max(2, len(s) / 2):
            continue
        (num if pd.api.types.is_numeric_dtype(s) else text).append(c)
    return text + num


def _check_distinct(names: list[str]):
    if len(set(names)) != len(names):
        raise AnalysisError("같은 변수를 두 역할에 동시에 선택했습니다. 서로 다른 변수를 고르세요.")


def _numeric_frame(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, int]:
    """선택한 열을 숫자로 바꾸고 결측 행을 제외. (데이터, 제외된 행 수) 반환."""
    for c in cols:
        if c not in df.columns:
            raise AnalysisError(f"'{c}' 열을 찾을 수 없습니다.")
    raw = df[cols]
    out = raw.apply(pd.to_numeric, errors="coerce")
    for c in cols:
        bad = raw[c].notna() & out[c].isna()
        if bad.sum() > 0 and bad.sum() >= raw[c].notna().sum() * 0.2:
            raise AnalysisError(
                f"'{c}' 열에 숫자가 아닌 값(예: '{raw[c][bad].iloc[0]}')이 많습니다. "
                "숫자형 변수를 선택하거나 엑셀에서 값을 고치세요."
            )
    before = len(out)
    out = out.dropna()
    return out, before - len(out)


def _p_fmt(p: float) -> str:
    return "< .001" if p < 0.001 else f"{p:.3f}"


def p_text(p: float) -> str:
    """문장용 p값 표기: 'p < .001' 또는 'p = 0.123'."""
    return "p < .001" if p < 0.001 else f"p = {p:.3f}"


# ---------------------------------------------------------------------------
# 1. 기초통계
# ---------------------------------------------------------------------------
def descriptive_statistics(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for col in columns:
        s = pd.to_numeric(df[col], errors="coerce")
        q1, q3 = s.quantile(.25), s.quantile(.75)
        rows.append({
            "변수": col,
            "사용 사례 수(n)": int(s.notna().sum()),
            "결측 수": int(s.isna().sum()),
            "평균": s.mean(),
            "표준편차": s.std(),
            "중앙값": s.median(),
            "최소값": s.min(),
            "최대값": s.max(),
            "Q1": q1,
            "Q3": q3,
            "사분위범위(IQR)": q3 - q1,
            "왜도": s.skew(),
        })
    return pd.DataFrame(rows)


def frequency_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    s = df[col]
    counts = s.value_counts(dropna=False)
    counts = counts.iloc[sorted(range(len(counts)), key=lambda i: str(counts.index[i]))]
    out = pd.DataFrame({
        "값": ["(결측)" if pd.isna(v) else v for v in counts.index],
        "빈도": counts.values,
    })
    out["비율(%)"] = out["빈도"] / out["빈도"].sum() * 100
    return out


# ---------------------------------------------------------------------------
# 2·3. 회귀분석 (최소제곱법)
# ---------------------------------------------------------------------------
def _ols_core(y: np.ndarray, X: np.ndarray):
    """X 는 절편 열 포함. 계수, 공분산, 잔차, df_resid 반환."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    fitted = X @ beta
    resid = y - fitted
    df_resid = n - k
    sse = float(resid @ resid)
    sigma2 = sse / df_resid
    cov = sigma2 * XtX_inv
    return beta, cov, fitted, resid, df_resid, sse


def vif_table(X: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = list(X.columns)
    for c in cols:
        others = [o for o in cols if o != c]
        if not others:
            rows.append({"변수": c, "VIF": 1.0})
            continue
        y = X[c].to_numpy(float)
        Z = np.column_stack([np.ones(len(X)), X[others].to_numpy(float)])
        _, _, _, resid, _, sse = _ols_core(y, Z)
        sst = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - sse / sst if sst > 0 else 1.0
        rows.append({"변수": c, "VIF": np.inf if r2 >= 1 else 1 / (1 - r2)})
    return pd.DataFrame(rows)


def regression(df: pd.DataFrame, y: str, xs: list[str], interaction: tuple[str, str] | None = None) -> dict:
    """OLS 회귀. interaction=(x, w) 를 주면 x*w 항을 추가."""
    if not y or not xs:
        raise AnalysisError("종속변수(Y) 1개와 독립변수(X) 1개 이상을 선택하세요.")
    _check_distinct([y] + list(xs))
    data, dropped = _numeric_frame(df, [y] + list(xs))
    X = data[list(xs)].copy()
    if interaction:
        a, b = interaction
        X[f"{a}×{b}"] = data[a] * data[b]
    k = X.shape[1] + 1
    n = len(data)
    if n < k + MIN_N_PER_PARAM:
        raise AnalysisError(
            f"표본이 너무 적습니다. 결측을 뺀 사례가 {n}개인데, 이 모형에는 최소 {k + MIN_N_PER_PARAM}개가 필요합니다."
        )
    for c in X.columns:
        if X[c].std() == 0:
            raise AnalysisError(f"'{c}' 값이 모두 같아서 회귀분석을 할 수 없습니다.")
    yv = data[y].to_numpy(float)
    if yv.std() == 0:
        raise AnalysisError(f"종속변수 '{y}' 값이 모두 같아서 분석할 수 없습니다.")
    Xm = np.column_stack([np.ones(n), X.to_numpy(float)])
    if np.linalg.matrix_rank(Xm) < Xm.shape[1]:
        raise AnalysisError("독립변수끼리 완전히 겹칩니다(완전 다중공선성). 겹치는 변수를 빼세요.")

    beta, cov, fitted, resid, df_resid, sse = _ols_core(yv, Xm)
    se = np.sqrt(np.diag(cov))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), df_resid)
    tcrit = stats.t.ppf(0.975, df_resid)
    sst = float(((yv - yv.mean()) ** 2).sum())
    r2 = 1 - sse / sst
    p_x = k - 1
    adj = 1 - (1 - r2) * (n - 1) / df_resid
    f = (r2 / p_x) / ((1 - r2) / df_resid)
    f_p = stats.f.sf(f, p_x, df_resid)

    sd_x = np.r_[np.nan, X.std(ddof=1).to_numpy()]
    std_beta = beta * sd_x / yv.std(ddof=1)
    names = ["(절편)"] + list(X.columns)
    coef = pd.DataFrame({
        "변수": names,
        "B": beta,
        "SE": se,
        "β(표준화)": std_beta,
        "t": t,
        "p": p,
        "95% CI 하한": beta - tcrit * se,
        "95% CI 상한": beta + tcrit * se,
    })
    return {
        "n": n, "dropped": dropped, "r2": r2, "adj_r2": adj,
        "F": f, "df1": p_x, "df2": df_resid, "F_p": f_p,
        "coef": coef, "fitted": fitted, "resid": resid,
        "vif": vif_table(X) if X.shape[1] > 1 else None,
        "y": y, "xs": list(X.columns), "cov": cov, "data": data,
    }


def regression_sentence(res: dict) -> str:
    c = res["coef"].iloc[1:]
    parts = []
    for _, r in c.iterrows():
        sig = "통계적으로 유의했다" if r["p"] < 0.05 else "통계적으로 유의하지 않았다"
        direction = "증가" if r["B"] > 0 else "감소"
        parts.append(
            f"'{r['변수']}'가 1 증가할 때 '{res['y']}'는 평균 {abs(r['B']):.3f} {direction}하는 관계가 있었으며 "
            f"이는 {sig}(B={r['B']:.3f}, {p_text(r['p'])})."
        )
    head = (f"모형은 '{res['y']}' 분산의 {res['r2']*100:.1f}%를 설명했다"
            f"(R²={res['r2']:.3f}, F({res['df1']}, {res['df2']})={res['F']:.2f}, {p_text(res['F_p'])}). ")
    return head + " ".join(parts) + " 회귀계수는 관계의 크기를 뜻하며, 그 자체로 원인-결과를 증명하지는 않는다."


# ---------------------------------------------------------------------------
# 4. 일원분산분석
# ---------------------------------------------------------------------------
def _prep_groups(df, y, factors):
    _check_distinct([y] + list(factors))
    for f in factors:
        if f not in df.columns:
            raise AnalysisError(f"'{f}' 열을 찾을 수 없습니다.")
    yv = pd.to_numeric(df[y], errors="coerce")
    bad = df[y].notna() & yv.isna()
    if bad.sum() >= max(1, df[y].notna().sum() * 0.2):
        raise AnalysisError(f"종속변수 '{y}'에 숫자가 아닌 값이 많습니다. 숫자형 변수를 선택하세요.")
    data = pd.DataFrame({y: yv})
    for f in factors:
        data[f] = df[f].astype("string")
    before = len(data)
    data = data.dropna()
    return data, before - len(data)


def one_way_anova(df: pd.DataFrame, y: str, group: str) -> dict:
    data, dropped = _prep_groups(df, y, [group])
    levels = sorted(data[group].unique())
    if len(levels) < 2:
        raise AnalysisError(f"집단변수 '{group}'에 집단이 {len(levels)}개뿐입니다. 집단이 2개 이상이어야 합니다.")
    groups = [data.loc[data[group] == lv, y].to_numpy(float) for lv in levels]
    small = [str(lv) for lv, g in zip(levels, groups) if len(g) < 2]
    if small:
        raise AnalysisError(f"사례가 2개 미만인 집단이 있습니다: {', '.join(small)}. 집단별로 2개 이상 필요합니다.")
    n = len(data)
    k = len(levels)
    if n - k < 1:
        raise AnalysisError("표본이 너무 적어 분산분석을 할 수 없습니다.")
    grand = data[y].mean()
    ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    if ssw == 0:
        raise AnalysisError("집단 안의 값이 모두 같아(집단 내 변동 0) F를 계산할 수 없습니다.")
    dfb, dfw = k - 1, n - k
    msb, msw = ssb / dfb, ssw / dfw
    F = msb / msw
    p = stats.f.sf(F, dfb, dfw)
    sst = ssb + ssw
    eta2 = ssb / sst
    omega2 = (ssb - dfb * msw) / (sst + msw)

    desc = pd.DataFrame({
        "집단": levels,
        "n": [len(g) for g in groups],
        "평균": [g.mean() for g in groups],
        "표준편차": [g.std(ddof=1) for g in groups],
    })
    table = pd.DataFrame({
        "변동원": ["집단 간", "집단 내(오차)", "전체"],
        "SS": [ssb, ssw, sst],
        "df": [dfb, dfw, n - 1],
        "MS": [msb, msw, np.nan],
        "F": [F, np.nan, np.nan],
        "p": [p, np.nan, np.nan],
    })
    lev = stats.levene(*groups, center="median")

    # 사후검정: Tukey HSD
    tk = stats.tukey_hsd(*groups)
    rows = []
    for i in range(k):
        for j in range(i + 1, k):
            ci = tk.confidence_interval(0.95)
            rows.append({
                "비교": f"{levels[i]} - {levels[j]}",
                "평균차": groups[i].mean() - groups[j].mean(),
                "p(Tukey)": tk.pvalue[i, j],
                "95% CI 하한": ci.low[i, j],
                "95% CI 상한": ci.high[i, j],
            })
    return {
        "n": n, "dropped": dropped, "F": F, "df1": dfb, "df2": dfw, "p": p,
        "eta2": eta2, "omega2": omega2, "desc": desc, "table": table,
        "levene_W": lev.statistic, "levene_p": lev.pvalue,
        "posthoc": pd.DataFrame(rows), "y": y, "group": group,
    }


# ---------------------------------------------------------------------------
# 5. 이원분산분석 (Type III 제곱합, 효과 코딩)
# ---------------------------------------------------------------------------
def _effect_code(s: pd.Series, levels: list) -> np.ndarray:
    """합-0 코딩(마지막 수준이 기준)."""
    cols = []
    for lv in levels[:-1]:
        cols.append(np.where(s == lv, 1.0, np.where(s == levels[-1], -1.0, 0.0)))
    return np.column_stack(cols)


def _sse(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(r @ r)


def two_way_anova(df: pd.DataFrame, y: str, a: str, b: str) -> dict:
    data, dropped = _prep_groups(df, y, [a, b])
    la, lb = sorted(data[a].unique()), sorted(data[b].unique())
    if len(la) < 2 or len(lb) < 2:
        raise AnalysisError("두 요인 모두 집단이 2개 이상이어야 합니다.")
    cell = data.groupby([a, b])[y].size()
    if len(cell) < len(la) * len(lb):
        raise AnalysisError("비어 있는 칸(요인 조합)이 있습니다. 모든 조합에 사례가 있어야 상호작용을 계산할 수 있습니다.")
    if (cell < 2).any():
        raise AnalysisError("사례가 2개 미만인 칸이 있습니다. 칸마다 2개 이상 필요합니다.")
    yv = data[y].to_numpy(float)
    n = len(yv)
    A = _effect_code(data[a].to_numpy(), la)
    B = _effect_code(data[b].to_numpy(), lb)
    AB = np.column_stack([A[:, i] * B[:, j] for i in range(A.shape[1]) for j in range(B.shape[1])])
    one = np.ones((n, 1))
    full = np.hstack([one, A, B, AB])
    sse_full = _sse(yv, full)
    df_err = n - full.shape[1]
    if df_err < 1:
        raise AnalysisError("표본이 너무 적어 이원분산분석을 할 수 없습니다.")
    mse = sse_full / df_err
    if mse == 0:
        raise AnalysisError("칸 안의 값이 모두 같아 F를 계산할 수 없습니다.")
    terms = {
        a: (np.hstack([one, B, AB]), A.shape[1]),
        b: (np.hstack([one, A, AB]), B.shape[1]),
        f"{a}×{b}": (np.hstack([one, A, B]), AB.shape[1]),
    }
    rows = []
    for name, (Xr, dfe) in terms.items():
        ss = _sse(yv, Xr) - sse_full
        F = (ss / dfe) / mse
        rows.append({
            "변동원": name, "SS(Type III)": ss, "df": dfe, "MS": ss / dfe, "F": F,
            "p": stats.f.sf(F, dfe, df_err), "부분 η²": ss / (ss + sse_full),
        })
    rows.append({"변동원": "오차", "SS(Type III)": sse_full, "df": df_err, "MS": mse,
                 "F": np.nan, "p": np.nan, "부분 η²": np.nan})
    table = pd.DataFrame(rows)
    means = data.groupby([a, b])[y].mean().unstack(b)
    marg_a = data.groupby(a)[y].agg(["count", "mean", "std"]).rename(columns={"count": "n", "mean": "평균", "std": "표준편차"})
    marg_b = data.groupby(b)[y].agg(["count", "mean", "std"]).rename(columns={"count": "n", "mean": "평균", "std": "표준편차"})
    return {
        "n": n, "dropped": dropped, "table": table, "cell_means": means,
        "marg_a": marg_a, "marg_b": marg_b, "balanced": cell.nunique() == 1,
        "interaction_p": rows[2]["p"], "y": y, "a": a, "b": b,
    }


# ---------------------------------------------------------------------------
# 6. 단순 매개효과 (X → M → Y)
# ---------------------------------------------------------------------------
def mediation(df: pd.DataFrame, x: str, m: str, y: str, n_boot: int = 5000, seed: int = 2026) -> dict:
    _check_distinct([x, m, y])
    data, dropped = _numeric_frame(df, [x, m, y])
    n = len(data)
    if n < 10:
        raise AnalysisError(f"매개분석에는 사례가 최소 10개 필요합니다. 현재 {n}개입니다.")
    path_c = regression(data, y, [x])
    path_a = regression(data, m, [x])
    path_b = regression(data, y, [x, m])
    a_ = path_a["coef"].iloc[1]
    c_ = path_c["coef"].iloc[1]
    cp_ = path_b["coef"].iloc[1]
    b_ = path_b["coef"].iloc[2]
    ab = a_["B"] * b_["B"]
    sobel_se = np.sqrt(b_["B"] ** 2 * a_["SE"] ** 2 + a_["B"] ** 2 * b_["SE"] ** 2)
    sobel_z = ab / sobel_se
    sobel_p = 2 * stats.norm.sf(abs(sobel_z))

    # 부트스트랩 (percentile)
    rng = np.random.default_rng(seed)
    X, M, Y = (data[c].to_numpy(float) for c in (x, m, y))
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = np.empty(n_boot)
    for i in range(n_boot):
        xi, mi, yi = X[idx[i]], M[idx[i]], Y[idx[i]]
        Xa = np.column_stack([np.ones(n), xi])
        a_b = np.linalg.lstsq(Xa, mi, rcond=None)[0][1]
        Xb = np.column_stack([np.ones(n), xi, mi])
        b_b = np.linalg.lstsq(Xb, yi, rcond=None)[0][2]
        boots[i] = a_b * b_b
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])

    def row(label, r):
        return {"경로": label, "B": r["B"], "SE": r["SE"], "t": r["t"], "p": r["p"]}

    paths = pd.DataFrame([
        row(f"a: {x} → {m}", a_),
        row(f"b: {m} → {y} ({x} 통제)", b_),
        row(f"c: {x} → {y} (총효과)", c_),
        row(f"c': {x} → {y} (직접효과)", cp_),
    ])
    return {
        "n": n, "dropped": dropped, "a": a_["B"], "b": b_["B"], "c": c_["B"], "c_prime": cp_["B"],
        "ab": ab, "sobel_z": sobel_z, "sobel_p": sobel_p, "boot_ci": (lo, hi), "n_boot": n_boot,
        "paths": paths, "prop_mediated": ab / c_["B"] if c_["B"] != 0 else np.nan,
        "x": x, "m": m, "y": y,
    }


def mediation_sentence(r: dict) -> str:
    lo, hi = r["boot_ci"]
    sig = (lo > 0 or hi < 0)
    s = (f"'{r['x']}'가 '{r['m']}'를 거쳐 '{r['y']}'와 연결되는 간접효과는 ab={r['ab']:.3f}이고, "
         f"부트스트랩 95% 신뢰구간은 [{lo:.3f}, {hi:.3f}]로 0을 {'포함하지 않아' if sig else '포함하여'} "
         f"간접효과가 {'통계적으로 유의했다' if sig else '유의하다고 보기 어렵다'}. ")
    s += "이 결과는 변수들 사이의 통계적 경로 관계를 보여 줄 뿐이며, 단면 자료로 인과관계를 확정할 수는 없다."
    return s


# ---------------------------------------------------------------------------
# 7. 조절효과 (Y ~ X + W + X×W)
# ---------------------------------------------------------------------------
def moderation(df: pd.DataFrame, x: str, w: str, y: str, center: bool = False) -> dict:
    _check_distinct([x, w, y])
    data, dropped = _numeric_frame(df, [x, w, y])
    if center:
        data[x] = data[x] - data[x].mean()
        data[w] = data[w] - data[w].mean()
    res = regression(data, y, [x, w], interaction=(x, w))
    beta = res["coef"]["B"].to_numpy()
    cov = res["cov"]
    w_mean, w_sd = data[w].mean(), data[w].std(ddof=1)
    rows = []
    for label, wv in [("W 낮음(평균-1SD)", w_mean - w_sd), ("W 평균", w_mean), ("W 높음(평균+1SD)", w_mean + w_sd)]:
        slope = beta[1] + beta[3] * wv
        var = cov[1, 1] + wv ** 2 * cov[3, 3] + 2 * wv * cov[1, 3]
        se = np.sqrt(var)
        t = slope / se
        rows.append({"W 수준": label, "W 값": wv, "단순기울기": slope, "SE": se, "t": t,
                     "p": 2 * stats.t.sf(abs(t), res["df2"])})
    # R² 증가량 (상호작용 추가 전후)
    base = regression(data, y, [x, w])
    res.update({
        "simple_slopes": pd.DataFrame(rows), "delta_r2": res["r2"] - base["r2"],
        "x": x, "w": w, "centered": center,
        "int_row": res["coef"].iloc[3], "w_levels": [w_mean - w_sd, w_mean, w_mean + w_sd],
    })
    return res


def reference_check(df: pd.DataFrame) -> pd.DataFrame:
    """교수자 기준데이터(기준결과_검산표.md)와 앱 계산값 비교표."""
    ref = [
        ("1 기초통계", "score 평균", 76.000, lambda: descriptive_statistics(df, ["score"]).iloc[0]["평균"]),
        ("1 기초통계", "score 표준편차", 8.135, lambda: descriptive_statistics(df, ["score"]).iloc[0]["표준편차"]),
        ("1 기초통계", "score 중앙값", 76.000, lambda: descriptive_statistics(df, ["score"]).iloc[0]["중앙값"]),
        ("2 단순회귀", "R²", 0.0330, lambda: regression(df, "score", ["study_time"])["r2"]),
        ("2 단순회귀", "절편", 72.4268, lambda: regression(df, "score", ["study_time"])["coef"]["B"][0]),
        ("2 단순회귀", "study_time B", 1.1089, lambda: regression(df, "score", ["study_time"])["coef"]["B"][1]),
        ("2 단순회귀", "study_time p", 0.288707, lambda: regression(df, "score", ["study_time"])["coef"]["p"][1]),
        ("3 다중회귀", "R²", 0.9349, lambda: regression(df, "score", ["study_time", "pre_score"])["r2"]),
        ("3 다중회귀", "수정 R²", 0.9310, lambda: regression(df, "score", ["study_time", "pre_score"])["adj_r2"]),
        ("3 다중회귀", "study_time B", 0.0729, lambda: regression(df, "score", ["study_time", "pre_score"])["coef"]["B"][1]),
        ("3 다중회귀", "study_time p", 0.792724, lambda: regression(df, "score", ["study_time", "pre_score"])["coef"]["p"][1]),
        ("3 다중회귀", "pre_score B", 0.8912, lambda: regression(df, "score", ["study_time", "pre_score"])["coef"]["B"][2]),
        ("4 일원분산", "F", 14.0291, lambda: one_way_anova(df, "anova_score", "method")["F"]),
        ("4 일원분산", "p", 0.000039, lambda: one_way_anova(df, "anova_score", "method")["p"]),
        ("4 일원분산", "A 평균", 55.166, lambda: one_way_anova(df, "anova_score", "method")["desc"]["평균"][0]),
        ("4 일원분산", "B 평균", 58.193, lambda: one_way_anova(df, "anova_score", "method")["desc"]["평균"][1]),
        ("4 일원분산", "C 평균", 62.407, lambda: one_way_anova(df, "anova_score", "method")["desc"]["평균"][2]),
        ("5 이원분산", "method F", 266.3419, lambda: two_way_anova(df, "anova_score", "method", "grade")["table"]["F"][0]),
        ("5 이원분산", "grade F", 283.2311, lambda: two_way_anova(df, "anova_score", "method", "grade")["table"]["F"][1]),
        ("5 이원분산", "상호작용 F", 8.2607, lambda: two_way_anova(df, "anova_score", "method", "grade")["table"]["F"][2]),
        ("5 이원분산", "상호작용 p", 0.000174, lambda: two_way_anova(df, "anova_score", "method", "grade")["table"]["p"][2]),
        ("6 매개", "a", 0.8027, lambda: mediation(df, "med_x", "med_m", "med_y", n_boot=200)["a"]),
        ("6 매개", "b", 1.5300, lambda: mediation(df, "med_x", "med_m", "med_y", n_boot=200)["b"]),
        ("6 매개", "c'", 0.1383, lambda: mediation(df, "med_x", "med_m", "med_y", n_boot=200)["c_prime"]),
        ("6 매개", "간접효과 ab", 1.2282, lambda: mediation(df, "med_x", "med_m", "med_y", n_boot=200)["ab"]),
        ("7 조절", "상호작용 B", 0.6786, lambda: moderation(df, "mod_x", "mod_w", "mod_y")["int_row"]["B"]),
        ("7 조절", "R²", 0.9743, lambda: moderation(df, "mod_x", "mod_w", "mod_y")["r2"]),
    ]
    rows = []
    for week, item, expected, fn in ref:
        try:
            got = float(fn())
            decimals = max(3, len(f"{expected}".split(".")[-1]))
            tol = 1.5 * 10 ** (-decimals) if expected >= 1e-3 or expected == 0 else 5e-6
            ok = abs(got - expected) <= max(tol, abs(expected) * 1e-4)
            rows.append({"주차": week, "항목": item, "기준값": expected, "앱 결과": got,
                         "차이": got - expected, "판정": "일치" if ok else "불일치"})
        except Exception as e:  # 열 이름이 다른 파일이면 여기로 옴
            rows.append({"주차": week, "항목": item, "기준값": expected, "앱 결과": np.nan,
                         "차이": np.nan, "판정": f"계산 불가({e})"})
    return pd.DataFrame(rows)


REFERENCE_COLUMNS = {"score", "study_time", "pre_score", "method", "grade", "anova_score",
                     "med_x", "med_m", "med_y", "mod_x", "mod_w", "mod_y"}


def moderation_sentence(r: dict) -> str:
    ir = r["int_row"]
    sig = ir["p"] < 0.05
    s = (f"상호작용항 '{ir['변수']}'의 계수는 B={ir['B']:.3f}({p_text(ir['p'])})로 "
         f"{'유의하여' if sig else '유의하지 않아'}, '{r['w']}' 수준에 따라 '{r['x']}'와 '{r['y']}'의 관계 크기가 "
         f"{'달라지는 것으로 나타났다' if sig else '달라진다고 보기 어렵다'}"
         f"(상호작용 추가로 R² {r['delta_r2']:.3f} 증가). ")
    s += "조절효과는 관계의 조건을 보여 주는 통계적 결과이며 인과관계를 단정하지 않는다."
    return s


# ===========================================================================
# 추가 분석: 정규성 · 상관 · t검정 · 교차분석 · 신뢰도
# ===========================================================================
def apa_p(p: float) -> str:
    """APA 표기: p < .001 / p = .027 (앞의 0 생략)."""
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ""
    return "< .001" if p < 0.001 else f"{p:.3f}".lstrip("0") if p < 1 else "1.000"


def apa_num(x: float, digits: int = 2, leading_zero: bool = True) -> str:
    s = f"{x:.{digits}f}"
    if not leading_zero:
        s = s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)
    return s


def _apa_p_eq(p):
    v = apa_p(p)
    return f"p {v}" if v.startswith("<") else f"p = {v}"


# ---------------------------------------------------------------------------
# 정규성 검정
# ---------------------------------------------------------------------------
def normality(df: pd.DataFrame, columns: list[str]) -> dict:
    if not columns:
        raise AnalysisError("정규성을 확인할 숫자형 변수를 1개 이상 고르세요.")
    rows, qq = [], {}
    for c in columns:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        n = len(s)
        row = {"변수": c, "n": n, "평균": s.mean(), "표준편차": s.std(), "왜도": s.skew(), "첨도": s.kurt(),
               "Shapiro-Wilk W": np.nan, "p": np.nan, "판정": ""}
        if n < 3:
            row["판정"] = "사례 3개 미만: 검정 불가"
        elif s.nunique() == 1:
            row["판정"] = "값이 모두 같음: 검정 불가"
        else:
            w, p = stats.shapiro(s.to_numpy(float)[:5000])
            row.update({"Shapiro-Wilk W": w, "p": p,
                        "판정": "정규분포 가정 가능" if p >= 0.05 else "정규분포에서 벗어남"})
            (osm, osr), (slope, inter, r) = stats.probplot(s.to_numpy(float), dist="norm")
            qq[c] = pd.DataFrame({"이론 분위수": osm, "관측값": osr, "기준선": inter + slope * osm})
        rows.append(row)
    return {"table": pd.DataFrame(rows), "qq": qq}


# ---------------------------------------------------------------------------
# 상관분석
# ---------------------------------------------------------------------------
def correlation(df: pd.DataFrame, columns: list[str], method: str = "pearson") -> dict:
    if len(columns) < 2:
        raise AnalysisError("상관분석에는 숫자형 변수가 2개 이상 필요합니다.")
    _check_distinct(list(columns))
    data = df[list(columns)].apply(pd.to_numeric, errors="coerce")
    k = len(columns)
    r = np.eye(k)
    p = np.zeros((k, k))
    n = np.zeros((k, k), dtype=int)
    func = stats.pearsonr if method == "pearson" else stats.spearmanr
    long = []
    for i in range(k):
        n[i, i] = data.iloc[:, i].notna().sum()
        for j in range(i + 1, k):
            pair = data.iloc[:, [i, j]].dropna()
            n[i, j] = n[j, i] = len(pair)
            if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
                r[i, j] = r[j, i] = np.nan
                p[i, j] = p[j, i] = np.nan
            else:
                res = func(pair.iloc[:, 0], pair.iloc[:, 1])
                r[i, j] = r[j, i] = float(res[0])
                p[i, j] = p[j, i] = float(res[1])
            long.append({"변수1": columns[i], "변수2": columns[j], "r": r[i, j], "p": p[i, j], "n": n[i, j]})
    names = list(columns)
    rdf = pd.DataFrame(r, index=names, columns=names)
    pdf = pd.DataFrame(p, index=names, columns=names)
    # 별표 표시 행렬 (APA 상관표처럼 아래 삼각형만)
    star = pd.DataFrame("", index=names, columns=names)
    for i in range(k):
        for j in range(k):
            if i == j:
                star.iloc[i, j] = "—"
            elif j < i:
                v, pv = r[i, j], p[i, j]
                mark = "***" if pv < .001 else "**" if pv < .01 else "*" if pv < .05 else ""
                star.iloc[i, j] = "" if np.isnan(v) else apa_num(v, 2, False) + mark
    return {"r": rdf, "p": pdf, "n": pd.DataFrame(n, index=names, columns=names),
            "pairs": pd.DataFrame(long), "star": star, "method": method}


def correlation_sentence(res: dict) -> str:
    pairs = res["pairs"].dropna(subset=["r"])
    if pairs.empty:
        return "계산 가능한 상관계수가 없습니다."
    top = pairs.reindex(pairs["r"].abs().sort_values(ascending=False).index).iloc[0]
    sym = "r" if res["method"] == "pearson" else "rₛ"
    strength = "강한" if abs(top["r"]) >= .5 else "중간 정도의" if abs(top["r"]) >= .3 else "약한"
    sign = "정(+)적" if top["r"] > 0 else "부(-)적"
    sig = pairs[pairs["p"] < .05]
    return (f"유의한 상관은 {len(sig)}쌍/{len(pairs)}쌍이었다. 가장 큰 상관은 '{top['변수1']}'와 '{top['변수2']}' 사이의 "
            f"{strength} {sign} 상관이었다({sym}({int(top['n']) - 2}) = {apa_num(top['r'], 2, False)}, {_apa_p_eq(top['p'])}). "
            "상관은 함께 변하는 정도일 뿐 인과관계를 뜻하지 않는다.")


# ---------------------------------------------------------------------------
# t검정
# ---------------------------------------------------------------------------
def _cohen_label(d):
    d = abs(d)
    return "큰" if d >= .8 else "중간" if d >= .5 else "작은" if d >= .2 else "매우 작은"


def t_test_independent(df: pd.DataFrame, y: str, group: str, levels: list | None = None) -> dict:
    data, dropped = _prep_groups(df, y, [group])
    all_levels = sorted(data[group].unique())
    if levels is None:
        if len(all_levels) != 2:
            raise AnalysisError(f"'{group}'의 집단이 {len(all_levels)}개입니다. 비교할 두 집단을 고르세요.")
        levels = all_levels
    levels = [str(l) for l in levels]
    if len(levels) != 2 or levels[0] == levels[1]:
        raise AnalysisError("서로 다른 두 집단을 골라야 합니다.")
    g1 = data.loc[data[group] == levels[0], y].to_numpy(float)
    g2 = data.loc[data[group] == levels[1], y].to_numpy(float)
    if len(g1) < 2 or len(g2) < 2:
        raise AnalysisError("각 집단에 사례가 2개 이상 있어야 합니다.")
    if np.var(g1) == 0 and np.var(g2) == 0:
        raise AnalysisError("두 집단 모두 값이 하나뿐이라 t검정을 할 수 없습니다.")
    n1, n2 = len(g1), len(g2)
    m1, m2 = g1.mean(), g2.mean()
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    sp = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    d = (m1 - m2) / sp if sp > 0 else np.nan
    g = d * (1 - 3 / (4 * (n1 + n2) - 9))
    lev = stats.levene(g1, g2, center="median")
    student = stats.ttest_ind(g1, g2, equal_var=True)
    welch = stats.ttest_ind(g1, g2, equal_var=False)
    se_s = sp * np.sqrt(1 / n1 + 1 / n2)
    se_w = np.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
    df_s = n1 + n2 - 2
    df_w = se_w ** 4 / ((s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1))
    diff = m1 - m2
    rows = []
    for name, t, p, dfv, se in [("등분산 가정(Student)", student.statistic, student.pvalue, df_s, se_s),
                                ("등분산 가정 안 함(Welch)", welch.statistic, welch.pvalue, df_w, se_w)]:
        tc = stats.t.ppf(.975, dfv)
        rows.append({"방법": name, "t": t, "df": dfv, "p": p, "평균차": diff,
                     "95% CI 하한": diff - tc * se, "95% CI 상한": diff + tc * se})
    use_welch = lev.pvalue < .05
    desc = pd.DataFrame({"집단": levels, "n": [n1, n2], "평균": [m1, m2], "표준편차": [s1, s2]})
    return {"desc": desc, "table": pd.DataFrame(rows), "levene_F": lev.statistic, "levene_p": lev.pvalue,
            "use_welch": use_welch, "d": d, "g": g, "n": n1 + n2, "dropped": dropped,
            "y": y, "group": group, "levels": levels}


def t_test_paired(df: pd.DataFrame, before: str, after: str) -> dict:
    _check_distinct([before, after])
    data, dropped = _numeric_frame(df, [before, after])
    n = len(data)
    if n < 3:
        raise AnalysisError(f"대응표본 t검정에는 짝지어진 사례가 3개 이상 필요합니다. 현재 {n}개입니다.")
    diff = (data[after] - data[before]).to_numpy(float)
    if diff.std(ddof=1) == 0:
        raise AnalysisError("모든 사례의 차이가 같아서 t검정을 할 수 없습니다.")
    res = stats.ttest_rel(data[after], data[before])
    se = diff.std(ddof=1) / np.sqrt(n)
    tc = stats.t.ppf(.975, n - 1)
    dz = diff.mean() / diff.std(ddof=1)
    desc = pd.DataFrame({"변수": [before, after], "n": [n, n],
                         "평균": [data[before].mean(), data[after].mean()],
                         "표준편차": [data[before].std(), data[after].std()]})
    table = pd.DataFrame([{"비교": f"{after} − {before}", "평균차": diff.mean(), "차이 SD": diff.std(ddof=1),
                           "t": res.statistic, "df": n - 1, "p": res.pvalue,
                           "95% CI 하한": diff.mean() - tc * se, "95% CI 상한": diff.mean() + tc * se}])
    r = stats.pearsonr(data[before], data[after])[0]
    return {"desc": desc, "table": table, "d": dz, "n": n, "dropped": dropped, "r": r,
            "before": before, "after": after}


def t_test_one_sample(df: pd.DataFrame, y: str, mu: float) -> dict:
    data, dropped = _numeric_frame(df, [y])
    s = data[y].to_numpy(float)
    n = len(s)
    if n < 3 or s.std(ddof=1) == 0:
        raise AnalysisError("사례가 3개 이상이고 값이 서로 달라야 일표본 t검정을 할 수 있습니다.")
    res = stats.ttest_1samp(s, mu)
    se = s.std(ddof=1) / np.sqrt(n)
    tc = stats.t.ppf(.975, n - 1)
    d = (s.mean() - mu) / s.std(ddof=1)
    table = pd.DataFrame([{"변수": y, "n": n, "평균": s.mean(), "검정값": mu, "평균차": s.mean() - mu,
                           "t": res.statistic, "df": n - 1, "p": res.pvalue,
                           "95% CI 하한": s.mean() - mu - tc * se, "95% CI 상한": s.mean() - mu + tc * se}])
    return {"table": table, "d": d, "n": n, "dropped": dropped, "y": y, "mu": mu}


def _df_txt(v) -> str:
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.2f}"


def t_sentence(kind: str, r: dict) -> str:
    if kind == "independent":
        row = r["table"].iloc[1 if r["use_welch"] else 0]
        a, b = r["desc"].iloc[0], r["desc"].iloc[1]
        sig = row["p"] < .05
        return (f"'{r['y']}' 평균은 {a['집단']} 집단(M = {a['평균']:.2f}, SD = {a['표준편차']:.2f})과 "
                f"{b['집단']} 집단(M = {b['평균']:.2f}, SD = {b['표준편차']:.2f}) 사이에 "
                f"{'통계적으로 유의한 차이가 있었다' if sig else '유의한 차이가 없었다'}, "
                f"t({_df_txt(row['df'])}) = {row['t']:.2f}, {_apa_p_eq(row['p'])}, d = {r['d']:.2f}({_cohen_label(r['d'])} 효과). "
                + ("Levene 검정에서 등분산 가정이 기각되어 Welch 결과를 보고했다." if r["use_welch"] else ""))
    if kind == "paired":
        row = r["table"].iloc[0]
        a, b = r["desc"].iloc[0], r["desc"].iloc[1]
        return (f"'{r['before']}'(M = {a['평균']:.2f}, SD = {a['표준편차']:.2f})에서 '{r['after']}'(M = {b['평균']:.2f}, "
                f"SD = {b['표준편차']:.2f})로의 변화는 {'통계적으로 유의했다' if row['p'] < .05 else '유의하지 않았다'}, "
                f"t({int(row['df'])}) = {row['t']:.2f}, {_apa_p_eq(row['p'])}, d = {r['d']:.2f}({_cohen_label(r['d'])} 효과). "
                "통제집단이 없으면 변화의 원인을 처치 효과로 단정할 수 없다.")
    row = r["table"].iloc[0]
    return (f"'{r['y']}'의 평균(M = {row['평균']:.2f})은 검정값 {r['mu']:g}와 "
            f"{'통계적으로 유의하게 달랐다' if row['p'] < .05 else '유의하게 다르지 않았다'}, "
            f"t({int(row['df'])}) = {row['t']:.2f}, {_apa_p_eq(row['p'])}, d = {r['d']:.2f}.")


# ---------------------------------------------------------------------------
# 교차분석 (카이제곱)
# ---------------------------------------------------------------------------
def chi_square(df: pd.DataFrame, row_var: str, col_var: str) -> dict:
    _check_distinct([row_var, col_var])
    data = df[[row_var, col_var]].dropna().astype(str)
    dropped = len(df) - len(data)
    tab = pd.crosstab(data[row_var], data[col_var])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        raise AnalysisError("두 변수 모두 범주가 2개 이상이어야 교차분석을 할 수 있습니다.")
    if tab.shape[0] * tab.shape[1] > 100:
        raise AnalysisError("범주가 너무 많습니다(칸 100개 초과). 범주형 변수를 고르세요.")
    chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
    n = int(tab.to_numpy().sum())
    k = min(tab.shape) - 1
    v = np.sqrt(chi2 / (n * k)) if k > 0 else np.nan
    low = float((exp < 5).mean() * 100)
    fisher_p = None
    if tab.shape == (2, 2):
        fisher_p = float(stats.fisher_exact(tab.to_numpy())[1])
    row_pct = tab.div(tab.sum(axis=1), axis=0) * 100
    exp_df = pd.DataFrame(exp, index=tab.index, columns=tab.columns)
    std_resid = (tab - exp_df) / np.sqrt(exp_df)
    return {"table": tab, "row_pct": row_pct, "expected": exp_df, "std_resid": std_resid,
            "chi2": chi2, "p": p, "df": dof, "n": n, "cramers_v": v, "low_expected_pct": low,
            "fisher_p": fisher_p, "dropped": dropped, "row": row_var, "col": col_var}


def chi_sentence(r: dict) -> str:
    size = "큰" if r["cramers_v"] >= .5 else "중간" if r["cramers_v"] >= .3 else "작은" if r["cramers_v"] >= .1 else "매우 작은"
    s = (f"'{r['row']}'와 '{r['col']}'는 {'통계적으로 유의한 관련이 있었다' if r['p'] < .05 else '유의한 관련이 없었다'}, "
         f"χ²({r['df']}, N = {r['n']}) = {r['chi2']:.2f}, {_apa_p_eq(r['p'])}, Cramér's V = {apa_num(r['cramers_v'], 2, False)}({size} 효과).")
    if r["low_expected_pct"] > 20:
        s += f" 단, 기대빈도 5 미만인 칸이 {r['low_expected_pct']:.0f}%로 20%를 넘어 결과 해석에 주의가 필요하다"
        s += f"(Fisher 정확검정 {_apa_p_eq(r['fisher_p'])})." if r["fisher_p"] is not None else "."
    return s


# ---------------------------------------------------------------------------
# 신뢰도 (Cronbach α)
# ---------------------------------------------------------------------------
def reverse_items(df: pd.DataFrame, items: list[str], scale_min: float, scale_max: float) -> pd.DataFrame:
    out = df.copy()
    for c in items:
        out[c] = scale_min + scale_max - pd.to_numeric(out[c], errors="coerce")
    return out


def _alpha(x: np.ndarray) -> float:
    k = x.shape[1]
    item_var = x.var(axis=0, ddof=1).sum()
    total_var = x.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - item_var / total_var) if total_var > 0 else np.nan


def cronbach_alpha(df: pd.DataFrame, items: list[str]) -> dict:
    if len(items) < 2:
        raise AnalysisError("신뢰도 분석에는 문항이 2개 이상 필요합니다.")
    _check_distinct(list(items))
    data, dropped = _numeric_frame(df, list(items))
    n = len(data)
    if n < 3:
        raise AnalysisError(f"신뢰도 분석에는 응답자가 3명 이상 필요합니다. 현재 {n}명입니다.")
    x = data.to_numpy(float)
    if (x.std(axis=0, ddof=1) == 0).any():
        raise AnalysisError("모든 응답이 같은 문항이 있어 신뢰도를 계산할 수 없습니다.")
    alpha = _alpha(x)
    corr = np.corrcoef(x, rowvar=False)
    k = x.shape[1]
    mean_r = (corr.sum() - k) / (k * (k - 1))
    std_alpha = k * mean_r / (1 + (k - 1) * mean_r)
    rows = []
    total = x.sum(axis=1)
    for i, c in enumerate(items):
        rest = total - x[:, i]
        citc = np.corrcoef(x[:, i], rest)[0, 1]
        a_del = _alpha(np.delete(x, i, axis=1)) if k > 2 else np.nan
        rows.append({"문항": c, "평균": x[:, i].mean(), "표준편차": x[:, i].std(ddof=1),
                     "수정된 문항-총점 상관": citc, "문항 삭제 시 α": a_del})
    items_df = pd.DataFrame(rows)
    return {"alpha": alpha, "std_alpha": std_alpha, "k": k, "n": n, "dropped": dropped,
            "items": items_df, "mean_inter_r": mean_r,
            "negative": items_df.loc[items_df["수정된 문항-총점 상관"] < 0, "문항"].tolist(),
            "improve": items_df.loc[items_df["문항 삭제 시 α"] > alpha + 0.01, "문항"].tolist()}


def alpha_sentence(r: dict) -> str:
    a = r["alpha"]
    level = ("매우 좋은" if a >= .9 else "좋은" if a >= .8 else "수용 가능한" if a >= .7
             else "다소 낮은" if a >= .6 else "낮은")
    s = f"{r['k']}개 문항의 내적 일관성 신뢰도는 Cronbach's α = {apa_num(a, 2, False)}로 {level} 수준이었다(N = {r['n']})."
    if r["negative"]:
        s += f" 문항-총점 상관이 음수인 문항({', '.join(r['negative'])})은 역문항일 수 있으니 역코딩 여부를 확인하라."
    elif r["improve"]:
        s += f" {', '.join(r['improve'])} 문항을 빼면 α가 높아지므로 문항 내용을 검토할 필요가 있다."
    return s


# ---------------------------------------------------------------------------
# 기존 분석의 APA 보고 문장
# ---------------------------------------------------------------------------
def apa_regression(res: dict) -> str:
    s = (f"R² = {apa_num(res['r2'], 3, False)}, adj. R² = {apa_num(res['adj_r2'], 3, False)}, "
         f"F({res['df1']}, {res['df2']}) = {res['F']:.2f}, {_apa_p_eq(res['F_p'])}")
    for _, r in res["coef"].iloc[1:].iterrows():
        s += f"; {r['변수']}: B = {r['B']:.3f}, SE = {r['SE']:.3f}, β = {apa_num(r['β(표준화)'], 2, False)}, t({res['df2']}) = {r['t']:.2f}, {_apa_p_eq(r['p'])}"
    return s


def apa_anova1(res: dict) -> str:
    return (f"F({res['df1']}, {res['df2']}) = {res['F']:.2f}, {_apa_p_eq(res['p'])}, "
            f"η² = {apa_num(res['eta2'], 2, False)}, ω² = {apa_num(res['omega2'], 2, False)}")


def apa_anova2(res: dict) -> str:
    t = res["table"]
    dfe = int(t["df"].iloc[3])
    return "; ".join(f"{t['변동원'][i]}: F({int(t['df'][i])}, {dfe}) = {t['F'][i]:.2f}, {_apa_p_eq(t['p'][i])}, "
                     f"partial η² = {apa_num(t['부분 η²'][i], 2, False)}" for i in range(3))


def apa_mediation(r: dict) -> str:
    lo, hi = r["boot_ci"]
    return (f"a = {r['a']:.3f}, b = {r['b']:.3f}, c = {r['c']:.3f}, c' = {r['c_prime']:.3f}, "
            f"indirect effect ab = {r['ab']:.3f}, 95% bootstrap CI [{lo:.3f}, {hi:.3f}] ({r['n_boot']} resamples)")


def apa_moderation(r: dict) -> str:
    ir = r["int_row"]
    return (f"{ir['변수']}: B = {ir['B']:.3f}, SE = {ir['SE']:.3f}, t({r['df2']}) = {ir['t']:.2f}, {_apa_p_eq(ir['p'])}; "
            f"ΔR² = {apa_num(r['delta_r2'], 3, False)}; model R² = {apa_num(r['r2'], 3, False)}")


# ---------------------------------------------------------------------------
# 결측 처리
# ---------------------------------------------------------------------------
def impute_mean(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict]:
    """숫자형 열의 결측(및 숫자로 바꿀 수 없는 값)을 평균으로 채움. (새 데이터, {열: 채운 개수})"""
    out = df.copy()
    filled = {}
    for c in columns:
        s = pd.to_numeric(out[c], errors="coerce")
        k = int(s.isna().sum())
        if k and s.notna().any():
            out[c] = s.fillna(s.mean())
            filled[c] = k
        else:
            out[c] = s
    return out, filled
