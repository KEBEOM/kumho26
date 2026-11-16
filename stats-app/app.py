"""📊 초보자용 통계분석 앱 (PC·스마트폰 브라우저 겸용)
by 2026 금오공대 빅데이터 8조

실행:  streamlit run app.py
스마트폰:  streamlit run app.py --server.address 0.0.0.0  →  http://PC-IP:8501
"""
import html
import io
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import analysis as A
from analysis import AnalysisError

CREDIT = "by 2026 금오공대 빅데이터 8조"
HERE = Path(__file__).resolve().parent
SAMPLE_FILES = {
    "기준데이터 (교수자 검산용, 36행)": HERE / "data" / "reference_data.xlsx",
    "설문 예제 (가상 설문, 120명)": HERE / "data" / "survey_sample.xlsx",
    "sample.xlsx (연습용, 12행)": HERE / "data" / "sample.xlsx",
}

M_DATA = "0. 데이터 확인"
M_DESC = "1. 기초통계"
M_NORM = "2. 정규성 검정"
M_CORR = "3. 상관분석"
M_T = "4. t검정"
M_CHI = "5. 교차분석 (카이제곱)"
M_ALPHA = "6. 신뢰도 (Cronbach α)"
M_REG1 = "7. 단순회귀"
M_REG2 = "8. 다중회귀"
M_AOV1 = "9. 일원분산분석"
M_AOV2 = "10. 이원분산분석"
M_MED = "11. 매개효과 (X→M→Y)"
M_MOD = "12. 조절효과 (X×W→Y)"
M_CHECK = "13. 기준값 검산"
M_REPORT = "14. 보고서 내려받기"
MENU = [M_DATA, M_DESC, M_NORM, M_CORR, M_T, M_CHI, M_ALPHA, M_REG1, M_REG2,
        M_AOV1, M_AOV2, M_MED, M_MOD, M_CHECK, M_REPORT]

st.set_page_config(page_title="통계분석 앱", page_icon="📊", layout="centered")

# ---------------------------------------------------------------------------
# 디자인 토큰 · 스타일 (Pretendard, 잉크 네이비 + 블루 포인트)
# ---------------------------------------------------------------------------
ACCENT = "#2A78D6"
SERIES = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#8A63D2", "#E34948"]  # 색각이상 검증 순서


def series_colors(n):
    return SERIES[:n] if n <= len(SERIES) else None


st.markdown(
    """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
:root { --ink:#16223A; --ink-2:#3B4658; --muted:#687386; --rule:#DCE1E8; --panel:#F3F5F8; --accent:#2A78D6; --accent-soft:#EDF4FC; }
html, body, .stApp, .stMarkdown, p, li, label, h1, h2, h3, h4, input, textarea, button,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stWidgetLabel"] {
  font-family: 'Pretendard Variable', Pretendard, -apple-system, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}
.stMarkdown, .hero, .interp, .foot, [data-testid="stAlert"] { word-break: keep-all; overflow-wrap: anywhere; }
.block-container { padding-top: 3.2rem; padding-left: 1rem; padding-right: 1rem; max-width: 920px; }
header[data-testid="stHeader"] { background: transparent; }

/* 머리 영역: 앱에서 유일하게 강한 요소 */
.hero { position: relative; overflow: hidden; background: var(--ink); color: #fff; border-radius: 10px; padding: 1.7rem 1.7rem 1.4rem; margin-bottom: 1.4rem; }
.hero svg { position: absolute; right: 0; bottom: 0; width: 56%; height: 100%; }
.hero .curve { fill: none; stroke: #8DB8EC; stroke-width: 1.6; }
.hero .ci { fill: rgba(42, 120, 214, .32); }
.hero .base { stroke: #3A4A66; stroke-width: 1; }
.hero .cut { stroke: #8DB8EC; stroke-width: 1; stroke-dasharray: 3 3; opacity: .7; }
.hero-text { position: relative; max-width: 25rem; }
.hero h1 { color: #fff; font-size: 1.95rem; font-weight: 700; letter-spacing: -0.025em; line-height: 1.2; margin: 0 0 .45rem; padding: 0; }
.hero .sub { color: #C7D1E1; font-size: .95rem; line-height: 1.6; margin: 0; }
.hero .credit { color: #8495AF; font-size: .74rem; margin: 1.1rem 0 0; }

/* 데이터 요약 줄 */
.dstrip { display: grid; grid-template-columns: 2.2fr 1fr 1fr 1fr 1fr; border: 1px solid var(--rule); border-radius: 8px; margin: .2rem 0 1rem; }
.dstrip > div { padding: .6rem .85rem; border-left: 1px solid var(--rule); min-width: 0; }
.dstrip > div:first-child { border-left: 0; }
.dstrip .k { display: block; color: var(--muted); font-size: .74rem; }
.dstrip .v { display: block; color: var(--ink); font-weight: 650; font-size: 1.02rem; font-variant-numeric: tabular-nums; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 결과 영역 */
h3 { color: var(--ink) !important; font-weight: 700 !important; letter-spacing: -0.015em; border-bottom: 1px solid var(--rule); padding-bottom: .45rem !important; margin-top: .4rem !important; }
[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: .65rem .9rem; }
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: .8rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: 1.35rem; font-weight: 650; font-variant-numeric: tabular-nums; }
.interp { border-left: 3px solid var(--accent); background: var(--accent-soft); border-radius: 0 8px 8px 0; padding: .8rem 1rem; margin: .7rem 0 1rem; color: var(--ink-2); line-height: 1.7; font-size: .95rem; }
.interp strong { display: block; color: var(--accent); font-size: .8rem; font-weight: 700; margin-bottom: .15rem; }
.apa-label { color: var(--muted); font-size: .8rem; margin: .4rem 0 -.3rem; }
.stButton button, .stDownloadButton button { border-radius: 6px; font-weight: 600; }
[data-testid="stSidebar"] { border-right: 1px solid var(--rule); }
.foot { color: var(--muted); font-size: .75rem; line-height: 1.6; text-align: center; border-top: 1px solid var(--rule); padding-top: 1rem; margin-top: 2rem; }
.foot .who { color: var(--ink-2); font-weight: 600; }

@media (max-width: 640px) {
  .block-container { padding-left: .7rem; padding-right: .7rem; }
  .hero { padding: 1.3rem 1.2rem 1.1rem; }
  .hero svg { width: 100%; opacity: .35; }
  .hero h1 { font-size: 1.5rem; }
  .dstrip { grid-template-columns: 1fr 1fr; }
  .dstrip > div { border-left: 0; border-top: 1px solid var(--rule); }
  .dstrip > div:first-child { grid-column: 1 / -1; border-top: 0; }
  .dstrip > div:nth-child(odd):not(:first-child) { border-left: 1px solid var(--rule); }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)


def _bell_svg() -> str:
    """정규분포 곡선 + 95% 구간(±1.96)을 그린 장식용 SVG."""
    w, h, top, base = 600, 170, 22, 150
    xs = [-3.6 + 7.2 * i / 120 for i in range(121)]
    sx = lambda x: (x + 3.6) / 7.2 * w
    sy = lambda x: base - (base - top) * math.exp(-x * x / 2)
    curve = "M" + " L".join(f"{sx(x):.1f},{sy(x):.1f}" for x in xs)
    ci_x = [x for x in xs if -1.96 <= x <= 1.96]
    ci = (f"M{sx(-1.96):.1f},{base} " + " ".join(f"L{sx(x):.1f},{sy(x):.1f}" for x in ci_x)
          + f" L{sx(1.96):.1f},{base} Z")
    cuts = "".join(f'<line class="cut" x1="{sx(v):.1f}" y1="{sy(v):.1f}" x2="{sx(v):.1f}" y2="{base}"/>' for v in (-1.96, 1.96))
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
            f'<path class="ci" d="{ci}"/>{cuts}<path class="curve" d="{curve}"/>'
            f'<line class="base" x1="0" y1="{base}" x2="{w}" y2="{base}"/></svg>')


def interp(text: str, head: str = "해석"):
    st.markdown(f'<div class="interp"><strong>{html.escape(head)}</strong>{html.escape(text)}</div>',
                unsafe_allow_html=True)


if "report" not in st.session_state:
    st.session_state["report"] = []


# ---------------------------------------------------------------------------
# 표시 도우미
# ---------------------------------------------------------------------------
def apa_mode() -> bool:
    return bool(st.session_state.get("apa"))


def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ""
    if apa_mode():
        return A.apa_p(p)
    return "< .001" if p < 0.001 else f"{p:.3f}"


P_COLS = ("p", "p(Tukey)")


def format_table(df: pd.DataFrame, digits=3) -> pd.DataFrame:
    """숫자 반올림 + p값 표기. APA 모드면 소수 둘째 자리, p는 앞의 0 생략."""
    out = df.copy()
    d = 2 if apa_mode() else digits
    for c in out.columns:
        if c in P_COLS:
            out[c] = out[c].map(fmt_p)
        elif pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].round(d)
    return out


def show_table(df: pd.DataFrame, digits=3, index=False):
    out = format_table(df, digits)
    if st.session_state.get("narrow") and out.shape[1] > 4 and out.shape[0] <= 6 and not index:
        out = out.set_index(out.columns[0]).T
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
        st.warning(f"{e}")
    except Exception as e:  # 예상하지 못한 오류
        st.error("계산 중 예상하지 못한 문제가 생겼습니다. 변수 선택과 데이터 값을 확인해 주세요.")
        with st.expander("자세한 오류 내용 (개발자용)"):
            st.code(repr(e))
    return None


def download_button(df: pd.DataFrame, name: str, index=False):
    st.download_button(
        "결과표 CSV로 저장", df.to_csv(index=index).encode("utf-8-sig"),
        file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}",
    )


def apa_box(text: str):
    st.markdown('<p class="apa-label">APA 보고 형식 · 오른쪽 위 아이콘으로 복사</p>', unsafe_allow_html=True)
    st.code(text, language=None)


def pick(options, preferred, fallback=0):
    for p in preferred:
        if p in options:
            return options.index(p)
    return min(fallback, max(len(options) - 1, 0))


# ---------------------------------------------------------------------------
# 보고서
# ---------------------------------------------------------------------------
def _add_report(title, parts):
    st.session_state["report"].append({
        "title": title, "parts": parts, "data": st.session_state.get("data_name", ""),
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    st.session_state["_last_added"] = title


def report_button(title: str, parts: list):
    """parts: [("table", 제목, DataFrame, index여부) | ("text", 문장) | ("apa", 문장)]"""
    frozen = [(p[0], p[1], format_table(p[2]), p[3]) if p[0] == "table" else p for p in parts]
    st.button("보고서에 담기", key=f"rep_{title}", on_click=_add_report, args=(title, frozen))
    if st.session_state.get("_last_added") == title:
        st.caption(f"보고서에 담았습니다. (현재 {len(st.session_state['report'])}개) · 메뉴 '{M_REPORT}'에서 내려받기")


def build_report_html(sections) -> str:
    body = []
    for i, sec in enumerate(sections, 1):
        body.append(f"<h2>{i}. {html.escape(sec['title'])}</h2>")
        body.append(f"<p class='meta'>데이터: {html.escape(str(sec['data']))} · 분석 시각 {sec['time']}</p>")
        for part in sec["parts"]:
            if part[0] == "table":
                _, cap, df, idx = part
                body.append(f"<p class='cap'>{html.escape(cap)}</p>")
                body.append(df.to_html(index=idx, na_rep="", border=0, classes="tbl"))
            elif part[0] == "text":
                body.append(f"<p class='interp'>{html.escape(part[1])}</p>")
            elif part[0] == "apa":
                body.append(f"<p class='apa'>APA: {html.escape(part[1])}</p>")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>통계분석 보고서</title>
<style>
body {{font-family: 'Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; color:#222; line-height:1.6}}
h1 {{font-size:1.6rem; border-bottom:2px solid #2E6BE6; padding-bottom:.4rem}}
h2 {{font-size:1.15rem; margin-top:2rem; color:#2E6BE6}}
.meta {{color:#888; font-size:.8rem; margin-top:-.6rem}}
.cap {{font-weight:bold; margin:1rem 0 .3rem}}
table.tbl {{border-collapse:collapse; font-size:.85rem; margin-bottom:.6rem}}
table.tbl th {{border-top:1.5px solid #222; border-bottom:1px solid #222; padding:4px 10px; text-align:center}}
table.tbl td {{padding:3px 10px; text-align:right}}
table.tbl tr:last-child td {{border-bottom:1.5px solid #222}}
.interp {{background:#f3f6fd; padding:.6rem .8rem; border-radius:6px}}
.apa {{font-family: 'Times New Roman', serif; font-style: italic; color:#333}}
.foot {{margin-top:3rem; color:#999; font-size:.75rem; text-align:center}}
@media print {{ body {{margin:0}} }}
</style></head><body>
<h1>📊 통계분석 결과 보고서</h1>
<p class="meta">작성 {now} · 분석 {len(sections)}건</p>
{''.join(body)}
<p class="foot">결과는 통계적 관계를 보여 줄 뿐 인과관계를 증명하지 않습니다.<br>{CREDIT}</p>
</body></html>"""


# ---------------------------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_file(data: bytes, name: str) -> pd.DataFrame:
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


st.markdown(
    '<section class="hero">' + _bell_svg() + '<div class="hero-text">'
    '<h1>통계분석 앱</h1>'
    '<p class="sub">엑셀이나 CSV 파일을 올리면 기초통계부터 매개·조절효과까지 계산하고, '
    '쉬운 해석과 APA 보고 문장을 함께 보여 줍니다.</p>'
    f'<p class="credit">{CREDIT}</p></div></section>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("설정")
    st.toggle("좁은 화면용 표 (세로로 보기)", key="narrow", help="스마트폰에서 표가 옆으로 길면 켜세요.")
    st.toggle("APA 형식 표", key="apa", help="소수 둘째 자리, p값 앞의 0 생략(.027) 등 논문 형식으로 표시합니다.")
    missing_mode = st.radio("결측값 처리", ["분석할 때 제외 (listwise)", "평균으로 대체 (숫자형)"],
                            help="평균 대체는 표본 수를 유지하지만 분산을 작게 만들 수 있습니다.")
    st.markdown("---")
    st.markdown(f"보고서에 담긴 결과: **{len(st.session_state['report'])}개**")
    st.markdown("**사용 순서**\n1. 파일 올리기\n2. 분석 메뉴 고르기\n3. 변수 고르기\n4. 결과와 해석 확인\n5. 보고서에 담고 내려받기")
    st.caption("개인정보(이름·학번·연락처)가 있는 파일은 올리지 마세요.")
    st.caption(CREDIT)

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
        st.error(f"{e}")
        st.stop()
    except Exception:
        st.error("파일을 읽지 못했습니다. 엑셀/CSV 파일이 맞는지, 첫 줄에 열 이름이 있는지, 파일이 손상되지 않았는지 확인하세요.")
        st.stop()
    data_name = uploaded.name
else:
    sample_pick = st.selectbox("예제 파일", list(SAMPLE_FILES))
    path = SAMPLE_FILES[sample_pick]
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

st.session_state["data_name"] = data_name
NUM = A.numeric_columns(df)
CAT = A.categorical_columns(df)
NUM_DEF = [c for c in NUM if c.lower() not in ("id", "no", "번호", "순번")] or NUM  # 기본 선택에서 ID 열 제외

if missing_mode.startswith("평균"):
    df, filled = A.impute_mean(df, NUM)
    if filled:
        st.info("결측값을 평균으로 채웠습니다: " + ", ".join(f"{k} {v}개" for k, v in filled.items()))

st.markdown(
    '<div class="dstrip">'
    f'<div><span class="k">불러온 파일</span><span class="v">{html.escape(str(data_name))}</span></div>'
    f'<div><span class="k">행</span><span class="v">{df.shape[0]:,}</span></div>'
    f'<div><span class="k">열</span><span class="v">{df.shape[1]}</span></div>'
    f'<div><span class="k">숫자형</span><span class="v">{len(NUM)}</span></div>'
    f'<div><span class="k">집단변수</span><span class="v">{len(CAT)}</span></div>'
    '</div>',
    unsafe_allow_html=True,
)
menu = st.selectbox("분석 메뉴", MENU, index=1)


def need(cols, k, what):
    if len(cols) < k:
        st.warning(f"이 분석에는 {what}이(가) {k}개 이상 필요합니다. 현재 파일에는 {len(cols)}개입니다.")
        st.stop()


# ---------------------------------------------------------------------------
# 0. 데이터 확인
# ---------------------------------------------------------------------------
if menu == M_DATA:
    st.subheader("데이터 미리보기 (처음 20행)")
    st.dataframe(df.head(20))
    info = pd.DataFrame({
        "열 이름": df.columns,
        "자료형": ["숫자형" if c in NUM else "문자/범주형" for c in df.columns],
        "결측 수": df.isna().sum().values,
        "서로 다른 값 수": df.nunique().values,
        "집단변수 가능": ["✓" if c in CAT else "" for c in df.columns],
    })
    st.subheader("열 정보")
    show_table(info)

# ---------------------------------------------------------------------------
# 1. 기초통계
# ---------------------------------------------------------------------------
elif menu == M_DESC:
    st.subheader(M_DESC)
    tab1, tab2 = st.tabs(["숫자형 변수", "빈도·비율"])
    with tab1:
        sel = st.multiselect("변수 선택", NUM, default=NUM_DEF[:3]) if NUM else []
        if not NUM:
            st.warning("숫자형 변수가 없습니다. '빈도·비율' 탭을 이용하세요.")
        elif sel:
            res = A.descriptive_statistics(df, sel)
            show_table(res)
            for c in sel:
                bad = df[c].notna() & pd.to_numeric(df[c], errors="coerce").isna()
                if bad.any():
                    st.caption(f"ℹ️ '{c}'의 숫자가 아닌 값 {int(bad.sum())}개(예: '{df[c][bad].iloc[0]}')는 결측으로 처리했습니다.")
            download_button(res, "기초통계")
            report_button("기초통계", [("table", "기술통계", res, False)])
            var = st.selectbox("그래프로 볼 변수", sel)
            s = pd.to_numeric(df[var], errors="coerce").dropna()
            if len(s) > 1 and s.nunique() > 1:
                bins = st.slider("막대 개수", 3, 30, min(10, max(3, s.nunique())))
                counts, edges = np.histogram(s, bins=bins)
                hist = pd.DataFrame({"구간": [f"{edges[i]:.1f}~{edges[i+1]:.1f}" for i in range(bins)], "빈도": counts})
                st.bar_chart(hist, x="구간", y="빈도", color=ACCENT)
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
                st.bar_chart(ft, x="값", y="빈도", color=ACCENT)
                report_button(f"빈도분석 - {col}", [("table", f"{col} 빈도·비율", ft, False)])

# ---------------------------------------------------------------------------
# 2. 정규성 검정
# ---------------------------------------------------------------------------
elif menu == M_NORM:
    st.subheader(M_NORM)
    need(NUM, 1, "숫자형 변수")
    sel = st.multiselect("변수 선택", NUM, default=NUM_DEF[:3])
    res = friendly(lambda: A.normality(df, sel)) if sel else None
    if not sel:
        st.info("변수를 1개 이상 고르세요.")
    if res:
        show_table(res["table"])
        download_button(res["table"], "정규성검정")
        st.caption("Shapiro-Wilk p ≥ .05 이면 정규분포 가정을 기각하지 않습니다. 표본이 크면(수백 이상) 작은 차이도 유의하게 나오므로 "
                   "왜도(|값| < 2)·첨도(|값| < 7)와 Q-Q 그림을 함께 보세요.")
        if res["qq"]:
            v = st.selectbox("Q-Q 그림을 볼 변수", list(res["qq"]))
            st.markdown("**Q-Q 그림** (점이 기준선 위에 있을수록 정규분포에 가까움)")
            st.scatter_chart(res["qq"][v], x="이론 분위수", y=["관측값", "기준선"], color=SERIES[:2])
        t = res["table"].dropna(subset=["p"])
        apa_box("; ".join(f"{r['변수']}: W = {A.apa_num(r['Shapiro-Wilk W'], 3, False)}, "
                          f"{'p ' + A.apa_p(r['p']) if r['p'] < .001 else 'p = ' + A.apa_p(r['p'])}" for _, r in t.iterrows()) or "-")
        report_button("정규성 검정", [("table", "Shapiro-Wilk 검정", res["table"], False)])

# ---------------------------------------------------------------------------
# 3. 상관분석
# ---------------------------------------------------------------------------
elif menu == M_CORR:
    st.subheader(M_CORR)
    need(NUM, 2, "숫자형 변수")
    method_lbl = st.radio("방법", ["Pearson (연속형, 선형관계)", "Spearman (순위·리커트, 비정규)"], horizontal=True)
    method = "pearson" if method_lbl.startswith("Pearson") else "spearman"
    default = NUM_DEF[:5]
    sel = st.multiselect("변수 선택 (2개 이상)", NUM, default=default)
    res = friendly(lambda: A.correlation(df, sel, method)) if len(sel) >= 2 else None
    if len(sel) < 2:
        st.info("변수를 2개 이상 고르세요.")
    if res:
        st.markdown("**상관계수 표** (* p < .05, ** p < .01, *** p < .001)")
        st.dataframe(res["star"])
        k = len(sel)
        long = []
        for i, a in enumerate(sel):
            for j, b in enumerate(sel):
                v = res["r"].iloc[i, j]
                long.append({"x": a, "y": b, "r": None if pd.isna(v) else float(v),
                             "label": "" if pd.isna(v) else f"{v:.2f}"})
        side = min(340, 70 * k + 40)
        st.markdown("**상관 히트맵**")
        st.vega_lite_chart(pd.DataFrame(long), {
            "width": side, "height": side,
            "encoding": {
                "x": {"field": "x", "type": "nominal", "sort": sel, "title": None},
                "y": {"field": "y", "type": "nominal", "sort": sel, "title": None},
            },
            "layer": [
                {"mark": "rect", "encoding": {
                    "color": {"field": "r", "type": "quantitative",
                              "scale": {"domain": [-1, 0, 1], "range": ["#E34948", "#F0EFEC", "#2A78D6"]}, "title": "r"},
                    "tooltip": [{"field": "x"}, {"field": "y"}, {"field": "r", "format": ".3f"}]}},
                {"mark": {"type": "text", "fontSize": 11}, "encoding": {"text": {"field": "label"}}},
            ],
        })
        with st.expander("상관계수·p값·n 자세히 보기"):
            show_table(res["pairs"])
        download_button(res["pairs"], "상관분석")
        interp(A.correlation_sentence(res))
        report_button("상관분석", [("table", f"상관계수 ({'Pearson' if method == 'pearson' else 'Spearman'})", res["star"], True),
                                ("table", "쌍별 상관계수", res["pairs"], False),
                                ("text", A.correlation_sentence(res))])

# ---------------------------------------------------------------------------
# 4. t검정
# ---------------------------------------------------------------------------
elif menu == M_T:
    st.subheader(M_T)
    need(NUM, 1, "숫자형 변수")
    kind = st.radio("종류", ["독립표본 (두 집단 비교)", "대응표본 (사전-사후)", "일표본 (기준값과 비교)"], horizontal=True)
    if kind.startswith("독립"):
        need(CAT, 1, "집단변수")
        y = st.selectbox("종속변수 Y (숫자형)", NUM, index=pick(NUM, ["사후점수", "score", "anova_score"]))
        g_opt = [c for c in CAT if c != y]
        two = [c for c in g_opt if df[c].dropna().nunique() == 2]
        g = st.selectbox("집단변수", g_opt, index=g_opt.index(two[0]) if two else 0)
        lv = sorted(df[g].dropna().astype(str).unique())
        chosen = lv
        if len(lv) > 2:
            chosen = st.multiselect("비교할 두 집단", lv, default=lv[:2], max_selections=2)
        if len(chosen) != 2:
            st.info("비교할 집단을 정확히 2개 고르세요.")
        else:
            res = friendly(lambda: A.t_test_independent(df, y, g, chosen))
            if res:
                row = res["table"].iloc[1 if res["use_welch"] else 0]
                metric_row([(f"t({row['df']:.1f})", f"{row['t']:.3f}"), ("p", fmt_p(row["p"])),
                            ("Cohen's d", f"{res['d']:.3f}"), ("Hedges' g", f"{res['g']:.3f}")])
                notice_dropped(res["n"], res["dropped"])
                show_table(res["desc"])
                st.bar_chart(res["desc"], x="집단", y="평균", color=ACCENT)
                show_table(res["table"])
                st.caption(f"Levene 등분산 검정: F = {res['levene_F']:.3f}, {A.p_text(res['levene_p'])} → "
                           + ("등분산 가정 기각, **Welch** 결과를 보세요." if res["use_welch"] else "등분산 가정 유지, **Student** 결과를 보세요."))
                download_button(res["table"], "독립표본t검정")
                sent = A.t_sentence("independent", res)
                interp(sent)
                report_button(f"독립표본 t검정 - {y} by {g}", [("table", "집단별 기술통계", res["desc"], False),
                                                             ("table", "t검정", res["table"], False), ("text", sent)])
    elif kind.startswith("대응"):
        need(NUM, 2, "숫자형 변수")
        b = st.selectbox("사전 (전)", NUM, index=pick(NUM, ["사전점수", "pre_score"]))
        a_opt = [c for c in NUM if c != b]
        a = st.selectbox("사후 (후)", a_opt, index=pick(a_opt, ["사후점수", "post_score"]))
        res = friendly(lambda: A.t_test_paired(df, b, a))
        if res:
            row = res["table"].iloc[0]
            metric_row([(f"t({int(row['df'])})", f"{row['t']:.3f}"), ("p", fmt_p(row["p"])),
                        ("평균 변화", f"{row['평균차']:.3f}"), ("Cohen's dz", f"{res['d']:.3f}")])
            notice_dropped(res["n"], res["dropped"])
            show_table(res["desc"])
            st.bar_chart(res["desc"], x="변수", y="평균", color=ACCENT)
            show_table(res["table"])
            st.caption(f"전·후 상관 r = {res['r']:.3f}")
            download_button(res["table"], "대응표본t검정")
            sent = A.t_sentence("paired", res)
            interp(sent)
            report_button(f"대응표본 t검정 - {b}→{a}", [("table", "기술통계", res["desc"], False),
                                                      ("table", "대응표본 t검정", res["table"], False), ("text", sent)])
    else:
        y = st.selectbox("변수", NUM, index=pick(NUM, ["score", "사후점수"]))
        s = pd.to_numeric(df[y], errors="coerce")
        mu = st.number_input("검정값 (비교할 기준 평균)", value=float(round(s.mean(), 0)) if s.notna().any() else 0.0)
        res = friendly(lambda: A.t_test_one_sample(df, y, mu))
        if res:
            row = res["table"].iloc[0]
            metric_row([(f"t({int(row['df'])})", f"{row['t']:.3f}"), ("p", fmt_p(row["p"]))])
            show_table(res["table"])
            sent = A.t_sentence("one", res)
            interp(sent)
            report_button(f"일표본 t검정 - {y}", [("table", "일표본 t검정", res["table"], False), ("text", sent)])

# ---------------------------------------------------------------------------
# 5. 교차분석
# ---------------------------------------------------------------------------
elif menu == M_CHI:
    st.subheader(M_CHI)
    need(CAT, 2, "범주형 변수(값 종류 2~20개)")
    r_var = st.selectbox("행 변수", CAT, index=pick(CAT, ["프로그램", "method"]))
    c_opt = [c for c in CAT if c != r_var]
    c_var = st.selectbox("열 변수", c_opt, index=pick(c_opt, ["재참여의사", "grade"]))
    res = friendly(lambda: A.chi_square(df, r_var, c_var))
    if res:
        metric_row([(f"χ²({res['df']})", f"{res['chi2']:.3f}"), ("p", fmt_p(res["p"])),
                    ("Cramér's V", f"{res['cramers_v']:.3f}"), ("N", f"{res['n']}")])
        if res["dropped"]:
            st.caption(f"결측이 있는 {res['dropped']}개 행은 제외했습니다.")
        st.markdown("**교차표 (빈도)**")
        show_table(res["table"], index=True)
        st.markdown("**행 백분율 (%)**")
        show_table(res["row_pct"], digits=1, index=True)
        st.bar_chart(res["table"], color=series_colors(res["table"].shape[1]))
        with st.expander("기대빈도·표준화 잔차 보기 (|잔차| > 1.96 인 칸이 차이를 만든 칸)"):
            show_table(res["expected"], digits=2, index=True)
            show_table(res["std_resid"], digits=2, index=True)
        if res["low_expected_pct"] > 20:
            st.warning(f"기대빈도가 5보다 작은 칸이 {res['low_expected_pct']:.0f}%입니다(20% 초과). 카이제곱 결과를 조심해서 해석하세요."
                       + (f" 2×2 표이므로 Fisher 정확검정 p = {fmt_p(res['fisher_p'])}를 참고하세요." if res["fisher_p"] is not None else ""))
        elif res["fisher_p"] is not None:
            st.caption(f"Fisher 정확검정 p = {fmt_p(res['fisher_p'])}")
        download_button(res["table"].reset_index(), "교차표")
        sent = A.chi_sentence(res)
        interp(sent)
        report_button(f"교차분석 - {r_var}×{c_var}", [("table", "교차표", res["table"], True),
                                                     ("table", "행 백분율(%)", res["row_pct"], True), ("text", sent)])

# ---------------------------------------------------------------------------
# 6. 신뢰도
# ---------------------------------------------------------------------------
elif menu == M_ALPHA:
    st.subheader(M_ALPHA)
    need(NUM, 2, "숫자형 문항")
    pref = [c for c in NUM if c.startswith(("만족", "문항", "Q", "q", "item"))]
    items = st.multiselect("한 척도를 이루는 문항들", NUM, default=pref or NUM_DEF[:3])
    rev = st.multiselect("역문항 (거꾸로 채점할 문항)", items, help="예: '수업이 지루했다'처럼 반대 방향으로 물은 문항")
    data_use = df
    if rev:
        vals = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in items]).dropna()
        c1, c2 = st.columns(2)
        lo = c1.number_input("척도 최솟값", value=float(vals.min()) if len(vals) else 1.0)
        hi = c2.number_input("척도 최댓값", value=float(vals.max()) if len(vals) else 5.0)
        data_use = A.reverse_items(df, rev, lo, hi)
        st.caption(f"역코딩: 새 값 = {lo:g} + {hi:g} − 원래 값")
    if len(items) < 2:
        st.info("문항을 2개 이상 고르세요.")
    else:
        res = friendly(lambda: A.cronbach_alpha(data_use, items))
        if res:
            metric_row([("Cronbach's α", f"{res['alpha']:.3f}"), ("표준화 α", f"{res['std_alpha']:.3f}"),
                        ("문항 수", f"{res['k']}"), ("평균 문항 간 상관", f"{res['mean_inter_r']:.3f}")])
            notice_dropped(res["n"], res["dropped"])
            show_table(res["items"])
            st.caption("기준(관례): α ≥ .9 매우 좋음 · .8 좋음 · .7 수용 가능 · .6 미만 낮음. "
                       "수정된 문항-총점 상관이 .3 미만이거나 음수인 문항은 검토 대상입니다.")
            if res["negative"]:
                st.warning(f"총점과 반대로 움직이는 문항: {', '.join(res['negative'])} → 역문항이면 위에서 '역문항'으로 지정하세요.")
            download_button(res["items"], "신뢰도분석")
            sent = A.alpha_sentence(res)
            interp(sent)
            apa_box(f"Cronbach's α = {A.apa_num(res['alpha'], 2, False)} ({res['k']} items, N = {res['n']})")
            report_button("신뢰도 분석", [("table", "문항 통계", res["items"], False), ("text", sent)])


# ---------------------------------------------------------------------------
# 7·8. 회귀
# ---------------------------------------------------------------------------
def show_regression(res, title):
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
    parts = [("table", "회귀계수", c, False)]
    if res.get("vif") is not None:
        st.markdown("**다중공선성 (VIF)**")
        show_table(res["vif"])
        parts.append(("table", "VIF", res["vif"], False))
        if (res["vif"]["VIF"] > 10).any():
            st.warning("VIF가 10을 넘는 변수가 있습니다. 독립변수끼리 너무 비슷해서 계수가 불안정할 수 있습니다.")
        else:
            st.caption("VIF가 모두 10 미만이면 다중공선성 문제가 크지 않다고 봅니다.")
    st.markdown("**잔차 그래프** (예측값 vs 잔차: 0 주변에 고르게 퍼져 있으면 좋음)")
    st.scatter_chart(pd.DataFrame({"예측값": res["fitted"], "잔차": res["resid"]}), x="예측값", y="잔차", color=ACCENT)
    sent = A.regression_sentence(res)
    interp(sent)
    apa_box(A.apa_regression(res))
    parts += [("text", sent), ("apa", A.apa_regression(res))]
    report_button(title, parts)


if menu == M_REG1:
    st.subheader("7. 단순회귀 (X 1개 → Y)")
    need(NUM, 2, "숫자형 변수")
    y = st.selectbox("종속변수 Y", NUM, index=pick(NUM, ["score", "사후점수"]))
    xs_opt = [c for c in NUM if c != y]
    x = st.selectbox("독립변수 X", xs_opt, index=pick(xs_opt, ["study_time", "주당학습시간"]))
    res = friendly(lambda: A.regression(df, y, [x]))
    if res:
        show_regression(res, f"단순회귀 - {y} ~ {x}")
        st.markdown("**산점도와 회귀선**")
        d = res["data"].sort_values(x)
        b0, b1 = res["coef"]["B"][0], res["coef"]["B"][1]
        plot = pd.DataFrame({x: d[x], "관측값": d[y], "회귀선(예측값)": b0 + b1 * d[x]})
        st.scatter_chart(plot, x=x, y=["관측값", "회귀선(예측값)"], color=SERIES[:2])

elif menu == M_REG2:
    st.subheader("8. 다중회귀 (X 여러 개 → Y)")
    need(NUM, 3, "숫자형 변수")
    y = st.selectbox("종속변수 Y", NUM, index=pick(NUM, ["score", "사후점수"]))
    xs_opt = [c for c in NUM if c != y]
    default = [c for c in ("study_time", "pre_score", "사전점수", "주당학습시간") if c in xs_opt] or xs_opt[:2]
    xs = st.multiselect("독립변수 X (2개 이상 권장)", xs_opt, default=default)
    if not xs:
        st.info("독립변수를 1개 이상 고르세요.")
    else:
        res = friendly(lambda: A.regression(df, y, xs))
        if res:
            show_regression(res, f"다중회귀 - {y} ~ {' + '.join(xs)}")
            st.caption("β(표준화)는 단위가 다른 변수들의 영향력을 비교할 때 사용합니다.")

# ---------------------------------------------------------------------------
# 9. 일원분산분석
# ---------------------------------------------------------------------------
elif menu == M_AOV1:
    st.subheader("9. 일원분산분석 (집단 간 평균 비교)")
    need(NUM, 1, "숫자형 변수")
    need(CAT, 1, "집단변수(값 종류 2~20개)")
    y = st.selectbox("종속변수 Y (숫자형)", NUM, index=pick(NUM, ["anova_score", "사후점수"]))
    g_opt = [c for c in CAT if c != y]
    if not g_opt:
        st.warning("집단변수로 쓸 열이 없습니다.")
        st.stop()
    g = st.selectbox("집단변수", g_opt, index=pick(g_opt, ["method", "전공계열"]))
    res = friendly(lambda: A.one_way_anova(df, y, g))
    if res:
        metric_row([(f"F({res['df1']}, {res['df2']})", f"{res['F']:.4f}"), ("p", fmt_p(res["p"])),
                    ("η² (효과크기)", f"{res['eta2']:.3f}"), ("ω²", f"{res['omega2']:.3f}")])
        notice_dropped(res["n"], res["dropped"])
        st.markdown("**집단별 기술통계**")
        show_table(res["desc"])
        st.bar_chart(res["desc"].assign(집단=res["desc"]["집단"].astype(str)), x="집단", y="평균", color=ACCENT)
        st.markdown("**분산분석표**")
        show_table(res["table"])
        download_button(res["table"], "일원분산분석표")
        st.markdown("**사후검정 (Tukey HSD)**")
        show_table(res["posthoc"])
        st.caption(f"등분산 검정(Levene): W={res['levene_W']:.3f}, {A.p_text(res['levene_p'])}"
                   + (" → 등분산 가정이 의심되므로 해석에 주의하세요." if res["levene_p"] < 0.05 else " → 등분산 가정을 크게 벗어나지 않습니다."))
        size = "큰" if res["eta2"] >= 0.14 else "중간" if res["eta2"] >= 0.06 else "작은"
        sig_pairs = res["posthoc"].loc[res["posthoc"]["p(Tukey)"] < 0.05, "비교"].tolist()
        sent = (f"'{g}' 집단에 따라 '{y}' 평균이 "
                f"{'통계적으로 유의하게 달랐다' if res['p'] < 0.05 else '유의하게 다르다고 보기 어렵다'}"
                f"(F({res['df1']}, {res['df2']})={res['F']:.2f}, {A.p_text(res['p'])}, η²={res['eta2']:.3f}, {size} 효과). "
                + (f"사후검정에서 차이가 유의한 쌍: {', '.join(sig_pairs)}." if sig_pairs else "사후검정에서 유의한 쌍은 없었다."))
        interp(sent)
        apa_box(A.apa_anova1(res))
        report_button(f"일원분산분석 - {y} by {g}", [("table", "집단별 기술통계", res["desc"], False),
                                                    ("table", "분산분석표", res["table"], False),
                                                    ("table", "Tukey HSD", res["posthoc"], False),
                                                    ("text", sent), ("apa", A.apa_anova1(res))])

# ---------------------------------------------------------------------------
# 10. 이원분산분석
# ---------------------------------------------------------------------------
elif menu == M_AOV2:
    st.subheader("10. 이원분산분석 (두 요인 + 상호작용)")
    need(NUM, 1, "숫자형 변수")
    need(CAT, 2, "집단변수(값 종류 2~20개)")
    y = st.selectbox("종속변수 Y (숫자형)", NUM, index=pick(NUM, ["anova_score", "사후점수"]))
    opts = [c for c in CAT if c != y]
    a = st.selectbox("요인 A", opts, index=pick(opts, ["method", "프로그램"]))
    b_opts = [c for c in opts if c != a]
    if not b_opts:
        st.warning("요인 B로 쓸 다른 집단변수가 없습니다.")
        st.stop()
    b = st.selectbox("요인 B", b_opts, index=pick(b_opts, ["grade", "성별"]))
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
        st.markdown("**상호작용 그래프** (선이 평행하지 않을수록 상호작용이 큼)")
        plot = res["cell_means"].copy()
        plot.index = plot.index.astype(str)
        plot.columns = [f"{b}={c}" for c in plot.columns]
        st.line_chart(plot, color=series_colors(plot.shape[1]))
        t = res["table"]
        lines = [f"{t['변동원'][i]}: F={t['F'][i]:.2f}, {A.p_text(t['p'][i])}, 부분η²={t['부분 η²'][i]:.3f}" for i in range(3)]
        interp(" / ".join(lines), "결과 요약")
        if res["interaction_p"] < 0.05:
            st.warning(f"상호작용이 유의합니다. '{a}'의 효과가 '{b}' 수준에 따라 다르므로, "
                       "각 요인의 주효과만 따로 해석하지 말고 상호작용 그래프와 칸 평균을 함께 보고 해석하세요.")
        apa_box(A.apa_anova2(res))
        report_button(f"이원분산분석 - {y} by {a}×{b}", [("table", "분산분석표(Type III)", res["table"], False),
                                                        ("table", "칸 평균", res["cell_means"], True),
                                                        ("text", " / ".join(lines)), ("apa", A.apa_anova2(res))])

# ---------------------------------------------------------------------------
# 11. 매개효과
# ---------------------------------------------------------------------------
elif menu == M_MED:
    st.subheader("11. 단순 매개효과 (X → M → Y)")
    need(NUM, 3, "숫자형 변수")
    x = st.selectbox("독립변수 X", NUM, index=pick(NUM, ["med_x", "주당학습시간"], 0))
    m = st.selectbox("매개변수 M", NUM, index=pick(NUM, ["med_m", "사전점수"], 1))
    y = st.selectbox("종속변수 Y", NUM, index=pick(NUM, ["med_y", "사후점수"], 2))
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
        sent = A.mediation_sentence(res)
        interp(sent)
        apa_box(A.apa_mediation(res))
        report_button(f"매개효과 - {x}→{m}→{y}", [("table", "경로계수", res["paths"], False),
                                                 ("text", sent), ("apa", A.apa_mediation(res))])

# ---------------------------------------------------------------------------
# 12. 조절효과
# ---------------------------------------------------------------------------
elif menu == M_MOD:
    st.subheader("12. 조절효과 (Y ~ X + W + X×W)")
    need(NUM, 3, "숫자형 변수")
    x = st.selectbox("독립변수 X", NUM, index=pick(NUM, ["mod_x", "주당학습시간"], 0))
    w = st.selectbox("조절변수 W", NUM, index=pick(NUM, ["mod_w", "스마트폰사용시간"], 1))
    y = st.selectbox("종속변수 Y", NUM, index=pick(NUM, ["mod_y", "사후점수"], 2))
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
        st.line_chart(plot, x=x, y=["W 낮음", "W 평균", "W 높음"], color=SERIES[:3])
        sent = A.moderation_sentence(res)
        interp(sent)
        apa_box(A.apa_moderation(res))
        report_button(f"조절효과 - {x}×{w}→{y}", [("table", "회귀계수", res["coef"], False),
                                                 ("table", "단순기울기", res["simple_slopes"], False),
                                                 ("text", sent), ("apa", A.apa_moderation(res))])

# ---------------------------------------------------------------------------
# 13. 기준값 검산
# ---------------------------------------------------------------------------
elif menu == M_CHECK:
    st.subheader("13. 기준값 검산 (교수자 기준결과와 비교)")
    missing = A.REFERENCE_COLUMNS - set(df.columns)
    if missing:
        st.warning("이 메뉴는 교수자 기준데이터(data/reference_data.xlsx) 전용입니다. "
                   "위에서 '예제 데이터 사용 → 기준데이터'를 고르세요. "
                   f"(없는 열: {', '.join(sorted(missing))})")
    else:
        with st.spinner("모든 분석을 다시 계산하는 중..."):
            chk = A.reference_check(df)
        ok = (chk["판정"] == "일치").sum()
        metric_row([("일치 항목", f"{ok} / {len(chk)}"), ("판정", "모두 일치" if ok == len(chk) else "확인 필요")])
        out = chk.copy()
        out["앱 결과"] = out["앱 결과"].round(6)
        out["차이"] = out["차이"].map(lambda v: f"{v:.2e}" if pd.notna(v) else "")
        st.dataframe(out, hide_index=True)
        download_button(chk, "검산결과")
        st.caption("소수점 반올림 차이(마지막 자리)는 허용합니다.")
        report_button("기준값 검산", [("table", "기준결과 vs 앱 결과", out, False)])

# ---------------------------------------------------------------------------
# 14. 보고서
# ---------------------------------------------------------------------------
elif menu == M_REPORT:
    st.subheader("14. 보고서 내려받기")
    rep = st.session_state["report"]
    if not rep:
        st.info("아직 담긴 결과가 없습니다. 각 분석 화면에서 **보고서에 담기**를 누르세요.")
    else:
        st.write(f"담긴 결과 **{len(rep)}개**")
        for i, sec in enumerate(rep, 1):
            st.markdown(f"{i}. {sec['title']}  <span style='color:#999;font-size:.8rem'>({sec['data']}, {sec['time']})</span>",
                        unsafe_allow_html=True)
        html_doc = build_report_html(rep)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        c1, c2 = st.columns(2)
        c1.download_button("HTML 보고서 내려받기", html_doc.encode("utf-8"), file_name=f"통계분석보고서_{stamp}.html",
                           mime="text/html", key="dl_report_html")
        c2.download_button("Word 파일(.doc) 내려받기", html_doc.encode("utf-8"), file_name=f"통계분석보고서_{stamp}.doc",
                           mime="application/msword", key="dl_report_doc")
        st.caption("HTML은 브라우저에서 열고 인쇄(Ctrl+P) → 'PDF로 저장'하면 PDF가 됩니다. .doc 파일은 Word에서 바로 열 수 있습니다.")
        if st.button("보고서 비우기"):
            st.session_state["report"] = []
            st.session_state["_last_added"] = None
            st.rerun()

st.markdown(
    '<div class="foot">결과는 변수 사이의 통계적 관계를 보여 줄 뿐 인과관계를 증명하지 않습니다.<br>'
    f'실제 연구에 쓰기 전에 기준데이터로 검산하세요.<br><span class="who">{CREDIT}</span></div>',
    unsafe_allow_html=True,
)
