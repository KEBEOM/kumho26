"""📊 초보자용 통계분석 앱 (PC·스마트폰 브라우저 겸용)

실행:  streamlit run app.py
스마트폰:  streamlit run app.py --server.address 0.0.0.0  →  http://PC-IP:8501
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import analysis as A
from analysis import AnalysisError

HERE = Path(__file__).resolve().parent
SAMPLE_FILES = {
    "기준데이터 (교수자 검산용, 36행)": HERE / "data" / "기준데이터.xlsx",
    "sample.xlsx (연습용, 12행)": HERE / "sample.xlsx",
}
MENU = [
    "0. 데이터 확인",
    "1. 기초통계",
    "2. 단순회귀",
    "3. 다중회귀",
    "4. 일원분산분석",
    "5. 이원분산분석",
    "6. 매개효과 (X→M→Y)",
    "7. 조절효과 (X×W→Y)",
    "8. 기준값 검산",
]

st.set_page_config(page_title="통계분석 앱", page_icon="📊", layout="centered")

# 스마트폰에서 여백을 줄이고 표가 잘리지 않도록 하는 간단한 CSS
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-left: 0.8rem; padding-right: 0.8rem; max-width: 900px;}
    div[data-testid="stMetricValue"] {font-size: 1.35rem;}
    div[data-testid="stDataFrame"] {overflow-x: auto;}
    @media (max-width: 640px) {
        h1 {font-size: 1.5rem !important;}
        h2, h3 {font-size: 1.15rem !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# 표시 도우미
# ---------------------------------------------------------------------------
def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ""
    return "< .001" if p < 0.001 else f"{p:.3f}"


def show_table(df: pd.DataFrame, p_cols=("p", "p(Tukey)"), digits=3, index=False):
    """숫자를 반올림하고 p값을 보기 좋게 바꿔 표시. 좁은 화면 모드면 세로로 뒤집기."""
    out = df.copy()
    for c in out.columns:
        if c in p_cols:
            out[c] = out[c].map(fmt_p)
        elif pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].round(digits)
    if st.session_state.get("narrow") and out.shape[1] > 4 and out.shape[0] <= 6:
        first = out.columns[0]
        out = out.set_index(first).T if not index else out.T
        st.dataframe(out)
    else:
        st.dataframe(out, hide_index=not index)


def metric_row(items):
    """[(라벨, 값), ...] 을 2개씩 끊어 표시 (스마트폰에서 줄바꿈이 깔끔함)."""
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        for col, (label, value) in zip(cols, items[i:i + 2]):
            col.metric(label, value)


def notice_dropped(n, dropped):
    msg = f"분석에 사용한 사례 수: **{n}개**"
    if dropped:
        msg += f" (결측·숫자 아닌 값이 있는 {dropped}개 행은 제외)"
    st.caption(msg)


def friendly(fn):
    """분석 함수를 감싸서 어떤 오류가 나도 앱이 멈추지 않게 함."""
    try:
        return fn()
    except AnalysisError as e:
        st.warning(f"⚠️ {e}")
    except Exception as e:  # 예상하지 못한 오류
        st.error("계산 중 예상하지 못한 문제가 생겼습니다. 변수 선택과 데이터 값을 확인해 주세요.")
        with st.expander("자세한 오류 내용 (개발자용)"):
            st.code(repr(e))
    return None


def download_button(df: pd.DataFrame, name: str):
    st.download_button(
        "⬇️ 결과표 CSV 저장", df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}",
    )


# ---------------------------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_file(data: bytes, name: str) -> pd.DataFrame:
    import io
    lower = name.lower()
    bio = io.BytesIO(data)
    if lower.endswith(".csv"):
        for enc in ("utf-8-sig", "cp949", "euc-kr"):
            try:
                bio.seek(0)
                return pd.read_csv(bio, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise AnalysisError("CSV 글자 인코딩을 알 수 없습니다. 엑셀에서 'CSV UTF-8'로 다시 저장해 보세요.")
    if lower.endswith(".xls"):
        return pd.read_excel(bio, engine="xlrd")
    return pd.read_excel(bio)


st.title("📊 초보자용 통계분석 앱")
st.write("엑셀(.xlsx/.xls) 또는 CSV 파일을 올리고 분석 메뉴를 고르세요. 스마트폰 브라우저에서도 동작합니다.")

with st.sidebar:
    st.header("⚙️ 설정")
    st.toggle("📱 좁은 화면용 표(세로로 보기)", key="narrow",
              help="스마트폰에서 표가 옆으로 길면 켜세요.")
    st.markdown("---")
    st.markdown("**사용 순서**\n1. 파일 올리기\n2. 분석 메뉴 고르기\n3. 변수 고르기\n4. 결과·해석 확인")
    st.caption("개인정보(이름·학번·연락처)가 있는 파일은 올리지 마세요.")

source = st.radio("데이터 선택", ["내 파일 올리기", "예제 데이터 사용"], horizontal=True)
df = None
if source == "내 파일 올리기":
    uploaded = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "xls", "csv"])
    if uploaded is None:
        st.info("파일을 올리거나 '예제 데이터 사용'을 눌러 바로 시험해 보세요.")
        st.stop()
    try:
        df = read_file(uploaded.getvalue(), uploaded.name)
    except AnalysisError as e:
        st.error(f"⚠️ {e}")
        st.stop()
    except Exception:
        st.error("파일을 읽지 못했습니다. 엑셀/CSV 파일이 맞는지, 첫 줄에 열 이름이 있는지, 파일이 손상되지 않았는지 확인하세요.")
        st.stop()
    data_name = uploaded.name
else:
    pick = st.selectbox("예제 파일", list(SAMPLE_FILES))
    path = SAMPLE_FILES[pick]
    if not path.exists():
        st.error(f"예제 파일이 없습니다: {path.name}. 압축을 풀 때 data 폴더가 빠지지 않았는지 확인하세요.")
        st.stop()
    df = pd.read_excel(path)
    data_name = path.name

if df is None or df.empty or df.shape[1] == 0:
    st.error("파일에 데이터가 없습니다. 첫 줄은 열 이름, 둘째 줄부터 값이 있어야 합니다.")
    st.stop()

df.columns = [str(c).strip() for c in df.columns]
if df.columns.duplicated().any():
    st.error("같은 이름의 열이 있습니다. 엑셀에서 열 이름을 서로 다르게 고쳐 주세요.")
    st.stop()

NUM = A.numeric_columns(df)
CAT = A.categorical_columns(df)

st.success(f"'{data_name}' 불러옴 — 행 {df.shape[0]}개, 열 {df.shape[1]}개 (숫자형 {len(NUM)}개)")
menu = st.selectbox("분석 메뉴", MENU, index=1)
st.markdown("---")


def need(cols, k, what):
    if len(cols) < k:
        st.warning(f"⚠️ 이 분석에는 {what}이(가) {k}개 이상 필요합니다. 현재 파일에는 {len(cols)}개입니다.")
        st.stop()


# ---------------------------------------------------------------------------
# 0. 데이터 확인
# ---------------------------------------------------------------------------
if menu == MENU[0]:
    st.subheader("데이터 미리보기 (처음 20행)")
    st.dataframe(df.head(20))
    info = pd.DataFrame({
        "열 이름": df.columns,
        "자료형": ["숫자형" if c in NUM else "문자/범주형" for c in df.columns],
        "결측 수": df.isna().sum().values,
        "서로 다른 값 수": df.nunique().values,
    })
    st.subheader("열 정보")
    show_table(info)

# ---------------------------------------------------------------------------
# 1. 기초통계
# ---------------------------------------------------------------------------
elif menu == MENU[1]:
    st.subheader("1. 기초통계")
    tab1, tab2 = st.tabs(["숫자형 변수", "빈도·비율"])
    with tab1:
        sel = st.multiselect("변수 선택", NUM, default=NUM[:3]) if NUM else []
        if not NUM:
            st.warning("⚠️ 숫자형 변수가 없습니다. '빈도·비율' 탭을 이용하세요.")
        elif sel:
            res = A.descriptive_statistics(df, sel)
            show_table(res)
            for c in sel:
                bad = df[c].notna() & pd.to_numeric(df[c], errors="coerce").isna()
                if bad.any():
                    st.caption(f"ℹ️ '{c}'의 숫자가 아닌 값 {int(bad.sum())}개(예: '{df[c][bad].iloc[0]}')는 결측으로 처리했습니다.")
            download_button(res, "기초통계")
            var = st.selectbox("그래프로 볼 변수", sel)
            s = pd.to_numeric(df[var], errors="coerce").dropna()
            if len(s) > 1 and s.nunique() > 1:
                bins = st.slider("막대 개수", 3, 30, min(10, max(3, s.nunique())))
                counts, edges = np.histogram(s, bins=bins)
                hist = pd.DataFrame({"구간": [f"{edges[i]:.1f}~{edges[i+1]:.1f}" for i in range(bins)], "빈도": counts})
                st.bar_chart(hist, x="구간", y="빈도")
            else:
                st.info("값이 하나뿐이라 그래프를 그리지 않습니다.")
        else:
            st.info("변수를 1개 이상 고르세요.")
    with tab2:
        col = st.selectbox("빈도를 볼 변수", list(df.columns),
                           index=list(df.columns).index(CAT[0]) if CAT else 0)
        if df[col].nunique() > 50:
            st.warning("서로 다른 값이 50개를 넘어 빈도표가 너무 깁니다. 범주형 변수를 고르세요.")
        else:
            ft = friendly(lambda: A.frequency_table(df, col))
            if ft is not None:
                ft["값"] = ft["값"].astype(str)
                show_table(ft)
                st.bar_chart(ft, x="값", y="빈도")


# ---------------------------------------------------------------------------
# 2·3. 회귀
# ---------------------------------------------------------------------------
def show_regression(res):
    metric_row([("R²", f"{res['r2']:.4f}"), ("수정 R²", f"{res['adj_r2']:.4f}"),
                (f"F({res['df1']}, {res['df2']})", f"{res['F']:.3f}"), ("모형 p", fmt_p(res["F_p"]))])
    notice_dropped(res["n"], res["dropped"])
    c = res["coef"]
    eq = f"{res['y']} = {c['B'][0]:.3f}" + "".join(
        f" {'+' if b >= 0 else '-'} {abs(b):.3f}×{v}" for v, b in zip(c["변수"][1:], c["B"][1:]))
    st.markdown(f"**회귀식:** `{eq}`")
    st.markdown("**회귀계수**")
    show_table(c)
    download_button(c, f"회귀계수_{res['y']}")
    if res.get("vif") is not None:
        st.markdown("**다중공선성 (VIF)**")
        show_table(res["vif"])
        if (res["vif"]["VIF"] > 10).any():
            st.warning("VIF가 10을 넘는 변수가 있습니다. 독립변수끼리 너무 비슷해서 계수가 불안정할 수 있습니다.")
        else:
            st.caption("VIF가 모두 10 미만이면 다중공선성 문제가 크지 않다고 봅니다.")
    st.markdown("**잔차 그래프** (예측값 vs 잔차: 0 주변에 고르게 퍼져 있으면 좋음)")
    st.scatter_chart(pd.DataFrame({"예측값": res["fitted"], "잔차": res["resid"]}), x="예측값", y="잔차")
    st.info("📝 해석: " + A.regression_sentence(res))


if menu == MENU[2]:
    st.subheader("2. 단순회귀 (X 1개 → Y)")
    need(NUM, 2, "숫자형 변수")
    y = st.selectbox("종속변수 Y", NUM, index=NUM.index("score") if "score" in NUM else 0)
    xs_opt = [c for c in NUM if c != y]
    x = st.selectbox("독립변수 X", xs_opt, index=xs_opt.index("study_time") if "study_time" in xs_opt else 0)
    res = friendly(lambda: A.regression(df, y, [x]))
    if res:
        show_regression(res)
        st.markdown("**산점도와 회귀선**")
        d = res["data"].sort_values(x)
        b0, b1 = res["coef"]["B"][0], res["coef"]["B"][1]
        plot = pd.DataFrame({x: d[x], "관측값": d[y], "회귀선(예측값)": b0 + b1 * d[x]})
        st.scatter_chart(plot, x=x, y=["관측값", "회귀선(예측값)"])

elif menu == MENU[3]:
    st.subheader("3. 다중회귀 (X 여러 개 → Y)")
    need(NUM, 3, "숫자형 변수")
    y = st.selectbox("종속변수 Y", NUM, index=NUM.index("score") if "score" in NUM else 0)
    xs_opt = [c for c in NUM if c != y]
    default = [c for c in ("study_time", "pre_score") if c in xs_opt] or xs_opt[:2]
    xs = st.multiselect("독립변수 X (2개 이상 권장)", xs_opt, default=default)
    if not xs:
        st.info("독립변수를 1개 이상 고르세요.")
    else:
        res = friendly(lambda: A.regression(df, y, xs))
        if res:
            show_regression(res)
            st.caption("β(표준화)는 단위가 다른 변수들의 영향력을 비교할 때 사용합니다.")

# ---------------------------------------------------------------------------
# 4. 일원분산분석
# ---------------------------------------------------------------------------
elif menu == MENU[4]:
    st.subheader("4. 일원분산분석 (집단 간 평균 비교)")
    need(NUM, 1, "숫자형 변수")
    need(CAT, 1, "집단변수(값 종류 2~20개)")
    y = st.selectbox("종속변수 Y (숫자형)", NUM, index=NUM.index("anova_score") if "anova_score" in NUM else 0)
    g_opt = [c for c in CAT if c != y]
    if not g_opt:
        st.warning("집단변수로 쓸 열이 없습니다.")
        st.stop()
    g = st.selectbox("집단변수", g_opt, index=g_opt.index("method") if "method" in g_opt else 0)
    res = friendly(lambda: A.one_way_anova(df, y, g))
    if res:
        metric_row([(f"F({res['df1']}, {res['df2']})", f"{res['F']:.4f}"), ("p", fmt_p(res["p"])),
                    ("η² (효과크기)", f"{res['eta2']:.3f}"), ("ω²", f"{res['omega2']:.3f}")])
        notice_dropped(res["n"], res["dropped"])
        st.markdown("**집단별 기술통계**")
        show_table(res["desc"])
        st.bar_chart(res["desc"].assign(집단=res["desc"]["집단"].astype(str)), x="집단", y="평균")
        st.markdown("**분산분석표**")
        show_table(res["table"])
        download_button(res["table"], "일원분산분석표")
        st.markdown("**사후검정 (Tukey HSD)**")
        show_table(res["posthoc"])
        st.caption(f"등분산 검정(Levene): W={res['levene_W']:.3f}, {A.p_text(res['levene_p'])}"
                   + (" → 등분산 가정이 의심되므로 해석에 주의하세요." if res["levene_p"] < 0.05 else " → 등분산 가정을 크게 벗어나지 않습니다."))
        size = "큰" if res["eta2"] >= 0.14 else "중간" if res["eta2"] >= 0.06 else "작은"
        sig_pairs = res["posthoc"].loc[res["posthoc"]["p(Tukey)"] < 0.05, "비교"].tolist()
        st.info(
            f"📝 해석: '{g}' 집단에 따라 '{y}' 평균이 "
            f"{'통계적으로 유의하게 달랐다' if res['p'] < 0.05 else '유의하게 다르다고 보기 어렵다'}"
            f"(F({res['df1']}, {res['df2']})={res['F']:.2f}, {A.p_text(res['p'])}, η²={res['eta2']:.3f}, {size} 효과). "
            + (f"사후검정에서 차이가 유의한 쌍: {', '.join(sig_pairs)}." if sig_pairs else "사후검정에서 유의한 쌍은 없었다.")
        )

# ---------------------------------------------------------------------------
# 5. 이원분산분석
# ---------------------------------------------------------------------------
elif menu == MENU[5]:
    st.subheader("5. 이원분산분석 (두 요인 + 상호작용)")
    need(NUM, 1, "숫자형 변수")
    need(CAT, 2, "집단변수(값 종류 2~20개)")
    y = st.selectbox("종속변수 Y (숫자형)", NUM, index=NUM.index("anova_score") if "anova_score" in NUM else 0)
    opts = [c for c in CAT if c != y]
    a = st.selectbox("요인 A", opts, index=opts.index("method") if "method" in opts else 0)
    b_opts = [c for c in opts if c != a]
    if not b_opts:
        st.warning("요인 B로 쓸 다른 집단변수가 없습니다.")
        st.stop()
    b = st.selectbox("요인 B", b_opts, index=b_opts.index("grade") if "grade" in b_opts else 0)
    res = friendly(lambda: A.two_way_anova(df, y, a, b))
    if res:
        notice_dropped(res["n"], res["dropped"])
        st.markdown("**분산분석표 (Type III 제곱합)**")
        show_table(res["table"])
        download_button(res["table"], "이원분산분석표")
        if not res["balanced"]:
            st.caption("칸마다 사례 수가 다른 불균형 자료입니다. Type III 제곱합을 사용했습니다.")
        st.markdown("**칸 평균**")
        show_table(res["cell_means"].reset_index())
        st.markdown(f"**상호작용 그래프** (선이 평행하지 않을수록 상호작용이 큼)")
        plot = res["cell_means"].copy()
        plot.index = plot.index.astype(str)
        plot.columns = [f"{b}={c}" for c in plot.columns]
        st.line_chart(plot)
        t = res["table"]
        lines = []
        for i in range(3):
            lines.append(f"{t['변동원'][i]}: F={t['F'][i]:.2f}, {A.p_text(t['p'][i])}, 부분η²={t['부분 η²'][i]:.3f}")
        st.info("📝 결과 요약: " + " / ".join(lines))
        if res["interaction_p"] < 0.05:
            st.warning(f"⚠️ 상호작용이 유의합니다. '{a}'의 효과가 '{b}' 수준에 따라 다르므로, "
                       "각 요인의 주효과만 따로 해석하지 말고 상호작용 그래프와 칸 평균을 함께 보고 해석하세요.")

# ---------------------------------------------------------------------------
# 6. 매개효과
# ---------------------------------------------------------------------------
elif menu == MENU[6]:
    st.subheader("6. 단순 매개효과 (X → M → Y)")
    need(NUM, 3, "숫자형 변수")
    pick = lambda name, i: NUM.index(name) if name in NUM else min(i, len(NUM) - 1)
    x = st.selectbox("독립변수 X", NUM, index=pick("med_x", 0))
    m = st.selectbox("매개변수 M", NUM, index=pick("med_m", 1))
    y = st.selectbox("종속변수 Y", NUM, index=pick("med_y", 2))
    nb = st.select_slider("부트스트랩 반복 수", [1000, 2000, 5000], value=2000)
    with st.spinner("부트스트랩 계산 중..."):
        res = friendly(lambda: A.mediation(df, x, m, y, n_boot=nb))
    if res:
        lo, hi = res["boot_ci"]
        metric_row([("a", f"{res['a']:.4f}"), ("b", f"{res['b']:.4f}"),
                    ("c (총효과)", f"{res['c']:.4f}"), ("c' (직접효과)", f"{res['c_prime']:.4f}"),
                    ("간접효과 ab", f"{res['ab']:.4f}"), ("95% 부트스트랩 CI", f"[{lo:.3f}, {hi:.3f}]")])
        notice_dropped(res["n"], res["dropped"])
        st.code(
            f"            [{m}]\n"
            f"   a={res['a']:.3f} ↗      ↘ b={res['b']:.3f}\n"
            f"[{x}] ── c'={res['c_prime']:.3f} ──→ [{y}]",
            language=None,
        )
        show_table(res["paths"])
        download_button(res["paths"], "매개효과_경로")
        st.caption(f"Sobel 검정: z={res['sobel_z']:.3f}, {A.p_text(res['sobel_p'])} · "
                   f"부트스트랩 {res['n_boot']}회 (난수 고정, 다시 실행해도 같은 결과)")
        st.info("📝 해석: " + A.mediation_sentence(res))

# ---------------------------------------------------------------------------
# 7. 조절효과
# ---------------------------------------------------------------------------
elif menu == MENU[7]:
    st.subheader("7. 조절효과 (Y ~ X + W + X×W)")
    need(NUM, 3, "숫자형 변수")
    pick = lambda name, i: NUM.index(name) if name in NUM else min(i, len(NUM) - 1)
    x = st.selectbox("독립변수 X", NUM, index=pick("mod_x", 0))
    w = st.selectbox("조절변수 W", NUM, index=pick("mod_w", 1))
    y = st.selectbox("종속변수 Y", NUM, index=pick("mod_y", 2))
    center = st.checkbox("X, W 평균중심화 (상호작용 B와 R²는 변하지 않고, X·W 계수 해석이 쉬워짐)")
    res = friendly(lambda: A.moderation(df, x, w, y, center=center))
    if res:
        ir = res["int_row"]
        metric_row([("상호작용 B", f"{ir['B']:.4f}"), ("상호작용 p", fmt_p(ir["p"])),
                    ("R²", f"{res['r2']:.4f}"), ("ΔR² (상호작용)", f"{res['delta_r2']:.4f}")])
        notice_dropped(res["n"], res["dropped"])
        st.markdown("**회귀계수**")
        show_table(res["coef"])
        st.markdown("**단순기울기** (W 수준별 X의 효과)")
        show_table(res["simple_slopes"])
        download_button(res["simple_slopes"], "조절효과_단순기울기")
        d = res["data"]
        xs = np.linspace(d[x].min(), d[x].max(), 20)
        B = res["coef"]["B"].to_numpy()
        plot = pd.DataFrame({x: xs})
        for label, wv in zip(["W 낮음", "W 평균", "W 높음"], res["w_levels"]):
            plot[label] = B[0] + B[1] * xs + B[2] * wv + B[3] * xs * wv
        st.markdown("**단순기울기 그래프**")
        st.line_chart(plot, x=x, y=["W 낮음", "W 평균", "W 높음"])
        st.info("📝 해석: " + A.moderation_sentence(res))

# ---------------------------------------------------------------------------
# 8. 기준값 검산
# ---------------------------------------------------------------------------
elif menu == MENU[8]:
    st.subheader("8. 기준값 검산 (교수자 기준결과와 비교)")
    missing = A.REFERENCE_COLUMNS - set(df.columns)
    if missing:
        st.warning("이 메뉴는 교수자 기준데이터(통계앱_기준데이터.xlsx) 전용입니다. "
                   "위에서 '예제 데이터 사용 → 기준데이터'를 고르세요. "
                   f"(없는 열: {', '.join(sorted(missing))})")
    else:
        with st.spinner("모든 분석을 다시 계산하는 중..."):
            chk = A.reference_check(df)
        ok = (chk["판정"] == "일치").sum()
        metric_row([("일치 항목", f"{ok} / {len(chk)}"), ("판정", "✅ 모두 일치" if ok == len(chk) else "⚠️ 확인 필요")])
        out = chk.copy()
        out["앱 결과"] = out["앱 결과"].round(6)
        out["차이"] = out["차이"].map(lambda v: f"{v:.2e}" if pd.notna(v) else "")
        st.dataframe(out, hide_index=True)
        download_button(chk, "검산결과")
        st.caption("소수점 반올림 차이(마지막 자리)는 허용합니다.")

st.markdown("---")
st.caption("교육용 통계분석 앱 · 결과는 통계적 관계를 보여 줄 뿐 인과관계를 증명하지 않습니다. "
           "실제 연구에 쓰기 전 기준데이터로 검산하세요.")
