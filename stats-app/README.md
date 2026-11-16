# 📊 초보자용 통계분석 앱

엑셀·CSV 파일을 올리면 **기초통계부터 t검정·교차분석·신뢰도·회귀·분산분석·매개·조절효과까지 14가지 분석**을 계산하고,
쉬운 한국어 해석과 **APA 보고 문장**, **내려받을 수 있는 보고서**까지 만들어 주는 웹앱입니다. PC와 스마트폰 브라우저에서 모두 쓸 수 있습니다.

> 금오공과대학교 대학원 빅데이터 과목 팀 과제 · **2026 금오공대 빅데이터 8조**
> 팀원: 김응범 외 팀원 명단은 제출 전에 확인해 기입합니다.
> 이번 수정본은 로컬 실행 기준입니다. 실제 배포 주소는 팀에서 확인 후 기입하세요.

---

## 이번 수정본에서 달라진 점

- 회귀 수치 안정성 및 완전 적합·무한값 안내 보완.
- 총점 분산 0인 신뢰도는 계산 불가로 안내하고 수준을 판정하지 않음.
- 정규성 검정은 전체 n과 실제 검정 n을 구분. 5,000개 초과 시 무작위 5,000개(시드 2026)로 검정.
- 조절분석의 원래 결측 제외 수를 유지하고 다중회귀 해석에 통제 조건을 명시.
- HTML 확장자 변경 대신 실제 DOCX 파일을 생성. 보고서에 결측 처리 방식 기록.
- 실행환경을 ZIP에서 제외. Windows는 `.venv-win`, macOS/Linux는 `.venv-unix`를 현지에서 생성.
- 자동 테스트 결과와 확인 범위는 `docs/VALIDATION.md` 참조. 실제 스마트폰 연결과 OS별 실기기 실행은 별도 확인이 필요함.

## ✨ 기능

| 메뉴 | 보여 주는 것 |
|---|---|
| 0. 데이터 확인 | 미리보기, 열별 자료형·결측·고유값 수, 집단변수 가능 여부 |
| 1. 기초통계 | n, 결측, 평균, 표준편차, 중앙값, 최소·최대, Q1·Q3·IQR, 왜도, 히스토그램, 빈도·비율 |
| 2. 정규성 검정 | Shapiro-Wilk W·p, 왜도·첨도, Q-Q 그림 |
| 3. 상관분석 | Pearson / Spearman, APA 형식 상관표(별표), 상관 히트맵, 쌍별 r·p·n |
| 4. t검정 | 독립표본(Student·Welch 자동 선택, Levene), 대응표본(사전-사후), 일표본, Cohen's d·Hedges' g, 95% CI |
| 5. 교차분석 | 교차표, 행 백분율, χ², Cramér's V, 기대빈도 5 미만 경고, Fisher 정확검정(2×2), 표준화 잔차 |
| 6. 신뢰도 | Cronbach's α, 표준화 α, 수정된 문항-총점 상관, 문항 삭제 시 α, 역문항 감지·역코딩 |
| 7. 단순회귀 | 회귀식, R², 수정 R², F, B·SE·β·t·p·95% CI, 산점도+회귀선, 잔차 그래프 |
| 8. 다중회귀 | 위 항목 + VIF(다중공선성) 경고 |
| 9. 일원분산분석 | 집단별 기술통계, 분산분석표, η²·ω², Levene 등분산 검정, Tukey HSD 사후검정 |
| 10. 이원분산분석 | Type III 분산분석표, 부분 η², 칸 평균, 상호작용 그래프, 상호작용 유의 시 해석 주의 |
| 11. 매개효과 | a, b, c, c', 간접효과 ab, Sobel 검정, 부트스트랩 95% CI, 경로 그림 |
| 12. 조절효과 | X×W 상호작용, ΔR², 평균중심화, 단순기울기(W 평균±1SD)와 그래프 |
| 13. 기준값 검산 | 교수자 기준결과 27개 항목과 앱 계산값 자동 비교 |
| 14. 보고서 내려받기 | 📌 버튼으로 담은 결과를 **HTML / Word(.docx)** 보고서 한 파일로 저장 (인쇄 → PDF 가능) |

**공통 기능**
- 📝 **APA 형식**: 결과마다 논문에 바로 붙일 APA 보고 문장 제공, 사이드바에서 표를 APA 형식(소수 둘째 자리, p = .027)으로 전환
- 🧩 **결측값 처리 선택**: 분석할 때 제외(listwise) / 숫자형 평균 대체
- 쉬운 한국어 해석 문장 · 오류 안내 · 결과표 CSV 저장 · 스마트폰용 세로 표 보기
- CSV 한글 인코딩(UTF-8/CP949) 자동 인식 · 예제 데이터 3종 내장

---

## 🚀 실행 방법

### 방법 1. 내 PC에서 (가장 쉬움)
1. 전달받은 ZIP을 **새 폴더**에 풉니다. `kumho26` 폴더 안에 `app.py`가 바로 보입니다. GitHub에서는 Code → Download ZIP을 사용할 수 있습니다.
2. **Windows**: `run_windows.bat` 더블클릭
   **macOS**: `start_mac.command` 더블클릭 (처음 한 번 "확인되지 않은 개발자" 창이 뜨면 우클릭 → 열기 → 열기)
   **Linux**: 터미널에서 `bash run_mac_linux.sh`
3. 실행 안내가 나오면 브라우저에서 `http://localhost:8501`을 직접 엽니다. 실행 터미널은 켜 둡니다.
4. 앱에서 **예제 데이터 사용 → 기준데이터**를 고르면 파일 없이 바로 시험할 수 있습니다.

> Python 3.12 권장 (Windows 설치 시 **Add python.exe to PATH** 체크)

<details>
<summary>명령어로 직접 실행하기</summary>

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```
</details>

### 방법 2. 스마트폰 — 같은 Wi-Fi
```bash
streamlit run app.py --server.address 0.0.0.0
```
PC IP 확인(Windows: `ipconfig` → IPv4 주소) 후 스마트폰 브라우저에서 `http://PC-IP:8501` 접속.
학교 Wi-Fi에서 안 되면 PC를 휴대폰 핫스팟에 연결해 보세요.

### 방법 3. 무료 서버에 배포 — Streamlit Community Cloud (어디서나 접속)
1. 이 저장소를 GitHub에 올립니다 (**Public** 권장).
2. [share.streamlit.io](https://share.streamlit.io) 에 GitHub 계정으로 로그인 → **Create app**
3. Repository: 이 저장소 / Branch: `main` / Main file path: `app.py` → **Deploy**
4. 발급된 `https://○○○.streamlit.app` 주소를 이 README 맨 위에 적고, 스마트폰에서 열어 확인합니다.

> ⚠️ Vercel·Netlify 같은 서비스는 Streamlit 앱 실행에 맞지 않습니다. Streamlit Community Cloud를 쓰세요.

---

## ✅ 검산

교수자 기준데이터(`data/reference_data.xlsx`)로 계산한 결과가 기준결과와 **27/27 항목 일치**합니다.
추가 분석(정규성·상관·t검정·교차분석·신뢰도)은 scipy·pandas의 독립 계산과 비교해 검증했습니다.

```bash
python -m pytest -q tests
```
- `tests/test_analysis.py` — 주차별 기준값 검산 + 잘못된 입력 처리
- `tests/test_extra.py` — 추가 분석을 scipy·pandas 계산과 교차검증 + APA 표기·결측 대체
- `tests/test_fixes.py` — 큰 수치·작은 수치, 완전 적합·무한값·신뢰도 불능·정규성 표본 수·조절 결측 수·실제 DOCX 검증
- `tests/test_app.py` — 15개 메뉴 × 예제 데이터 3종이 오류 없이 열리는지, 보고서 담기·내려받기 (Streamlit AppTest)

이 ZIP의 `kumho26` 폴더 **안의 내용 전체**를 저장소 루트로 올리면 포함된 workflow를 사용할 수 있습니다. 실제 GitHub Actions 실행은 팀에서 확인하세요.

<details>
<summary>기준값 비교표 보기</summary>

| 분석 | 기준값 | 앱 결과 |
|---|---|---|
| 기초통계 score | n=36, 평균 76.000, SD 8.135 | 동일 |
| 단순회귀 score~study_time | R²=0.0330, B=1.1089, p=0.288707 | 동일 |
| 다중회귀 score~study_time+pre_score | R²=0.9349, 수정R²=0.9310 | 동일 |
| 일원분산분석 anova_score~method | F=14.0291, p=0.000039 | 동일 |
| 이원분산분석 method×grade | F=266.3419 / 283.2311 / 8.2607 | 동일 |
| 매개 med_x→med_m→med_y | a=0.8027, b=1.5300, c'=0.1383, ab=1.2282 | 동일 |
| 조절 mod_x×mod_w | B=0.6786, R²=0.9743 | 동일 |

전체 표: [`docs/MASTER_PROMPT.md`](docs/MASTER_PROMPT.md) 4장
</details>

---

## 📁 폴더 구성

```
├─ app.py                     화면·업로드·메뉴 (Streamlit)
├─ analysis.py                통계 계산 (numpy·pandas·scipy)
├─ report_export.py           실제 DOCX 생성
├─ requirements.txt           필요한 패키지
├─ run_windows.bat            Windows 더블클릭 실행
├─ start_mac.command          macOS 더블클릭 실행
├─ run_mac_linux.sh           macOS/Linux 터미널 실행
├─ .streamlit/config.toml     업로드 용량·테마 설정
├─ data/
│  ├─ reference_data.xlsx     교수자 제공 검산용 익명 데이터 (36행)
│  ├─ survey_sample.xlsx      가상 설문 예제 (120명, 리커트 5문항·역문항 포함)
│  └─ sample.xlsx             개인정보 없는 연습 데이터 (12행)
├─ tests/
│  ├─ test_analysis.py        기준값 검산 테스트
│  ├─ test_extra.py           추가 분석 검증 테스트
│  └─ test_app.py             앱 화면 테스트
├─ docs/
│  └─ MASTER_PROMPT.md        개발에 사용한 마스터·코딩 프롬프트
└─ .github/workflows/tests.yml  GitHub 자동 테스트
```

---

## 🧰 사용 기술

Python 3.12 · Streamlit · pandas · numpy · scipy · openpyxl · xlrd · pytest · python-docx
(이번 검증: Python 3.12, pandas 2.2.3, numpy 2.3.5, scipy 1.17.0, Streamlit 1.67.0. 직접 의존성은 requirements.txt에 고정)

- 회귀는 설명변수를 중심화·척도조정한 뒤 SVD로 계산하고 계수·공분산을 원래 단위로 복원합니다. 분산분석은 기존 최소제곱법 구현을 유지합니다.
- Tukey HSD: `scipy.stats.tukey_hsd`, 등분산: `scipy.stats.levene`, 정규성: `scipy.stats.shapiro`
- 상관 히트맵은 Streamlit 내장 Vega-Lite 차트 사용(추가 설치 없음)
- 매개효과 부트스트랩은 난수를 고정해 다시 실행해도 같은 결과
- 화면: Pretendard 글꼴, 잉크 네이비 머리 영역(정규분포 곡선과 95% 구간), 스마트폰 대응 레이아웃
- 차트 색은 기존 파랑·주황·청록 계열을 유지했습니다. 이번 수정에서 색각이상 접근성 검증을 새로 수행하지는 않았습니다.

## ⚠️ 제한점

- 결측은 분석별 제외 또는 평균 대체만 지원. 상관분석은 쌍별 제외(pairwise)를 사용하므로 각 쌍의 n을 확인하세요. 평균 대체는 분산·상관·표준오차를 왜곡할 수 있습니다.
- 보고서에는 표·해석·APA 문장이 담기며 그래프는 포함되지 않음. DOCX 구조와 내용은 자동 검사했으며 Word 실프로그램의 시각 검수는 별도로 필요함
- 회귀의 X는 숫자형만 지원(범주형 더미 변환 없음)
- 이원분산분석은 모든 요인 조합에 사례가 2개 이상 필요
- 매개·조절은 단순 모형(X 1개, M 또는 W 1개), 공변량 통제 없음
- 결과는 통계적 관계를 보여 줄 뿐 **인과관계를 증명하지 않습니다**

## 🔒 개인정보

실제 이름·학번·연락처·성적이 담긴 파일은 저장소에 올리지 마세요. `data/` 의 예제 파일은 익명 가상 데이터입니다.

## 🛠 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| `python`을 찾을 수 없음 | Python 재설치 시 "Add to PATH" 체크 |
| `ModuleNotFoundError` | `pip install -r requirements.txt` 다시 실행 |
| `.xls` 파일이 안 열림 | 엑셀에서 `.xlsx`로 다시 저장 |
| CSV 한글 깨짐 | 엑셀에서 "CSV UTF-8"로 저장 |
| 스마트폰 접속 안 됨 | 같은 Wi-Fi/핫스팟 확인, 방화벽 허용, 또는 방법 3 사용 |
| Streamlit Cloud 배포 실패 | Main file path가 `app.py`인지, `requirements.txt`가 저장소 맨 위에 있는지 확인 |

---

<sub>by 2026 금오공대 빅데이터 8조</sub>
